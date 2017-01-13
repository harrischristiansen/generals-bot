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

import client.generals as generals
from viewer import GeneralsViewer

# Opponent Type Definitions
OPP_EMPTY = 0
OPP_ARMY = 1
OPP_CITY = 2
OPP_GENERAL = 3

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

class GeneralsBot(object):
	def __init__(self, updateMethod, name="PurdueBot", gameType="private"):
		# Save Config
		self._updateMethod = updateMethod
		self._name = name
		self._gameType = gameType

		# Start Game Loop
		_create_thread(self._start_game_loop)

		# Start Game Viewer
		self._viewer = GeneralsViewer()
		self._viewer.mainViewerLoop()

	def _start_game_loop(self):
		# Create Game
		if (self._gameType == "ffa"): # FFA
			self._game = generals.Generals(self._name, self._name, 'ffa')
		elif (self._gameType == "1v1"): # 1v1
			self._game = generals.Generals(self._name, self._name, '1v1')
		else: # private
			self._game = generals.Generals(self._name, self._name, 'private', gameid='HyI4d3_rl') # Private Game - http://generals.io/games/HyI4d3_rl

		# Start Game Update Loop
		self._running = True
		_create_thread(self._start_update_loop)

		while (self._running):
			msg = input('Send Msg:')
			print("Sending MSG: " + msg)
			# TODO: Send msg

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
		self._updateMethod(self, self._update)

	######################### Tile Finding #########################

	def find_largest_tile(self, notInPath=None):
		largest = None
		for x in range(self._update.cols): # Check Each Square
			for y in range(self._update.rows):
				tile = self._update.grid[y][x]
				if (tile.tile == self._update.player_index and (largest == None or largest.army < tile.army) and (notInPath == None or tile not in notInPath)):
					largest = tile

		return largest

	def find_closest_in_path(self, tile, path):
		closest = None
		closest_distance = 9999
		for x in range(self._update.cols): # Check Each Square
			for y in range(self._update.rows):
				dest = self._update.grid[y][x]
				if (dest in path):
					distance = self._distance(tile, dest)
					if (distance < closest_distance):
						closest = dest
						closest_distance = distance

		return closest


	def find_primary_target(self, target=None):
		target_type = OPP_EMPTY - 1
		if (target != None and target in self._update.generals):
			target_type = OPP_GENERAL
		elif (target != None and target in self._update.cities):
			target_type = OPP_CITY
		elif (target != None and target.army > 0):
			target_type = OPP_ARMY
		elif (target != None):
			target_type = OPP_EMPTY

		if (target != None and target.tile == self._update.player_index): # Acquired Target
			target = None
			target_type = OPP_EMPTY - 1

		# Determine Max Target Size
		general_tile = self._update.generals[self._update.player_index]
		max_target_size = self._update.grid[general_tile.y][general_tile.x].army * 1.5

		for x in _shuffle(range(self._update.cols)): # Check Each Square
			for y in _shuffle(range(self._update.rows)):
				source = self._update.grid[y][x]

				if (target_type <= OPP_GENERAL): # Search for Generals
					if (source.tile >= 0 and source.tile != self._update.player_index and source in self._update.generals):
						return source

				if (target_type <= OPP_CITY): # Search for Smallest Cities
					if (source.tile != self._update.player_index and source.army < max_target_size and source in self._update.cities):
						if (target_type < OPP_CITY or target.army > source.army):
							target = source
							target_type = OPP_CITY
							newTarget = True

				if (target_type <= OPP_ARMY): # Search for Largest Opponent Armies
					if (source.tile >= 0 and source.tile != self._update.player_index and (target == None or source.army > target.army) and source not in self._update.cities):
						target = source
						target_type = OPP_ARMY

				if (target_type < OPP_EMPTY): # Search for Empty Squares
					if (source.tile == generals.map.TILE_EMPTY and source.army < max_target_size):
						return source

		return target

	######################### Pathfinding #########################

	def find_path(self, source=None, dest=None):
		# Verify Source and Dest
		if (source == None): # No Source, Use General
			source = self._update.generals[self._update.player_index]
		if (dest == None): # No Dest, Use Primary Target
			dest = self.find_primary_target()

		# Determine Path To Destination
		frontier = Queue()
		frontier.put(source)
		came_from = {}
		came_from[source] = None
		self._max_target_size = [[0 for x in range(self._update.cols)] for y in range(self._update.rows)]
		self._max_target_size[source.y][source.x] = source.army - 1

		while not frontier.empty():
			current = frontier.get()

			if current == dest: # Found Destination
				break

			for next in self._neighbors(current, self._max_target_size[current.y][current.x]):
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
			if (self.validPosition(x+dx, y+dy)):
				current = self._update.grid[y+dy][x+dx]

				max_target_size_current = max_target_size
				if (current.tile == self._update.player_index):
					max_target_size_current += (current.army - 1)
				elif (current.army > 0):
					max_target_size_current -= (current.army + 1)

				if (current.tile == self._update.player_index or max_target_size == 0 or current.army < max_target_size):
					if (self._max_target_size[y+dy][x+dx] == 0):
						self._max_target_size[y+dy][x+dx] = max_target_size_current
					neighbors.append(current)

		return neighbors
	

	######################### Movement Helpers #########################

	def _toward_dest_moves(self, source, dest=None):
		# Determine Destination
		if (dest == None):
			dest = self.find_primary_target()

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

	def _distance(self, source, dest):
		return abs(source.x - dest.x) + abs(source.y - dest.y)

	def place_move(self, source, dest, move_half=False):
		if (self.validPosition(dest.x, dest.y)):
			self._game.move(source.y, source.x, dest.y, dest.x, move_half)
			return True
		return False

	def validPosition(self, x, y):
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
