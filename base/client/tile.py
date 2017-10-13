'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Tile: Objects for representing Generals IO Tiles
'''

from queue import Queue

from .constants import *

class Tile(object):
	def __init__(self, x, y):
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
		self._general_index = -1	# Player Index if tile is a general

	def __repr__(self):
		return "(%d,%d) %d (%d)" % (self.x, self.y, self.tile, self.army)

	'''def __eq__(self, other):
			return (other != None and self.x==other.x and self.y==other.y)'''

	def __lt__(self, other):
			return self.army < other.army

	def setIsSwamp(self, isSwamp):
		self.isSwamp = isSwamp

	def update(self, map, tile, army, isCity=False, isGeneral=False):
		self._map = map

		if (self.tile < 0 or tile >= 0 or (tile < TILE_MOUNTAIN and self.tile == map.player_index)): # Remember Discovered Tiles
			if ((tile >= 0 or self.tile >= 0) and self.tile != tile):
				if self.tile >= 0:
					map.tiles[self.tile].remove(self)
				map.tiles[tile].append(self)
				self.turn_captured = map.turn
			self.tile = tile
		if (self.army == 0 or army > 0): # Remember Discovered Armies
			self.army = army

		if isCity:
			self.isCity = True
			self.isGeneral = False
			if self not in map.cities:
				map.cities.append(self)
				print(map.cities)
			if self._general_index != -1 and self._general_index < 8:
				map.generals[self._general_index] = None
				self._general_index = -1
		elif isGeneral:
			self.isGeneral = True
			map.generals[tile] = self
			self._general_index = self.tile

	################################ Select Other Tiles ################################

	def neighbors(self, includeSwamps=False):
		x = self.x
		y = self.y

		neighbors = []
		for dy, dx in DIRECTIONS:
			if self._map.isValidPosition(x+dx, y+dy):
				current = self._map.grid[y+dy][x+dx]
				if (current.tile != TILE_OBSTACLE or current in self._map.cities or current in self._map.generals) and (includeSwamps or not self.isSwamp):
					neighbors.append(current)

		return neighbors

	################################ Pathfinding ################################

	def find_path(self, dest):
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

		# Create Path List
		path = _path_reconstruct(came_from, dest)

		return path

################################ PRIVATE FUNCTIONS ################################

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