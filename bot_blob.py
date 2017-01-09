'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_blob: Creates a blob of troops.
'''

import logging
import random
import threading
import time

import client.generals as generals
from viewer import GeneralsViewer

# Show all logging
logging.basicConfig(level=logging.DEBUG)

class GeneralsBot(object):
	def __init__(self):
		# Start Game Loop
		_create_thread(self._start_game_loop)

		# Start Game Viewer
		self._viewer = GeneralsViewer()
		self._viewer.mainViewerLoop()

	def _start_game_loop(self):
		# Create Game
		self._game = generals.Generals('PurdueBot-Blob', 'PurdueBot-Blob', 'private', gameid='HyI4d3_rl') # Private Game - http://generals.io/games/HyI4d3_rl
		#self._game = generals.Generals('PurdueBot', 'PurdueBot', '1v1') # 1v1
		#self._game = generals.Generals('PurdueBot', 'PurdueBot', 'ffa') # FFA

		# Start Game Update Loop
		self._running = True
		_create_thread(self._start_update_loop)

		while (self._running):
			msg = input('Send Msg:')
			print("Sending MSG: " + msg)
			# TODO: Send msg

	######################### Handle Updates From Server #########################

	def _start_update_loop(self):
		firstUpdate = True

		for update in self._game.get_updates():
			self._set_update(update)

			if (not self._running):
				return

			#self._print_scores()

			if (firstUpdate):
				_create_thread(self._start_moves)
				firstUpdate = False

			# Update GeneralsViewer Grid
			if '_viewer' in dir(self):
				self._viewer.updateGrid(self._update)

	def _set_update(self, update):
		if (update['complete']):
			print("!!!! Game Complete. Result = " + str(update['result']) + " !!!!")
			return

		self._update = update
		self._pi = update['player_index']
		self._opponent_position = None
		self._rows = update['rows']
		self._cols = update['cols']

		self._record_opponent_position()

	def _print_scores(self):
		scores = sorted(self._update['scores'], key=lambda general: general['total'], reverse=True) # Sort Scores
		lands = sorted(self._update['lands'], reverse=True)
		armies = sorted(self._update['armies'], reverse=True)

		print(" -------- Scores --------")
		for score in scores:
			pos_lands = lands.index(score['tiles'])
			pos_armies = armies.index(score['total'])

			if (score['i'] == self._pi):
				print("SELF: ")
			print('Land: %d (%4d), Army: %d (%4d) / %d' % (pos_lands+1, score['tiles'], pos_armies+1, score['total'], len(scores)))

	######################### Thread: Make Moves #########################

	def _start_moves(self):
		while (self._running and not self._update['complete']):
			self._expand_edges()
			self._run_chains_distribution()
			self._dumb_distribute()

	######################### Record Opponent Position #########################

	def _record_opponent_position(self):
		largestArmy = 0

		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_tile = self._update['tile_grid'][y][x]
				source_army = self._update['army_grid'][y][x]
				if (source_tile >= 0 and source_tile != self._pi and source_army > largestArmy): # Find Opponent with largest armies
					self._opponent_position = (x,y)
					largestArmy = source_army
					

	######################### Expand Edges #########################

	def _expand_edges(self):
		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_tile = self._update['tile_grid'][y][x]
				source_army = self._update['army_grid'][y][x]
				if (source_tile == self._pi and source_army >= 2): # Find One With Armies
					for dy, dx in self._explore_moves(x,y):
						if (self._validPosition(x+dx,y+dy)):
							dest_tile = self._update['tile_grid'][y+dy][x+dx]
							dest_army = self._update['army_grid'][y+dy][x+dx] + 1
							if (dest_tile != self._pi and source_army > dest_army): # Capture Somewhere New
								self._place_move(y, x, y+dy, x+dx)

	######################### Dumb Distribute #########################

	def _dumb_distribute(self):
		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_tile = self._update['tile_grid'][y][x]
				source_army = self._update['army_grid'][y][x]
				if (source_tile == self._pi and source_army > 6): # Find One With Armies
					for dy, dx in self._explore_moves(x,y):
						if (self._validPosition(x+dx,y+dy)):
							dest_tile = self._update['tile_grid'][y+dy][x+dx]
							dest_army = self._update['army_grid'][y+dy][x+dx]
							if (source_army > (dest_army * 2)): # Position has less army count
								if (self._place_move(y, x, y+dy, x+dx, move_half=True)):
									return


	######################### Run Chains Distribution #########################

	def _run_chains_distribution(self):
		distribution_path = []

		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_tile = self._update['tile_grid'][y][x]
				source_army = self._update['army_grid'][y][x]
				if (source_tile == self._pi and source_army > 12): # Find One With Armies
					distribution_path = self._distribute_square(distribution_path, x, y)

	def _distribute_square(self, path, x, y):
		if (not self._validPosition(x,y)):
			return path

		source_tile = self._update['tile_grid'][y][x]
		source_army = self._update['army_grid'][y][x]

		if (source_army < 2 or source_tile != self._pi):
			return path

		if (path == None):
			path = []

		if ((x,y) in path):
			return path
		path.append((x,y))

		for dy, dx in self._explore_moves(x,y):
			if (self._validPosition(x+dx,y+dy)):
				dest_tile = self._update['tile_grid'][y+dy][x+dx]
				dest_army = self._update['army_grid'][y+dy][x+dx] + 1
				if (dest_tile != self._pi and source_army > dest_army): # Capture Somewhere New
					self._place_move(y, x, y+dy, x+dx)
					return self._distribute_square(path, x+dx, y+dy)

				if (source_army > dest_army): # Position has less army count
					if ((x+dx,y+dy) not in path): # Not Traveled Before
						self._place_move(y, x, y+dy, x+dx)
						return self._distribute_square(path, x+dx, y+dy)

		return path

	######################### Movement Controllers #########################
	
	def _explore_moves(self, x, y):
		positions = self._toward_target_moves(x,y)
		first_positions = []
		smallest_opponent = 9999

		for dy, dx in positions:
			if (self._validPosition(x+dx,y+dy)):
				dest_tile = self._update['tile_grid'][y+dy][x+dx]
				dest_army = self._update['army_grid'][y+dy][x+dx]

				if (dest_tile >= 0 and dest_tile != self._pi): # Other Players
					if (dest_army < smallest_opponent):
						smallest_opponent = dest_army
						first_positions.insert(0,(dy,dx)) # Sort from smallest to largest army
					else:
						first_positions.append((dy,dx))
					positions.remove((dy,dx))

				elif (dest_tile != self._pi and ((y,x) in self._update['cities'] or (y,x) in self._update['generals'])): # Other Cities
					first_positions.insert(0,(dy,dx))
					positions.remove((dy,dx))


		first_positions.extend(positions)
		return first_positions

	def _toward_target_moves(self, origin_x, origin_y):
		closest_target = None
		closest_target_distance = 1000

		current_army = self._update['army_grid'][origin_y][origin_x]

		for x in range(self._cols): # Check Each Square, Find Closest Optimal Target
			for y in range(self._rows):
				dest_tile = self._update['tile_grid'][y][x]
				dest_army = self._update['army_grid'][y][x]
				if (dest_tile >= 0 and dest_tile != self._pi): # Other Player
					distance = abs(x-origin_x) + abs(y-origin_y)
					if (distance < closest_target_distance):
						closest_target = (x,y)
						closest_target_distance = distance

				if (dest_tile != self._pi and ((y,x) in self._update['cities'] or (y,x) in self._update['generals']) and current_army > (.75 * dest_army)): # Other Cities
					distance = abs(x-origin_x) + abs(y-origin_y)
					if (distance < (closest_target_distance * 1.5)):
						closest_target = (x,y)
						closest_target_distance = distance * 0.7


		if (closest_target == None):
			return self._away_king_moves(x,y)

		self._opponent_position = closest_target
		return self._toward_opponent_moves(origin_x,origin_y)


	def _toward_opponent_moves(self, x, y):
		opp_x, opp_y = self._opponent_position

		if y > opp_y:
			if x > opp_x: # dy=-1, dx=-1
				moves = random.sample([(-1, 0), (0, -1)],2)
				moves.extend(random.sample([(1, 0), (0, 1)],2))
				return moves
			else: # dy=-1, dx=1
				moves = random.sample([(0, 1), (-1, 0)],2)
				moves.extend(random.sample([(1, 0), (0, -1)],2))
				return moves
		else:
			if x > opp_x: # dy=1, dx=-1
				moves = random.sample([(1, 0), (0, -1)],2)
				moves.extend(random.sample([(-1, 0), (0, 1)],2))
				return moves
			else: # dy=1, dx=1
				moves = random.sample([(0, 1), (1, 0)],2)
				moves.extend(random.sample([(-1, 0), (0, -1)],2))
				return moves

	def _away_king_moves(self, x, y):
		king_y, king_x = self._update['generals'][self._pi]

		if (y == king_y and x == king_x): # Moving from king
			return self._moves_random()

		if y > king_y:
			if x > king_x: # dy=1, dx=1
				moves = random.sample([(1, 0), (0, 1)],2)
				moves.extend(random.sample([(-1, 0), (0, -1)],2))
				return moves
			else: # dy=1, dx=-1
				moves = random.sample([(0, -1), (1, 0)],2)
				moves.extend(random.sample([(-1, 0), (0, 1)],2))
				return moves
		else:
			if x > king_x: # dy=-1, dx=1
				moves = random.sample([(-1, 0), (0, 1)],2)
				moves.extend(random.sample([(1, 0), (0, -1)],2))
				return moves
			else: # dy=-1, dx=-1
				moves = random.sample([(0, -1), (-1, 0)],2)
				moves.extend(random.sample([(1, 0), (0, 1)],2))
				return moves


	def _moves_random(self):
		return random.sample([(1, 0), (-1, 0), (0, 1), (0, -1)], 4)

	def _place_move(self, y1, x1, y2, x2, move_half=False):
		if (self._validPosition(x2, y2)):
			self._game.move(y1, x1, y2, x2, move_half)

			# Calculate Remaining Army
			army_remaining = 1
			if move_half:
				army_remaining = self._update['army_grid'][y1][x1] / 2

			# Update Current Board
			if (self._update['tile_grid'][y2][x2] == self._pi): # Owned By Self
				self._update['army_grid'][y2][x2] = self._update['army_grid'][y1][x1] + self._update['army_grid'][y2][x2] - army_remaining
			else:
				self._update['army_grid'][y2][x2] = self._update['army_grid'][y1][x1] - self._update['army_grid'][y2][x2] - army_remaining
			self._update['tile_grid'][y2][x2] = self._pi
			self._update['army_grid'][y1][x1] = army_remaining

			time.sleep(0.45) # Wait for next move
			return True
		return False

	def _validPosition(self, x, y):
		return 0 <= y < self._rows and 0 <= x < self._cols and self._update['tile_grid'][y][x] != generals.MOUNTAIN

######################### Global Helpers #########################

def _create_thread(f):
	t = threading.Thread(target=f)
	t.daemon = True
	t.start()

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)

######################### Main #########################

# Start Bot
GeneralsBot()