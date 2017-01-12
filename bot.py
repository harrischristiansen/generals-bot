'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Base Bot Class
'''

import logging
from Queue import Queue
import random
import threading

import client2.generals as generals
from viewer import GeneralsViewer

BOT_NAME = 'PurdueBot-Path'

# Opponent Type Definitions
OPP_EMPTY = 0
OPP_ARMY = 1
OPP_CITY = 2
OPP_GENERAL = 3

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

# Show all logging
logging.basicConfig(level=logging.DEBUG)

class GeneralsBot(object):
	def __init__(self):
		# Start Game Loop
		_create_thread(self._start_game_loop)

		# Start Game Viewer
		self._viewer = GeneralsViewer()
		self._viewer.mainViewerLoop()

	def _start_game_loop(self):
		# Create Game
		self._game = generals.Generals(BOT_NAME, BOT_NAME, 'private', gameid='HyI4d3_rl') # Private Game - http://generals.io/games/HyI4d3_rl
		#self._game = generals.Generals(BOT_NAME, BOT_NAME, '1v1') # 1v1
		#self._game = generals.Generals(BOT_NAME, BOT_NAME, 'ffa') # FFA

		# Start Game Update Loop
		self._running = True
		self._pre_game_start()
		_create_thread(self._start_update_loop)

		while (self._running):
			msg = input('Send Msg:')
			print("Sending MSG: " + msg)
			# TODO: Send msg

	def _pre_game_start(self):
		self._clear_target()
		self._path = []
		self._restart_primary_path()
		return

	######################### Handle Updates From Server #########################

	def _start_update_loop(self):
		for update in self._game.get_updates():
			self._set_update(update)

			if (not self._running):
				return

			self._make_move()
			#self._print_scores()

			# Update GeneralsViewer Grid
			if '_viewer' in dir(self):
				if '_path' in dir(self):
					self._update.path = self._path
				self._viewer.updateGrid(self._update)

	def _set_update(self, update):
		if (update.complete):
			print("!!!! Game Complete. Result = " + str(update.result) + " !!!!")
			self._running = False
			return

		self._update = update

	def _print_scores(self):
		scores = sorted(self._update.scores, key=lambda general: general['total'], reverse=True) # Sort Scores
		lands = sorted([s['tiles'] for s in self._update.scores], reverse=True)
		armies = sorted([s['total'] for s in self._update.scores], reverse=True)

		print(" -------- Scores --------")
		for score in scores:
			pos_lands = lands.index(score['tiles'])
			pos_armies = armies.index(score['total'])

			if (score['i'] == self._update.player_index):
				print("SELF: ")
			print('Land: %d (%4d), Army: %d (%4d) / %d' % (pos_lands+1, score['tiles'], pos_armies+1, score['total'], len(scores)))

	######################### Move Generation #########################

	def _make_move(self):
		if (self._update.turn % 2 == 0):
			self._make_primary_move()
		else:
			if not self._move_outward():
				self._make_primary_move()
		return

	def _make_primary_move(self):
		self._update_primary_target()
		if (len(self._path) > 0):
			self._move_primary_path_forward()

	######################### Primary Target Finding #########################

	def _update_primary_target(self):
		if self._find_primary_target():
			oldPosition = None
			if (self._path_position > 0 and len(self._path) > 0): # Store old path position
				oldPosition = self._path[self._path_position]
			self._path = self._find_path() # Find new path to target
			self._restart_primary_path(oldPosition) # Check if old path position part of new path
			print("New Path: " + str(self._path))

	def _find_primary_target(self):
		newTarget = False

		if (self._target != None and self._target.tile == self._update.player_index): # Acquired Target
			self._clear_target()

		general_tile = self._update.generals[self._update.player_index]
		max_target_size = self._update.grid[general_tile.y][general_tile.x].army * 1.5

		for x in _shuffle(range(self._update.cols)): # Check Each Square
			for y in _shuffle(range(self._update.rows)):
				source = self._update.grid[y][x]

				if (self._target_type <= OPP_GENERAL): # Search for Generals
					if (source.tile >= 0 and source.tile != self._update.player_index and source in self._update.generals):
						self._target = source
						self._target_type = OPP_GENERAL
						return True

				if (self._target_type <= OPP_CITY): # Search for Smallest Cities
					if (source.tile != self._update.player_index and source.army < max_target_size and source in self._update.cities):
						if (self._target_type < OPP_CITY or self._target.army > source.army):
							self._target = source
							self._target_type = OPP_CITY
							newTarget = True

				if (self._target_type <= OPP_ARMY): # Search for Largest Opponent Armies
					if (source.tile >= 0 and source.tile != self._update.player_index and source.army > self._target.army and source not in self._update.cities):
						self._target = source
						self._target_type = OPP_ARMY
						newTarget = True

				if (self._target_type < OPP_EMPTY): # Search for Empty Squares
					if (source.tile == generals.map.TILE_EMPTY and source.army < max_target_size):
						self._target = source
						self._target_type = OPP_EMPTY
						return True

		return newTarget

	def _clear_target(self):
		self._target = None
		self._target_type = OPP_EMPTY - 1

	######################### Pathfinding #########################

	def _find_path(self, source=None, dest=None):
		# Verify Source and Dest
		if (source == None): # No Source, Use General
			source = self._update.generals[self._update.player_index]
		if (dest == None): # No Dest, Use Primary Target
			dest = self._target

		# Determine Path To Destination
		frontier = Queue()
		frontier.put(source)
		came_from = {}
		came_from[source] = None
		self.max_target_size = [[0 for x in range(self._update.cols)] for y in range(self._update.rows)]
		self.max_target_size[source.y][source.x] = source.army - 1

		while not frontier.empty():
			current = frontier.get()

			if current == dest: # Found Destination
				break

			for next in self._neighbors(current, self.max_target_size[current.y][current.x]):
				if next not in came_from:
					frontier.put(next)
					came_from[next] = current # Remove Max Target Amount

		# Create Path List
		current = dest
		path = [current]
		try:
			while current != source:
				current = came_from[current]
				path.append(current)
		except KeyError:
			None
		path.reverse()

		return path

	def _neighbors(self, source, max_target_size=0):
		x = source.x
		y = source.y

		neighbors = []
		for dy, dx in DIRECTIONS:
			if (self._validPosition(x+dx, y+dy)):
				current = self._update.grid[y+dy][x+dx]

				max_target_size_current = max_target_size
				if (current.tile == self._update.player_index):
					max_target_size_current += (current.army - 1)
				elif (current.army > 0):
					max_target_size_current -= (current.army + 1)

				if (current.tile == self._update.player_index or max_target_size == 0 or current.army < max_target_size):
					if (self.max_target_size[y+dy][x+dx] == 0):
						self.max_target_size[y+dy][x+dx] = max_target_size_current
					neighbors.append(current)

		return neighbors

	######################### Move Forward Along Path #########################

	def _move_primary_path_forward(self):
		try:
			source = self._path_coordinates(self._path_position)
		except IndexError:
			logging.debug("Invalid Current Path Position")
			return self._restart_primary_path()

		if (source.tile != self._update.player_index or source.army < 2): # Out of Army, Restart Path
			#logging.debug("Path Error: Out of Army (%d,%d)" % (source.tile, source.army))
			return self._restart_primary_path()

		try:
			dest = self._path_coordinates(self._path_position+1) # Determine Destination
			if (dest.tile == self._update.player_index or source.army > (dest.army+1)):
				self._place_move(source, dest)
			else:
				#logging.debug("Path Error: Out of Army To Attack (%d,%d,%d,%d)" % (dest.x,dest.y,source.army,dest.army))
				return self._restart_primary_path()
		except IndexError:
			#logging.debug("Path Error: Invalid Target Destination")
			return self._restart_primary_path()

		self._path_position += 1
		return True

	def _path_coordinates(self, i):
		return self._path[i]

	def _restart_primary_path(self, old_tile=None):
		self._path_position = 0
		if (old_tile != None):
			for i, tile in enumerate(self._path):
				if (tile.x, tile.y) == (old_tile.x, old_tile.y):
					self._path_position = i
					return True
		
		return False

	######################### Move Outward #########################

	def _move_outward(self):
		for x in _shuffle(range(self._update.cols)): # Check Each Square
			for y in _shuffle(range(self._update.rows)):
				source = self._update.grid[y][x]

				if (source.tile == self._update.player_index and source.army >= 2 and source not in self._path): # Find One With Armies
					for dy, dx in self._toward_dest_moves(source):
						if (self._validPosition(x+dx,y+dy)):
							dest = self._update.grid[y+dy][x+dx]
							if ((dest.tile != self._update.player_index and source.army > (dest.army+1)) or dest in self._path): # Capture Somewhere New
								self._place_move(source, dest)
								return True
		return False

	######################### Collect To Path #########################

	def _move_collect_to_path(self):
		return True
	

	######################### Movement Helpers #########################


	def _toward_dest_moves(self, source, dest=None):
		# Determine Destination
		if (dest == None):
			dest = self._target

		# Compute X/y Directions
		dir_y = 1
		if source.y > dest.y:
			dir_y = -1

		dir_x = 1
		if source.x > dest.x:
			dir_x = -1

		# Return List of Moves
		moves = random.sample([(0, dir_x), (dir_y, 0)],2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)],2))
		return moves

	def _away_king_moves(self, source):
		general = self._update.generals[self._update.player_index]

		if (source.y == general.y and source.x == general.x): # Moving from General
			return self._moves_random()

		dir_y = 1
		if source.y < general.y:
			dir_y = -1

		dir_x = 1
		if source.x < general.x:
			dir_x = -1

		moves = random.sample([(0, dir_x), (dir_y, 0)],2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)],2))
		return moves

	def _moves_random(self):
		return random.sample(DIRECTIONS, 4)

	def _place_move(self, source, dest, move_half=False):
		if (self._validPosition(dest.x, dest.y)):
			self._game.move(source.y, source.x, dest.y, dest.x, move_half)
			return True
		return False

	def _validPosition(self, x, y):
		return 0 <= y < self._update.rows and 0 <= x < self._update.cols and self._update._tile_grid[y][x] != generals.map.TILE_MOUNTAIN and self._update._tile_grid[y][x] != generals.map.TILE_OBSTACLE

######################### Global Helpers #########################

def _create_thread(f):
	t = threading.Thread(target=f)
	t.daemon = True
	t.start()

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)

######################### Main #########################

# Start Bot
GeneralsBot()