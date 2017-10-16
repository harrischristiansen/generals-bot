'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Tile: Objects for representing Generals IO Tiles
'''

from queue import Queue

from .constants import *

class Tile(object):
	def __init__(self, gamemap, x, y):
		# Public Properties
		self.x = x					# Integer X Coordinate
		self.y = y					# Integer Y Coordinate
		self.tile = TILE_EMPTY		# Integer Tile Type (TILE_OBSTACLE, TILE_FOG, TILE_MOUNTAIN, TILE_EMPTY, or player_ID)
		self.turn_captured = 0		# Integer Turn Tile Last Captured
		self.army = 0				# Integer Army Count
		self.isCity = False			# Boolean isCity
		self.isSwamp = False		# Boolean isSwamp
		self.isGeneral = False		# Boolean isGeneral

		# Private Properties
		self._map = gamemap			# Pointer to Map Object
		self._general_index = -1	# Player Index if tile is a general

	def __repr__(self):
		return "(%d,%d) %d (%d)" % (self.x, self.y, self.tile, self.army)

	'''def __eq__(self, other):
			return (other != None and self.x==other.x and self.y==other.y)'''

	def __lt__(self, other):
			return self.army < other.army

	def setNeighbors(self, gamemap):
		self._map = gamemap
		self._setNeighbors()

	def setIsSwamp(self, isSwamp):
		self.isSwamp = isSwamp

	def update(self, gamemap, tile, army, isCity=False, isGeneral=False):
		self._map = gamemap

		if (self.tile < 0 or tile >= 0 or (tile < TILE_MOUNTAIN and self.tile == gamemap.player_index)): # Remember Discovered Tiles
			if ((tile >= 0 or self.tile >= 0) and self.tile != tile):
				if self.tile >= 0:
					gamemap.tiles[self.tile].remove(self)
				gamemap.tiles[tile].append(self)
				self.turn_captured = gamemap.turn
			self.tile = tile
		if (self.army == 0 or army > 0): # Remember Discovered Armies
			self.army = army

		if isCity:
			self.isCity = True
			self.isGeneral = False
			if self not in gamemap.cities:
				gamemap.cities.append(self)
			if self._general_index != -1 and self._general_index < 8:
				gamemap.generals[self._general_index] = None
				self._general_index = -1
		elif isGeneral:
			self.isGeneral = True
			gamemap.generals[tile] = self
			self._general_index = self.tile

	################################ Tile Properties ################################

	def distance_to(self, dest):
		if dest != None:
			return abs(self.x - dest.x) + abs(self.y - dest.y)
		return 0

	def neighbors(self, includeSwamps=False):
		neighbors = []
		for tile in self._neighbors:
			if (tile.tile != TILE_OBSTACLE or tile.isCity or tile.isGeneral) and tile.tile != TILE_MOUNTAIN and (includeSwamps or not tile.isSwamp):
				neighbors.append(tile)
		return neighbors

	def isValidTarget(self): # Check tile to verify reachability
		for dy, dx in DIRECTIONS:
			if self._map.isValidPosition(self.x+dx, self.y+dy):
				tile = self._map.grid[self.y+dy][self.x+dx]
				if tile.tile != TILE_OBSTACLE or tile in self._map.cities or tile in self._map.generals:
					return True
		return False

	################################ Select Other Tiles ################################

	def nearest_tile_in_path(self, path):
		dest = None
		dest_distance = 9999
		for tile in path:
			distance = self.distance_to(tile)
			if distance < tile_distance:
				dest = tile
				dest_distance = distance

		return dest

	def nearest_target_tile(self):
		max_target_army = self.army * 2 + 14

		dest = None
		dest_distance = 9999
		for x in range(self._map.cols): # Check Each Square
			for y in range(self._map.rows):
				tile = self._map.grid[y][x]
				if (tile.tile < TILE_EMPTY or tile.tile == self._map.player_index or tile.army > max_target_army): # Non Target Tiles
					continue

				distance = self.distance_to(tile)
				if tile in self._map.generals: # Generals appear closer
					distance = distance * 0.13
				elif tile in self._map.cities: # Cities vary distance based on size, but appear closer
					distance = distance * sorted((0.18, (tile.army / (3.2*self.army)), 4))[1]
				elif tile.tile == TILE_EMPTY: # Empties appear further away
					distance = distance * 3.8

				if tile.army > self.army: # Larger targets appear further away
					distance = distance * (1.5*tile.army/self.army)

				if tile.isSwamp: # Swamps appear further away
					distance = distance * 10

				if distance < dest_distance and tile.isValidTarget():
					dest = tile
					dest_distance = distance

		return dest

	################################ Pathfinding ################################

	def path_to(self, dest):
		if dest == None:
			return []

		# Determine Path To Destination
		frontier = Queue()
		frontier.put(self)
		came_from = {}
		came_from[self] = None

		while not frontier.empty():
			current = frontier.get()

			if current == dest: # Found Destination
				break

			for next in current.neighbors():
				if next not in came_from and (next == dest or next.tile == self._map.player_index or next not in self._map.cities): # Add to frontier
					#priority = self.distance(next, dest)
					frontier.put(next)
					came_from[next] = current

		if dest not in came_from: # Did not find dest
			return []

		# Create Path List
		path = _path_reconstruct(came_from, dest)

		return path

	################################ PRIVATE FUNCTIONS ################################

	def _setNeighbors(self):
		x = self.x
		y = self.y

		neighbors = []
		for dy, dx in DIRECTIONS:
			if self._map.isValidPosition(x+dx, y+dy):
				tile = self._map.grid[y+dy][x+dx]
				neighbors.append(tile)

		self._neighbors = neighbors
		return neighbors

def _path_reconstruct(came_from, dest):
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