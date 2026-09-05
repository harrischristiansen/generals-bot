'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Replay Simulator: Reconstruct per-turn board state from a parsed replay

	Rules mirror the official simulator (github.com/vzhou842/generals.io-Replay-Utils):
	cities/generals gain 1 army every RECRUIT_RATE turns, all owned land every FARM_RATE
	turns, and capturing a general transfers the loser's tiles at half army.
'''

TILE_EMPTY = -1
TILE_MOUNTAIN = -2
DEAD_GENERAL = -1

RECRUIT_RATE = 2	# 1 army per city/general every _ turns
FARM_RATE = 50		# 1 army per owned land every _ turns


class SimulatedGame(object):
	def __init__(self, replay):
		self.replay = replay
		self.width = replay.mapWidth
		self.height = replay.mapHeight
		self.turn = 0

		size = self.width * self.height
		self.tiles = [TILE_EMPTY] * size
		self.armies = [0] * size

		for index in replay.mountains:
			self.tiles[index] = TILE_MOUNTAIN
		for i, index in enumerate(replay.cities):
			self.armies[index] = replay.cityArmies[i]

		self.cities = list(replay.cities)
		self.generals = list(replay.generals)
		for player, index in enumerate(self.generals):
			self.tiles[index] = player
			self.armies[index] = 1

		self.num_players = len(replay.usernames)
		self.alive = [True] * self.num_players
		self.captured_by = [None] * self.num_players	# player -> who killed them

		self._moves_by_turn = {}
		for move in replay.moves:
			self._moves_by_turn.setdefault(move.turn, []).append(move)

	######################### Board Helpers #########################

	def is_adjacent(self, a, b):
		ar, ac = a // self.width, a % self.width
		br, bc = b // self.width, b % self.width
		return abs(ar - br) + abs(ac - bc) == 1

	def scores(self): # [{'army':, 'land':}] per player
		army = [0] * self.num_players
		land = [0] * self.num_players
		for i, owner in enumerate(self.tiles):
			if owner >= 0:
				army[owner] += self.armies[i]
				land[owner] += 1
		return [{'army': army[p], 'land': land[p]} for p in range(self.num_players)]

	######################### Simulation #########################

	def _attack(self, start, end, is50):
		if self.tiles[start] < 0 or not self.is_adjacent(start, end):
			return False
		if self.tiles[end] == TILE_MOUNTAIN:
			return False
		if self.armies[start] <= 1:
			return False

		reserve = -(-self.armies[start] // 2) if is50 else 1 # ceil(army/2) when moving half

		if self.tiles[end] == self.tiles[start]:
			self.armies[end] += self.armies[start] - reserve
		else:
			if self.armies[end] >= self.armies[start] - reserve: # Attack repelled
				self.armies[end] -= self.armies[start] - reserve
			else: # Takeover
				self.armies[end] = self.armies[start] - reserve - self.armies[end]
				self.tiles[end] = self.tiles[start]

		self.armies[start] = reserve
		return True

	def _apply_move(self, move):
		if self.tiles[move.start] != move.index:
			return False

		before = self.tiles[move.end]
		if not self._attack(move.start, move.end, move.is50):
			return False

		after = self.tiles[move.end]
		if after != before and move.end in self.generals: # General captured
			loser = self.generals.index(move.end)
			self.alive[loser] = False
			self.captured_by[loser] = after
			for i, owner in enumerate(self.tiles): # Winner absorbs their board at half army
				if owner == before:
					self.tiles[i] = after
					self.armies[i] = round(self.armies[i] * 0.5)
			self.cities.append(move.end)
			self.generals[loser] = DEAD_GENERAL

		return True

	def step(self): # Advance exactly one turn
		for move in self._moves_by_turn.get(self.turn, []):
			self._apply_move(move)

		self.turn += 1

		if self.turn % RECRUIT_RATE == 0:
			for index in self.generals:
				if index != DEAD_GENERAL:
					self.armies[index] += 1
			for index in self.cities:
				if self.tiles[index] >= 0:
					self.armies[index] += 1

		if self.turn % FARM_RATE == 0:
			for i, owner in enumerate(self.tiles):
				if owner >= 0:
					self.armies[i] += 1

	def run(self, until_turn=None, on_turn=None): # Replay the game, optionally calling on_turn(self) each turn
		last_turn = max(self._moves_by_turn) if self._moves_by_turn else 0
		if until_turn is None:
			until_turn = last_turn + 1

		while self.turn <= until_turn:
			self.step()
			if on_turn:
				on_turn(self)
			if sum(1 for a in self.alive if a) <= 1:
				break

		return self

	def winner(self):
		alive = [p for p in range(self.num_players) if self.alive[p]]
		if len(alive) == 1:
			return alive[0]
		return None
