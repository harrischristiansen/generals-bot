'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Tile: Objects for representing Generals IO Tiles
'''

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

	def __repr__(self):
		return "(%d,%d) %d (%d)" % (self.x, self.y, self.tile, self.army)

	'''def __eq__(self, other):
			return (other != None and self.x==other.x and self.y==other.y)'''

	def __lt__(self, other):
			return self.army < other.army

	def setSwamp(self, isSwamp):
		self.isSwamp = isSwamp

	def update(self, map, tile, army, isCity=False, isGeneral=False):
		if (self.tile < 0 or tile >= 0 or (tile < TILE_MOUNTAIN and self.tile == map.player_index)): # Remember Discovered Tiles
			if ((tile >= 0 or self.tile >= 0) and self.tile != tile):
				self.turn_captured = map.turn
			self.tile = tile
		if (self.army == 0 or army > 0): # Remember Discovered Armies
			self.army = army

		if isCity:
			self.isCity = True
			self.isGeneral = False
			if self in map.cities:
				map.cities.remove(self)
			map.cities.append(self)
			if self in map.generals:
				map.generals[self._general_index] = None
		elif isGeneral:
			self.isGeneral = True
			map.generals[tile] = self
			self._general_index = self.tile
