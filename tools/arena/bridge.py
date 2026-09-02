'''
	Builds the same start_data/data wire-format dicts the real generals.io server sends
	to a client, computed from the omniscient TrueBoard with fog of war applied per player.
	This lets each worker's unmodified Map.__init__/Map.update() consume it exactly like
	a real game update, regardless of which git commit that Map class came from.
'''

TILE_MOUNTAIN = -2
TILE_EMPTY = -1
TILE_FOG = -3


class PlayerMemory(object):
	'''What a single player has permanently discovered - mirrors what the real server
	remembers on their behalf: cities/generals never un-discover, everything else
	(plain land/army) reverts to fog once out of vision.'''

	def __init__(self, player_index, board):
		self.player_index = player_index
		self.known_cities = []			# ordered [(row,col), ...] ever seen as a city
		self._known_city_set = set()
		self.known_mountains = set()	# {(row,col), ...} ever seen as a mountain
		self.known_generals = {player_index: board.general_positions[player_index]} # player_index -> (row,col)

	def observe(self, board, visible):
		for (r, c) in visible:
			if board.is_city[r][c] and (r, c) not in self._known_city_set:
				self._known_city_set.add((r, c))
				self.known_cities.append((r, c))
			if board.owner[r][c] == TILE_MOUNTAIN:
				self.known_mountains.add((r, c))
		for p, pos in enumerate(board.general_positions):
			if p not in self.known_generals and pos in visible:
				self.known_generals[p] = pos


def _diff_full_replace(values):
	return [0, len(values)] + list(values) + [0]


def build_start_data(player_index, usernames):
	return {
		'playerIndex': player_index,
		'usernames': usernames,
		'replay_id': 'local-arena',
		'swamps': [],
	}


def build_update(board, player_index, memory):
	visible = board.visible_cells(player_index)
	memory.observe(board, visible)

	rows, cols = board.rows, board.cols
	army_flat = [0] * (rows * cols)
	type_flat = [0] * (rows * cols)

	for r in range(rows):
		for c in range(cols):
			idx = r * cols + c
			if (r, c) in visible:
				army_flat[idx] = board.army[r][c]
				type_flat[idx] = board.owner[r][c]
			elif (r, c) in memory.known_mountains:
				type_flat[idx] = TILE_MOUNTAIN
			else:
				type_flat[idx] = TILE_FOG

	map_flat = [cols, rows] + army_flat + type_flat
	city_positions = [r * cols + c for (r, c) in memory.known_cities]

	generals = []
	for p in range(board.num_players):
		if p in memory.known_generals:
			r, c = memory.known_generals[p]
			generals.append(r * cols + c)
		else:
			generals.append(-1)

	return {
		'turn': board.turn,
		'map_diff': _diff_full_replace(map_flat),
		'cities_diff': _diff_full_replace(city_positions),
		'generals': generals,
		'scores': board.scores(),
	}
