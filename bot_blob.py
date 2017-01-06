
import logging
from pprint import pprint
import random
import threading
import time

import client.generals as generals

# Show all logging
logging.basicConfig(level=logging.DEBUG)

DISTRIBUTE_MIN = 10
DISTRIBUTE_GREATER = 5

class GeneralsBot(object):
	def __init__(self):
		# Create Game
		#self._game = generals.Generals('PurdueBot', 'PurdueBot', 'private', gameid='HyI4d3_rl') # Private Game - http://generals.io/games/HyI4d3_rl
		#self._game = generals.Generals('PurdueBot', 'PurdueBot', '1v1') # 1v1
		self._game = generals.Generals('PurdueBot', 'PurdueBot', 'ffa') # FFA

		_create_thread(self._start_update_loop)

		while (True):
			msg = input('Send Msg:')
			print("Sending MSG: " + msg)
			# TODO: Send msg

	def _start_update_loop(self):
		firstUpdate = True

		for update in self._game.get_updates():
			if (self._set_update(update)):
				break

			if (firstUpdate):
				_create_thread(self._start_moves)
				firstUpdate = False

			pprint(update['army_grid'])

	def _set_update(self, update):
		self._update = update

		if (update['complete']):
			print("!!!! Game Complete. Result = " + str(update['result']) + " !!!!")
			return True

		self._pi = update['player_index']
		self._rows = update['rows']
		self._cols = update['cols']

		#self._print_scores()

		return False

	def _print_scores(self):
		scores = sorted(update['scores'], key=lambda general: general['total'], reverse=True) # Sort Scores
		lands = sorted(update['lands'], reverse=True)
		armies = sorted(update['armies'], reverse=True)

		print(" -------- Scores --------")
		for score in scores:
			pos_lands = lands.index(score['tiles'])
			pos_armies = armies.index(score['total'])

			if (score['i'] == self._pi):
				print("SELF: ")
			print('Land: %d (%4d), Army: %d (%4d) / %d' % (pos_lands+1, score['tiles'], pos_armies+1, score['total'], len(scores)))

	def _start_moves(self):
		while (not self._update['complete']):
			# Expand Outward
			for x in _shuffle(range(self._cols)): # Check Each Square
				for y in _shuffle(range(self._rows)):
					source_tile = self._update['tile_grid'][y][x]
					source_army = self._update['army_grid'][y][x]
					if (source_tile == self._pi and source_army >= 2): # Find One With Armies
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
						for dy, dx in self._distribute_moves(x,y):
							if (self._validPosition(x+dx,y+dy)):
								dest_tile = self._update['tile_grid'][y+dy][x+dx]
								dest_army = self._update['army_grid'][y+dy][x+dx]
								if (source_army > (dest_army + DISTRIBUTE_GREATER)): # Position has less army count
									if (self._place_move(y, x, y+dy, x+dx, move_half=True)):
										break

			time.sleep(0.1)

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

	def _distribute_moves(self, x, y):
		king_y, king_x = self._update['generals'][self._pi]

		if y > king_y:
			if x > king_x: # dy=1, dx=1
				return [(1, 0), (0, 1), (-1, 0), (0, -1)]
			else: # dy=1, dx=-1
				return [(1, 0), (0, -1), (-1, 0), (0, 1)]
		else:
			if x > king_x: # dy=-1, dx=1
				return [(-1, 0), (0, 1), (1, 0), (0, -1)]
			else: # dy=-1, dx=-1
				return [(-1, 0), (0, -1), (1, 0), (0, 1)]


	def _place_move(self, y1, x1, y2, x2, move_half=False):
		if (self._validPosition(x2, y2)):
			self._game.move(y1, x1, y2, x2, move_half)
			return True
		return False

	def _validPosition(self, x, y):
		return 0 <= y < self._rows and 0 <= x < self._cols and self._update['tile_grid'][y][x] != generals.MOUNTAIN

def _create_thread(f):
	t = threading.Thread(target=f)
	#t.daemon = True
	t.start()

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)

# Start Bot
GeneralsBot()