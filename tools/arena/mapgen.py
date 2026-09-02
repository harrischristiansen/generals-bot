'''
	Random test-map generator for the local bot arena.
	Produces a 25x25-style board with two generals on opposite sides,
	randomly placed mountains and neutral cities, guaranteed to be
	connected (a route exists between the two generals).
'''

import random
from collections import deque

TILE_MOUNTAIN = -2
TILE_EMPTY = -1

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


class GeneratedMap(object):
	def __init__(self, rows, cols, owner, army, is_city, general_positions):
		self.rows = rows
		self.cols = cols
		self.owner = owner						# 2D [row][col] -> player index, -1 neutral, TILE_MOUNTAIN
		self.army = army						# 2D [row][col] -> int
		self.is_city = is_city					# 2D [row][col] -> bool
		self.general_positions = general_positions	# [(row,col), ...] indexed by player index


def _in_bounds(rows, cols, r, c):
	return 0 <= r < rows and 0 <= c < cols


def _connected(rows, cols, owner, start, goal):
	if start == goal:
		return True
	seen = {start}
	frontier = deque([start])
	while frontier:
		r, c = frontier.popleft()
		for dr, dc in DIRECTIONS:
			nr, nc = r + dr, c + dc
			if not _in_bounds(rows, cols, nr, nc) or (nr, nc) in seen:
				continue
			if owner[nr][nc] == TILE_MOUNTAIN:
				continue
			if (nr, nc) == goal:
				return True
			seen.add((nr, nc))
			frontier.append((nr, nc))
	return False


def _carve_path(rows, cols, owner, start, goal):
	# Guarantee connectivity by clearing a simple L-shaped corridor between start and goal
	r, c = start
	gr, gc = goal
	while c != gc:
		c += 1 if gc > c else -1
		if owner[r][c] == TILE_MOUNTAIN:
			owner[r][c] = TILE_EMPTY
	while r != gr:
		r += 1 if gr > r else -1
		if owner[r][c] == TILE_MOUNTAIN:
			owner[r][c] = TILE_EMPTY


def generate_map(rows=25, cols=25, mountain_density=0.18, city_count=6, city_army_range=(40, 50),
					general_margin=0.22, min_general_distance=None, seed=None, max_attempts=300):
	rng = random.Random(seed)

	if min_general_distance is None:
		min_general_distance = (rows + cols) // 2

	left_max_col = max(1, int(cols * general_margin))
	right_min_col = min(cols - 2, cols - 1 - int(cols * general_margin))

	for attempt in range(max_attempts):
		owner = [[TILE_EMPTY for _ in range(cols)] for _ in range(rows)]
		army = [[0 for _ in range(cols)] for _ in range(rows)]
		is_city = [[False for _ in range(cols)] for _ in range(rows)]

		general_a = (rng.randrange(0, rows), rng.randrange(0, left_max_col + 1))
		general_b = (rng.randrange(0, rows), rng.randrange(right_min_col, cols))

		if abs(general_a[0] - general_b[0]) + abs(general_a[1] - general_b[1]) < min_general_distance:
			continue # Too close together, try a fresh layout

		reserved = {general_a, general_b}
		for gr, gc in (general_a, general_b): # Keep a 1-tile clearing around each general
			for dr, dc in DIRECTIONS:
				nr, nc = gr + dr, gc + dc
				if _in_bounds(rows, cols, nr, nc):
					reserved.add((nr, nc))

		for r in range(rows): # Scatter mountains
			for c in range(cols):
				if (r, c) in reserved:
					continue
				if rng.random() < mountain_density:
					owner[r][c] = TILE_MOUNTAIN

		if not _connected(rows, cols, owner, general_a, general_b):
			continue # Regenerate mountains rather than settle for a blocked map

		open_cells = [(r, c) for r in range(rows) for c in range(cols)
						if (r, c) not in reserved and owner[r][c] != TILE_MOUNTAIN]
		rng.shuffle(open_cells)
		for r, c in open_cells[:city_count]:
			is_city[r][c] = True
			army[r][c] = rng.randint(city_army_range[0], city_army_range[1])

		return GeneratedMap(rows, cols, owner, army, is_city, [general_a, general_b])

	# Fallback: last layout, forcibly carved connected
	_carve_path(rows, cols, owner, general_a, general_b)
	open_cells = [(r, c) for r in range(rows) for c in range(cols)
					if (r, c) not in reserved and owner[r][c] != TILE_MOUNTAIN]
	rng.shuffle(open_cells)
	for r, c in open_cells[:city_count]:
		is_city[r][c] = True
		army[r][c] = rng.randint(city_army_range[0], city_army_range[1])

	return GeneratedMap(rows, cols, owner, army, is_city, [general_a, general_b])
