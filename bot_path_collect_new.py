'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_path_collect: Collects troops along a path, and attacks outward using path.
'''

import logging
from Queue import Queue
import random
import threading
import time

import client2.generals as generals
from viewer import GeneralsViewer

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
		self._game = generals.Generals('PurdueBot-Path', 'PurdueBot-Path', 'private', gameid='HyI4d3_rl') # Private Game - http://generals.io/games/HyI4d3_rl
		#self._game = generals.Generals('PurdueBot', 'PurdueBot', '1v1') # 1v1
		#self._game = generals.Generals('PurdueBot', 'PurdueBot', 'ffa') # FFA

		# Start Game Update Loop
		self._running = True
		_create_thread(self._start_update_loop)

		while (self._running):
			msg = input('Send Msg:')
			print("Sending MSG: " + msg)
			# TODO: Send msg

	######################### Handle Updates From Server #########################

	def _start_update_loop(self):
		received_first_update = False

		for update in self._game.get_updates():
			self._set_update(update)

			if (not received_first_update):
				self._received_first_update()
				received_first_update = True

			if (not self._running):
				return

			self._make_move()
			#self._print_scores()

			# Update GeneralsViewer Grid
			if '_viewer' in dir(self):
				if '_path' in dir(self):
					self._update.path = self._path
				self._viewer.updateGrid(self._update)

	def _received_first_update(self):
		self._clear_target()
		self._path = []
		self._path_position = -1
		return

	def _set_update(self, update):
		if (update.complete):
			print("!!!! Game Complete. Result = " + str(update.result) + " !!!!")
			self._running = False
			return

		self._update = update
		self._pi = update.player_index
		self._rows = update.rows
		self._cols = update.cols

	def _print_scores(self):
		'''
		scores = sorted(self._update.scores, key=lambda general: general['total'], reverse=True) # Sort Scores
		lands = sorted(self._update['lands'], reverse=True)
		armies = sorted(self._update['armies'], reverse=True)

		print(" -------- Scores --------")
		for score in scores:
			pos_lands = lands.index(score['tiles'])
			pos_armies = armies.index(score['total'])

			if (score['i'] == self._pi):
				print("SELF: ")
			print('Land: %d (%4d), Army: %d (%4d) / %d' % (pos_lands+1, score['tiles'], pos_armies+1, score['total'], len(scores)))
		'''
		print("Update To New API")

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
		self._move_primary_path_forward()

	######################### Primary Target Finding #########################

	def _update_primary_target(self):
		if self._find_primary_target():
			old_x, old_y = (-1, -1)
			if (self._path_position >= 0): # Store old path position
				old_x, old_y = self._path_coordinates(self._path_position)
			self._path = self._find_path() # Find new path to target
			self._restart_primary_path(old_x, old_y) # Check if old path position part of new path

	def _find_primary_target(self):
		newTarget = False

		if (self._target_position != None and self._update._tile_grid[self._target_position[0]][self._target_position[1]] == self._pi): # Acquired Target
			self._clear_target()

		king_y, king_x = self._update._visible_generals[self._pi]
		max_target_size = self._update._army_grid[king_y][king_x] * 1.5

		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_pos = (y,x)
				source_tile = self._update._tile_grid[y][x]
				source_army = self._update._army_grid[y][x]

				if (self._target_type <= OPP_GENERAL): # Search for Generals
					if (source_tile >= 0 and source_tile != self._pi and source_pos in self._update._visible_generals):
						self._target_position = source_pos
						self._target_type = OPP_GENERAL
						self._target_army = source_army
						return True

				if (self._target_type <= OPP_CITY): # Search for Smallest Cities
					if (source_tile != self._pi and source_army < max_target_size and source_pos in self._update._visible_cities):
						if (self._target_type < OPP_CITY or self._target_army > source_army):
							self._target_position = source_pos
							self._target_type = OPP_CITY
							self._target_army = source_army
							newTarget = True

				if (self._target_type <= OPP_ARMY): # Search for Largest Opponent Armies
					if (source_tile >= 0 and source_tile != self._pi and source_army > self._target_army and source_pos not in self._update._visible_cities):
						self._target_position = source_pos
						self._target_type = OPP_ARMY
						self._target_army = source_army
						newTarget = True

				if (self._target_type < OPP_EMPTY): # Search for Empty Squares
					if (source_tile == generals.EMPTY and source_army < max_target_size):
						self._target_position = source_pos
						self._target_type = OPP_EMPTY
						self._target_army = source_army
						return True

		return newTarget

	def _clear_target(self):
		self._target_position = None
		self._target_army = 0
		self._target_type = OPP_EMPTY - 1

	######################### Pathfinding #########################

	def _find_path(self, x1=-1, y1=-1, x2=-1, y2=-1):
		# Verify Source and Dest
		if (x1 == -1 or not self._validPosition(x1,y1)): # No Source, Use King
			y1, x1 = self._update._visible_generals[self._pi]
		if (x2 == -1 or not self._validPosition(x2,y2)): # No Dest, Use Primary Target
			y2, x2 = self._target_position

		source = (x1, y1, self._update._army_grid[y1][x1]-1)
		dest = (x2,y2)

		# Determine Path To Destination
		frontier = Queue()
		frontier.put(source)
		came_from = {}
		came_from[source[:2]] = None

		while not frontier.empty():
			current = frontier.get()
			current_pos = current[:2]

			if current_pos == dest: # Found Destination
				break

			for next in self._neighbors(current[0], current[1], current[2]):
				next_pos = next[:2]
				if next_pos not in came_from:
					frontier.put(next)
					came_from[next_pos] = current_pos # Remove Max Target Amount

		# Create Path List
		source = source[:2]
		current = dest
		path = [current]
		try:
			while current != source:
				current = came_from[current]
				path.append(current)
			path.append(source)
		except KeyError:
			None
		path.reverse()

		return path

	def _neighbors(self, x, y, max_target_size=0):
		neighbors = []

		for dy, dx in DIRECTIONS:
			if (self._validPosition(x+dx, y+dy)):
				current_tile = self._update._tile_grid[y][x]
				current_army = self._update._army_grid[y][x]

				max_target_size_current = max_target_size
				if (current_tile == self._pi):
					max_target_size_current += (current_army - 1)

				if (current_tile == self._pi or max_target_size == 0 or current_army < max_target_size):
					neighbors.append((x+dx, y+dy, max_target_size_current))

		return neighbors

	######################### Move Forward Along Path #########################

	def _move_primary_path_forward(self):
		try:
			x,y = self._path_coordinates(self._path_position)
		except (AttributeError, TypeError):
			#logging.debug("Invalid Current Path Position")
			return self._restart_primary_path()

		source_tile = self._update._tile_grid[y][x]
		source_army = self._update._army_grid[y][x]

		if (source_tile != self._pi or source_army < 2): # Out of Army, Restart Path
			#logging.debug("Path Error: Out of Army (%d,%d)" % (source_tile, source_army))
			return self._restart_primary_path()

		#try:
		x2,y2 = self._path_coordinates(self._path_position+1) # Determine Destination
		dest_tile = self._update._tile_grid[y2][x2]
		dest_army = self._update._army_grid[y2][x2] + 1
		if (dest_tile == self._pi or source_army > dest_army):
			self._place_move(y, x, y2, x2)
		else:
			#logging.debug("Path Error: Out of Army To Attack (%d,%d,%d,%d)" % (x,y,source_army,dest_army))
			return self._restart_primary_path()
		'''except TypeError:
			#logging.debug("Path Error: Invalid Target Destination")
			return self._restart_primary_path()'''

		self._path_position = self._path_position + 1
		return True

	def _path_coordinates(self, i):
		try:
			return self._path[i]
		except IndexError:
			return None

	def _restart_primary_path(self, old_x=-1, old_y=-1): # Always returns False
		self._path_position = 0
		if (old_x >= 0):
			for i, pos in enumerate(self._path):
				if pos == (old_x, old_y):
					self._path_position = i
		
		return False

	######################### Move Outward #########################

	def _move_outward(self):
		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_tile = self._update._tile_grid[y][x]
				source_army = self._update._army_grid[y][x]
				if (source_tile == self._pi and source_army >= 2 and (x,y) not in self._path): # Find One With Armies
					for dy, dx in self._toward_dest_moves(x,y):
						if (self._validPosition(x+dx,y+dy)):
							dest_tile = self._update._tile_grid[y+dy][x+dx]
							dest_army = self._update._army_grid[y+dy][x+dx] + 1
							if ((dest_tile != self._pi and source_army > dest_army) or (x+dx,y+dy) in self._path): # Capture Somewhere New
								self._place_move(y, x, y+dy, x+dx)
								return True
		return False

	######################### Collect To Path #########################

	def _move_collect_to_path(self):
		return True
	

	######################### Movement Helpers #########################


	def _toward_dest_moves(self, source_x, source_y, dest_x=-1, dest_y=-1):
		# Determine Destination
		if (dest_x == -1):
			dest_y, dest_x = self._target_position

		# Compute X/y Directions
		dir_y = 1
		if source_y > dest_y:
			dir_y = -1

		dir_x = 1
		if source_x > dest_x:
			dir_x = -1

		# Return List of Moves
		moves = random.sample([(0, dir_x), (dir_y, 0)],2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)],2))
		return moves

	def _away_king_moves(self, x, y):
		king_y, king_x = self._update._visible_generals[self._pi]

		if (y == king_y and x == king_x): # Moving from king
			return self._moves_random()

		dir_y = 1
		if y < king_y:
			dir_y = -1

		dir_x = 1
		if x < king_x:
			dir_x = -1

		moves = random.sample([(0, dir_x), (dir_y, 0)],2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)],2))
		return moves

	def _moves_random(self):
		return random.sample(DIRECTIONS, 4)

	def _place_move(self, y1, x1, y2, x2, move_half=False):
		if (self._validPosition(x2, y2)):
			self._game.move(y1, x1, y2, x2, move_half)
			return True
		return False

	def _validPosition(self, x, y):
		return 0 <= y < self._rows and 0 <= x < self._cols and self._update._tile_grid[y][x] != generals.MOUNTAIN and self._update._tile_grid[y][x] != generals.OBSTACLE

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