'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Base Bot Class
'''

import logging
from Queue import PriorityQueue
import random
import threading
import time

from client import generals
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
		window_title = "%s (%s)" % (self._name, self._gameType)
		self._viewer = GeneralsViewer(window_title)
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
			msg = str(raw_input('Send Msg:'))
			self._game.send_chat(msg)
			time.sleep(0.7)

	######################### Handle Updates From Server #########################

	def _start_update_loop(self):
		for update in self._game.get_updates():
			self._set_update(update)

			if (not self._running):
				return

			self._make_move()

			# Update GeneralsViewer Grid
			if '_viewer' in dir(self):
				if '_path' in dir(self):
					self._update.path = self._path
				if '_collect_path' in dir(self):
					self._update.collect_path = self._collect_path
				self._viewer.updateGrid(self._update)

	def _set_update(self, update):
		if (update.complete):
			print("!!!! Game Complete. Result = " + str(update.result) + " !!!!")
			self._running = False
			return

		self._update = update

	######################### Move Generation #########################

	def _make_move(self):
		self._updateMethod(self, self._update)

	######################### Tile Finding #########################

	def find_largest_tile(self, ofType=None, notInPath=[], includeGeneral=False): # ofType = Integer, notInPath = [Tile], includeGeneral = False|True|Int Acceptable Largest|0.1->0.9 Ratio
		if (ofType == None):
			ofType = self._update.player_index
		general = self._update.generals[ofType]

		largest = None
		for x in range(self._update.cols): # Check Each Square
			for y in range(self._update.rows):
				tile = self._update.grid[y][x]
				if (tile.tile == ofType and (largest == None or largest.army < tile.army)): # New Largest
					if ((tile not in notInPath) and tile != general): # Exclude Path and General
						largest = tile

		if (includeGeneral > 0): # Handle includeGeneral
			if (includeGeneral < 1):
				includeGeneral = general.army * includeGeneral
				if (includeGeneral < 6):
					includeGeneral = 6
			if (largest == None): 
				largest = general
			elif (includeGeneral == True and largest.army < general.army):
				largest = general
			elif (includeGeneral > True and largest.army < general.army and largest.army <= includeGeneral):
				largest = general

		return largest

	def find_city(self, ofType=None, notOfType=None, notInPath=[], findLargest=True, includeGeneral=False): # ofType = Integer, notOfType = Integer, notInPath = [Tile], findLargest = Boolean
		if (ofType == None and notOfType == None):
			ofType = self._update.player_index

		found_city = None
		for city in self._update.cities: # Check Each City
			if (city in notInPath):
				continue

			if (city.tile == ofType or (notOfType != None and city.tile != notOfType)):
				if (found_city == None):
					found_city = city
				if (findLargest and found_city.army < city.army) or (not findLargest and city.army < found_city.army):
					found_city = city

		if includeGeneral:
			general = self._update.generals[ofType]
			if (found_city == None):
				return general
			if (general != None and ((findLargest and general.army > found_city.army) or (not findLargest and general.army < found_city.army))):
				return general

		return found_city

	def find_closest_in_path(self, tile, path):
		closest = None
		closest_distance = 9999
		for x in range(self._update.cols): # Check Each Square
			for y in range(self._update.rows):
				dest = self._update.grid[y][x]
				if (dest in path):
					distance = self.distance(tile, dest)
					if (distance < closest_distance):
						closest = dest
						closest_distance = distance

		return closest

	def find_closest_target(self, source):
		max_target_army = source.army * 2 + 14

		closest = None
		closest_distance = 9999
		for x in range(self._update.cols): # Check Each Square
			for y in range(self._update.rows):
				dest = self._update.grid[y][x]
				if (dest.tile < generals.map.TILE_EMPTY or dest.tile == self._update.player_index or dest.army > max_target_army): # Non Target Tiles
					continue

				distance = self.distance(source, dest)
				if (dest in self._update.generals): # Generals appear closer
					distance = distance * 0.17
				elif (dest in self._update.cities): # Cities vary distance based on size
					distance = distance * sorted((0.22, (dest.army / source.army), 4))[1]
				elif (dest.tile == generals.map.TILE_EMPTY): # Empties appear further away
					distance = distance * 1.7

				if (dest.army > source.army): # Larger targets appear further away
					distance = distance * (1.5*dest.army/source.army)

				if (distance < closest_distance and self._validTarget(dest)):
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
		largest = self.find_largest_tile(includeGeneral=True)
		max_target_size = largest.army * 1.25

		for x in _shuffle(range(self._update.cols)): # Check Each Square
			for y in _shuffle(range(self._update.rows)):
				source = self._update.grid[y][x]

				if (not self._validTarget(source)):
					continue

				if (target_type <= OPP_GENERAL): # Search for Generals
					if (source.tile >= 0 and source.tile != self._update.player_index and source in self._update.generals and source.army < largest.army):
						return source

				if (target_type <= OPP_CITY): # Search for Smallest Cities
					if (source.tile != self._update.player_index and source.army < max_target_size and source in self._update.cities):
						if (target_type < OPP_CITY or source.army < target.army):
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

		# Current Player Largest Army
		largest = self.find_largest_tile(includeGeneral=True)

		# Determine Path To Destination
		frontier = PriorityQueue()
		frontier.put(source, largest.army - source.army)
		came_from = {}
		cost_so_far = {}
		came_from[source] = None
		cost_so_far[source] = largest.army - source.army

		while not frontier.empty():
			current = frontier.get()

			if current == dest: # Found Destination
				break

			for next in self._neighbors(current):
				# Calculate New Cost
				new_cost = next.army
				if (next.tile == self._update.player_index):
					new_cost = 0 - new_cost
				new_cost = cost_so_far[current] + largest.army + new_cost

				# Add to frontier
				if next not in cost_so_far or (new_cost < cost_so_far[next] and next not in self._path_reconstruct(came_from, current)):
					cost_so_far[next] = new_cost

					# Calculate Priority
					priority = new_cost + (self.distance(next, dest)**2)
					if (next.tile != self._update.player_index and (next in self._update.cities or next in self._update.generals)): # Increase Priority of New Cities
						priority = priority - largest.army

					frontier.put(next, priority)
					came_from[next] = current

		# Create Path List
		path = self._path_reconstruct(came_from, dest)

		return path

	def _path_reconstruct(self, came_from, dest):
		current = dest
		path = [current]
		try:
			while came_from[current] != None:
				current = came_from[current]
				path.append(current)
		except KeyError:
			None
		path.reverse()

		return path

	def _neighbors(self, source):
		x = source.x
		y = source.y

		neighbors = []
		for dy, dx in DIRECTIONS:
			if (self.validPosition(x+dx, y+dy)):
				current = self._update.grid[y+dy][x+dx]
				if (current.tile != generals.map.TILE_OBSTACLE or current in self._update.cities or current in self._update.generals):
					neighbors.append(current)

		return neighbors
	

	######################### Movement Helpers #########################

	def path_forward_moves(self, path):
		if (len(path) < 2):
			return (None, None)

		# Find largest tile in path to move forward
		largest = path[0]
		largest_index = 0
		for i, tile in enumerate(path):
			if (tile == path[-1]):
				break
			if (tile.tile == path[0].tile and tile > largest):
				largest = tile
				largest_index = i

		dest = path[largest_index+1]
		return (largest, dest)

	def toward_dest_moves(self, source, dest=None):
		# Determine Destination
		if (dest == None):
			dest = self.find_primary_target()

		# Compute X/Y Directions
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

	def away_king_moves(self, source):
		general = self._update.generals[self._update.player_index]

		if (source.y == general.y and source.x == general.x): # Moving from General
			return self.moves_random()

		dir_y = 1
		if source.y < general.y:
			dir_y = -1

		dir_x = 1
		if source.x < general.x:
			dir_x = -1

		moves = random.sample([(0, dir_x), (dir_y, 0)],2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)],2))
		return moves

	def moves_random(self):
		return random.sample(DIRECTIONS, 4)

	def distance(self, source, dest):
		return abs(source.x - dest.x) + abs(source.y - dest.y)

	def place_move(self, source, dest, move_half=False):
		if (self.validPosition(dest.x, dest.y)):
			self._game.move(source.y, source.x, dest.y, dest.x, move_half)
			return True
		return False

	def validPosition(self, x, y):
		return 0 <= y < self._update.rows and 0 <= x < self._update.cols and self._update._tile_grid[y][x] != generals.map.TILE_MOUNTAIN

	def _validTarget(self, target): # Check target to verify reachable
		for dy, dx in self.moves_random():
			if (self.validPosition(target.x+dx, target.y+dy)):
				tile = self._update.grid[target.y+dy][target.x+dx]
				if (tile.tile != generals.map.TILE_OBSTACLE or tile in self._update.cities or tile in self._update.generals):
					return True
		return False


######################### Global Helpers #########################

def _create_thread(f):
	t = threading.Thread(target=f)
	t.daemon = True
	t.start()

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)
