
import logging
from pprint import pprint
import random

import client.generals as generals

# Show all logging
logging.basicConfig(level=logging.DEBUG)

DISTRIBUTE_MIN = 10
DISTRIBUTE_GREATER = 5

class GeneralsBot(object):
	def __init__(self):
		# Create Game
		#self._game = generals.Generals('GeneralsTest', 'GeneralsTest', 'private', gameid='HyI4d3_rl') # Private Game - http://generals.io/games/HyI4d3_rl
		self._game = generals.Generals('GeneralsTest', 'GeneralsTest', '1v1') # 1v1
		#self._game = generals.Generals('GeneralsTest', 'GeneralsTest', 'ffa') # FFA

		self._start_update_loop()

	def _start_update_loop(self):
		for update in self._game.get_updates():
			if (self._set_update(update)):
				break

			pprint(update['army_grid'])
			self._move();

	def _set_update(self, update):
		self._update = update

		if (update['complete']):
			print("!!!! Game Complete. Result = " + str(update['result']) + " !!!!")
			return True

		self._pi = update['player_index']
		self._rows = update['rows']
		self._cols = update['cols']

		return False

	def _move(self):
		# Expand Outward
		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_tile = self._update['tile_grid'][y][x]
				source_army = self._update['army_grid'][y][x]
				if (source_tile == self._pi and source_army > 2): # Find One With Armies
					for dy, dx in self._explore_moves(x,y):
						if (self._validPosition(x+dx,y+dy)):
							dest_tile = self._update['tile_grid'][y+dy][x+dx]
							dest_army = self._update['army_grid'][y+dy][x+dx]
							if (dest_army > 0):
								dest_army += 2
							if (dest_tile != self._pi and source_army > dest_army): # Capture Somewhere New
								self._place_move(y, x, y+dy, x+dx)

		# Distribute Armies
		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_tile = self._update['tile_grid'][y][x]
				source_army = self._update['army_grid'][y][x]
				if (source_tile == self._pi and source_army > DISTRIBUTE_MIN): # Find One With Armies
					for dy, dx in _shuffle([(0, 1), (0, -1), (1, 0), (-1, 0)]):
						if (self._validPosition(x+dx,y+dy)):
							dest_tile = self._update['tile_grid'][y+dy][x+dx]
							dest_army = self._update['army_grid'][y+dy][x+dx]
							if (source_army > (dest_army + DISTRIBUTE_GREATER)): # Position has less army count
								if (self._place_move(y, x, y+dy, x+dx, move_half=True)):
									return

	def _explore_moves(self, x, y):
		positions = [(0, 1), (0, -1), (1, 0), (-1, 0)]
		first_positions = []
		for dy, dx in positions:
			if (self._validPosition(x+dx,y+dy)):
				dest_tile = self._update['tile_grid'][y+dy][x+dx]
				dest_army = self._update['army_grid'][y+dy][x+dx]
				if (dest_tile != 0 and dest_tile != self._pi):
					first_positions.append((dy,dx))
					positions.remove((dy,dx))

		first_positions.extend(_shuffle(positions))
		return first_positions

	def _place_move(self, y1, x1, y2, x2, move_half=False):
		if (self._validPosition(x2, y2)):
			self._game.move(y1, x1, y2, x2, move_half)
			return True
		return False

	def _validPosition(self, x, y):
		return 0 <= y < self._rows and 0 <= x < self._cols and self._update['tile_grid'][y][x] != generals.MOUNTAIN

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)

# Start Bot
GeneralsBot()