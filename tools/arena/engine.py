'''
	Local, headless generals.io rules engine used to play two bot versions
	against each other quickly (no network, no viewer, no real-time delay).

	Approximates the real game rules closely enough for relative bot-strength
	comparison: 4-directional movement, cities/generals +1 army/turn,
	all owned tiles +1 army every 25 turns, capture-on-greater-army combat,
	and capturing a general eliminates that player and transfers their board.
'''

TILE_MOUNTAIN = -2
TILE_EMPTY = -1

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

CITY_GENERAL_GROWTH_INTERVAL = 1
LAND_GROWTH_INTERVAL = 25


class TrueBoard(object):
	'''Omniscient board state - the ground truth both players' fogged views are derived from.'''

	def __init__(self, generated_map, num_players=2):
		self.rows = generated_map.rows
		self.cols = generated_map.cols
		self.num_players = num_players
		self.turn = 1

		self.owner = [row[:] for row in generated_map.owner]
		self.army = [row[:] for row in generated_map.army]
		self.is_city = [row[:] for row in generated_map.is_city]
		self.general_positions = list(generated_map.general_positions)
		self.alive = [True for _ in range(num_players)]

		for p, (r, c) in enumerate(self.general_positions):
			self.owner[r][c] = p
			self.army[r][c] = 1

	def in_bounds(self, r, c):
		return 0 <= r < self.rows and 0 <= c < self.cols

	def is_general(self, r, c):
		return (r, c) in self.general_positions

	def apply_move(self, player_index, source, dest, move_half):
		'''source/dest are (row,col) tuples. Illegal moves are silently ignored (as the real server would reject them).'''
		if not self.alive[player_index] or source == dest:
			return

		sr, sc = source
		dr, dc = dest
		if not (self.in_bounds(sr, sc) and self.in_bounds(dr, dc)):
			return
		if abs(sr - dr) + abs(sc - dc) != 1: # Must be 4-directionally adjacent
			return
		if self.owner[sr][sc] != player_index:
			return
		if self.owner[dr][dc] == TILE_MOUNTAIN:
			return
		if self.army[sr][sc] < 2: # Need at least 2 army to move (1 must stay behind)
			return

		if move_half:
			moving = self.army[sr][sc] // 2 # Half stays, half moves (any odd remainder stays)
		else:
			moving = self.army[sr][sc] - 1 # All but 1 moves
		if moving < 1:
			return

		self.army[sr][sc] -= moving

		if self.owner[dr][dc] == player_index: # Reinforcing our own tile
			self.army[dr][dc] += moving
			return

		defender = self.owner[dr][dc]
		if moving > self.army[dr][dc]: # Capture
			self.army[dr][dc] = moving - self.army[dr][dc]
			if self.is_general(dr, dc) and defender >= 0: # Eliminate the defender, absorb their whole board
				self._eliminate(defender, player_index)
			self.owner[dr][dc] = player_index
		elif moving == self.army[dr][dc]: # Mutual destruction, tile stays with defender at 0 army
			self.army[dr][dc] = 0
		else: # Attack repelled
			self.army[dr][dc] -= moving

	def _eliminate(self, loser, winner):
		self.alive[loser] = False
		for r in range(self.rows):
			for c in range(self.cols):
				if self.owner[r][c] == loser:
					self.owner[r][c] = winner
					self.army[r][c] = max(1, self.army[r][c] // 2) # Halve captured armies, matching generals.io general-capture rule

	def advance_growth(self):
		self.turn += 1
		round_growth = (self.turn % LAND_GROWTH_INTERVAL == 0)
		for r in range(self.rows):
			for c in range(self.cols):
				owner = self.owner[r][c]
				if owner < 0:
					continue
				if self.is_city[r][c] or self.is_general(r, c): # Cities/generals grow every turn...
					self.army[r][c] += 1
				if round_growth: # ...and every owned tile (including cities/generals) also grows on round turns
					self.army[r][c] += 1

	def winner(self):
		alive_players = [p for p in range(self.num_players) if self.alive[p]]
		if len(alive_players) == 1:
			return alive_players[0]
		return None

	def scores(self):
		totals = [0] * self.num_players
		tiles = [0] * self.num_players
		for r in range(self.rows):
			for c in range(self.cols):
				owner = self.owner[r][c]
				if owner >= 0:
					totals[owner] += self.army[r][c]
					tiles[owner] += 1
		return [{'i': p, 'total': totals[p], 'tiles': tiles[p], 'dead': not self.alive[p]} for p in range(self.num_players)]

	def visible_cells(self, player_index):
		visible = set()
		for r in range(self.rows):
			for c in range(self.cols):
				if self.owner[r][c] == player_index:
					visible.add((r, c))
					for dy in (-1, 0, 1):
						for dx in (-1, 0, 1):
							nr, nc = r + dy, c + dx
							if self.in_bounds(nr, nc):
								visible.add((nr, nc))
		return visible
