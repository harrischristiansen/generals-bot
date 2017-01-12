'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Map: Objects for representing Generals IO Map and Tiles
'''

TILE_EMPTY = -1
TILE_MOUNTAIN = -2
TILE_FOG = -3
TILE_OBSTACLE = -4

_REPLAY_URLS = {
	'na': "http://generals.io/replays/",
	'eu': "http://eu.generals.io/replays/",
}

class Map(object):
	def __init__(self, start_data, data):
		# Start Data
		self._start_data = start_data
		self.player_index = start_data['playerIndex']
		self.usernames = start_data['usernames']
		self.replay_url = _REPLAY_URLS["na"] + start_data['replay_id'] # TODO: Use Client Region

		# First Game Data
		self._applyUpdateDiff(data)
		self.grid = [[Tile(x,y) for x in range(self.cols)] for y in range(self.rows)]
		self.turn = data['turn']
		self.cities = []
		self.generals = []
		self.stars = []
		self.scores = self._getScores(data)
		self.complete = False
		self.result = False
		

	def update(self, data):
		self._applyUpdateDiff(data)
		self.scores = self._getScores(data)
		self.turn = data['turn']

		for x in range(self.cols): # Update Each Tile
			for y in range(self.rows):
				tile_type = self._tile_grid[y][x]
				army_count = self._army_grid[y][x]
				isCity = (y,x) in self._visible_cities
				isGeneral = (y,x) in self._visible_generals
				self.grid[y][x].update(self.cities, self.generals, tile_type, army_count, isCity, isGeneral)

		return self

	def result(self, result):
		self.complete = True
		self.result = result == "game_won"
		return self

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

class Tile(object):
	def __init__(self, x, y):
		# Public Properties
		self.x = x
		self.y = y
		self.tile = TILE_EMPTY
		self.army = 0
		self.isCity = False
		self.isGeneral = False

	def __repr__(self):
		return str(self._x)+","+str(self._y)

	def update(self, cities, generals, tile, army, isCity=False, isGeneral=False):
		self.tile = tile # TODO: Do not update if city -> obstalce
		self.army = army
		if isCity:
			self.isCity = True
			self.isGeneral = False
			if self not in cities:
				cities.append(self)
			if self in generals:
				generals.remove(self)
		if isGeneral:
			self.isGeneral = True
			if self not in generals:
				generals.append(self)

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
