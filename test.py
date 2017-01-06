
import logging
import client.generals as generals

# Show all logging
logging.basicConfig(level=logging.DEBUG)

class GeneralsBot(object):
	def __init__(self):
		# Create Private Game
		self._game = generals.Generals('your userid', 'GeneralsTest', 'private', gameid='HyI4d3_rl')

		self._start_update_loop()

	def _start_update_loop(self):
		for update in self._game.get_updates():
			if (self._set_update(update)):
				break

			self._move();

	def _set_update(self, update):
		self._update = update

		if (update['complete']):
			print("Game Complete. Result = " + update['result'])
			return True

		self._pi = update['player_index']
		self._rows = update['rows']
		self._cols = update['cols']

		return False

	def _move(self):
		tile_grid = self._update['tile_grid']
		army_grid = self._update['army_grid']
		for x in range(self._cols): # Check Each Square
			for y in range(self._rows):
				if (tile_grid[y][x] == self._pi and army_grid[y][x] > 2): # Find One With Armies
					for dy, dx in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
						if (self._validPosition(x+dx,y+dy) and tile_grid[y+dy][x+dx] != self._pi and army_grid[y][x] > army_grid[y+dy][x+dx]): # Capture Somewhere New
							if (self._place_move(y, x, y+dy, x+dx)):
								break

	def _place_move(self, y1, x1, y2, x2, move_half=False):
		if (self._validPosition(x2, y2)):
			self._game.move(y1, x1, y2, x2, move_half)
			return True
		return False

	def _validPosition(self, x, y):
		return 0 <= y < self._rows and 0 <= x < self._cols and self._update['tile_grid'][y][x] != generals.MOUNTAIN

# Start Bot
GeneralsBot()