'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Map: Objects for representing Generals IO Map
'''

import logging

from .constants import *
from .tile import Tile

class Map(object):
	def __init__(self, start_data, data):
		# Start Data
		self._start_data = start_data
		self.player_index = start_data['playerIndex'] 									# Integer Player Index
		self.usernames = start_data['usernames'] 										# List of String Usernames
		self.replay_url = REPLAY_URLS["na"] + start_data['replay_id'] 					# String Replay URL          # TODO: Use Client Region

		# First Game Data
		self._applyUpdateDiff(data)
		self.rows = self.rows 															# Integer Number Grid Rows
		self.cols = self.cols 															# Integer Number Grid Cols
		self.grid = [[Tile(self,x,y) for x in range(self.cols)] for y in range(self.rows)]	# 2D List of Tile Objects
		self._setNeighbors()
		self.swamps = [(c // self.cols, c % self.cols) for c in start_data['swamps']] 	# List [(y,x)] of swamps
		self._setSwamps()
		self.turn = data['turn']														# Integer Turn # (1 turn / 0.5 seconds)
		self.tiles = [[] for x in range(12)]											# List of 8 (+ extra) Players Tiles
		self.cities = []																# List of City Tiles
		self.generals = [None for x in range(12)]										# List of 8 (+ extra) Generals (None if not found)
		self._setGenerals()
		self.stars = []																	# List of Player Star Ratings
		self.scores = self._getScores(data)												# List of Player Scores
		self.complete = False															# Boolean Game Complete
		self.result = False																# Boolean Game Result (True = Won)

		# Public Options
		self.exit_on_game_over = True													# Controls if bot exits after game over
		self.do_not_attack_players = []													# List of player IDs not to attack
	
	################################ Game Updates ################################

	def update(self, data):
		if self.complete: # Game Over - Ignore Empty Board Updates
			return self

		self._applyUpdateDiff(data)
		self.scores = self._getScores(data)
		self.turn = data['turn']

		for x in range(self.cols): # Update Each Tile
			for y in range(self.rows):
				tile_type = self._tile_grid[y][x]
				army_count = self._army_grid[y][x]
				isCity = (y,x) in self._visible_cities
				isGeneral = (y,x) in self._visible_generals
				self.grid[y][x].update(self, tile_type, army_count, isCity, isGeneral)

		return self

	def updateResult(self, result):
		self.complete = True
		self.result = result == "game_won"
		return self

	################################ Map Search/Selection ################################

	def find_city(self, ofType=None, notOfType=None, notInPath=[], findLargest=True, includeGeneral=False): # ofType = Integer, notOfType = Integer, notInPath = [Tile], findLargest = Boolean
		if ofType == None and notOfType == None:
			ofType = self.player_index

		found_city = None
		for city in self.cities: # Check Each City
			if city.tile == ofType or (notOfType != None and city.tile != notOfType):
				if city in notInPath:
					continue
				if found_city == None:
					found_city = city
				elif (findLargest and found_city.army < city.army) or (not findLargest and city.army < found_city.army):
					found_city = city

		if includeGeneral:
			general = self.generals[ofType]
			if found_city == None:
				return general
			if general != None and ((findLargest and general.army > found_city.army) or (not findLargest and general.army < found_city.army)):
				return general

		return found_city

	def find_largest_tile(self, ofType=None, notInPath=[], includeGeneral=False): # ofType = Integer, notInPath = [Tile], includeGeneral = False|True|Int Acceptable Largest|0.1->0.9 Ratio
		if ofType == None:
			ofType = self.player_index
		general = self.generals[ofType]
		if general == None:
			logging.error("ERROR: find_largest_tile encountered general=None for player %d with list %s" % (ofType, self.generals))

		largest = None
		for tile in self.tiles[ofType]: # Check each ofType tile
			if largest == None or largest.army < tile.army: # New largest
				if not tile.isGeneral and tile not in notInPath: # Exclude general and path
					largest = tile

		if includeGeneral > 0 and general != None and general not in notInPath: # Handle includeGeneral
			if includeGeneral < 1:
				includeGeneral = general.army * includeGeneral
				if includeGeneral < 6:
					includeGeneral = 6
			if largest == None:
				largest = general
			elif includeGeneral == True and largest.army < general.army:
				largest = general
			elif includeGeneral > True and largest.army < general.army and largest.army <= includeGeneral:
				largest = general

		return largest

	################################ Validators ################################

	def isValidPosition(self, x, y):
		return 0 <= y < self.rows and 0 <= x < self.cols and self._tile_grid[y][x] != TILE_MOUNTAIN

	def canCompletePath(self, path):
		if len(path) < 2:
			return False
		
		army_total = 0
		for tile in path: # Verify can obtain every tile in path
			if tile.isSwamp:
				army_total -= 1

			if tile.tile == self.player_index:
				army_total += tile.army - 1
			elif tile.army + 1 > army_total: # Cannot obtain tile
				return False
		return True

	def canStepPath(self, path):
		if len(path) < 2:
			return False
		
		army_total = 0
		for tile in path: # Verify can obtain at least one tile in path
			if tile.isSwamp:
				army_total -= 1

			if tile.tile == self.player_index:
				army_total += tile.army - 1
			else:
				if tile.army + 1 > army_total: # Cannot obtain tile
					return False
				return True
		return True

	################################ PRIVATE FUNCTIONS ################################

	def _getScores(self, data):
		scores = {s['i']: s for s in data['scores']}
		scores = [scores[i] for i in range(len(scores))]

		if 'stars' in data:
			self.stars[:] = data['stars']

		return scores

	def _applyUpdateDiff(self, data):
		if not '_map_private' in dir(self):
			self._map_private = []
			self._cities_private = []
		_apply_diff(self._map_private, data['map_diff'])
		_apply_diff(self._cities_private, data['cities_diff'])

		# Get Number Rows + Columns
		self.rows, self.cols = self._map_private[1], self._map_private[0]

		# Create Updated Tile Grid
		self._tile_grid = [[self._map_private[2 + self.cols*self.rows + y*self.cols + x] for x in range(self.cols)] for y in range(self.rows)]
		# Create Updated Army Grid
		self._army_grid = [[self._map_private[2 + y*self.cols + x] for x in range(self.cols)] for y in range(self.rows)]

		# Update Visible Cities
		self._visible_cities = [(c // self.cols, c % self.cols) for c in self._cities_private] # returns [(y,x)]

		# Update Visible Generals
		self._visible_generals = [(-1, -1) if g == -1 else (g // self.cols, g % self.cols) for g in data['generals']] # returns [(y,x)]

	def _setNeighbors(self):
		for x in range(self.cols):
			for y in range(self.rows):
				self.grid[y][x].setNeighbors(self)

	def _setSwamps(self):
		for (y,x) in self.swamps:
			self.grid[y][x].setIsSwamp(True)

	def _setGenerals(self):
		for i, general in enumerate(self._visible_generals):
			if general[0] != -1:
				self.generals[i] = self.grid[general[0]][general[1]]

def _apply_diff(cache, diff):
	i = 0
	a = 0
	while i < len(diff) - 1:

		# offset and length
		a += diff[i]
		n = diff[i+1]

		cache[a:a+n] = diff[i+2:i+2+n]
		a += n
		i += n + 2

	if i == len(diff) - 1:
		cache[:] = cache[:a+diff[i]]
		i += 1

	assert i == len(diff)
