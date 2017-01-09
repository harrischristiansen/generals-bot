'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_path_collect: Collects troops along a path, and attacks outward using path.
'''

import logging
import random
import threading
import time

import client.generals as generals
from viewer import GeneralsViewer

# Opponent Type Definitions
OPP_EMPTY = 0
OPP_ARMY = 1
OPP_CITY = 2
OPP_GENERAL = 3

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
		self._game = generals.Generals('PurdueBot', 'PurdueBot', 'private', gameid='HyI4d3_rl') # Private Game - http://generals.io/games/HyI4d3_rl
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
		received_first_update = False

		for update in self._game.get_updates():
			self._set_update(update)

			if (not received_first_update):
				self._received_first_update()
				received_first_update = True

			if (not self._running):
				return

			self._make_move()
			#self._print_scores()

			# Update GeneralsViewer Grid
			if '_viewer' in dir(self):
				self._viewer.updateGrid(self._update)

	def _received_first_update(self):
		self._clear_target()
		return

	def _set_update(self, update):
		if (update['complete']):
			print("!!!! Game Complete. Result = " + str(update['result']) + " !!!!")
			self._running = False
			return

		self._update = update
		self._pi = update['player_index']
		self._rows = update['rows']
		self._cols = update['cols']

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

	######################### Move Generation #########################

	def _make_move(self):
		if self._find_target():
			print("New Target: "+str(self._target_position))
			self._restart_path()
			self._find_path()
		self._move_path_forward()
		return

	######################### Find Primary Target For Path #########################

	def _find_target(self):
		newTarget = False

		if (self._target_position != None and self._update['tile_grid'][self._target_position[0]][self._target_position[1]] == self._pi): # Aquired Target
			self._clear_target()

		min_city_size = self._update['armies'][self._pi] / 2

		for x in _shuffle(range(self._cols)): # Check Each Square
			for y in _shuffle(range(self._rows)):
				source_pos = (y,x)
				source_tile = self._update['tile_grid'][y][x]
				source_army = self._update['army_grid'][y][x]

				if (self._target_type <= OPP_GENERAL): # Search for Generals
					if (source_tile >= 0 and source_tile != self._pi and source_pos in self._update['generals']):
						self._target_position = source_pos
						self._target_type = OPP_GENERAL
						self._target_army = source_army
						return True

				if (self._target_type <= OPP_CITY): # Search for Smallest Cities
					if (source_tile != self._pi and source_army < min_city_size and source_pos in self._update['cities']):
						if (self._target_type < OPP_CITY or self._target_army > source_army):
							self._target_position = source_pos
							self._target_type = OPP_CITY
							self._target_army = source_army
							newTarget = True

				if (self._target_type <= OPP_ARMY): # Search for Largest Opponent Armies
					if (source_tile >= 0 and source_tile != self._pi and source_army > self._target_army):
						self._target_position = source_pos
						self._target_type = OPP_ARMY
						self._target_army = source_army
						newTarget = True

				if (self._target_type < OPP_EMPTY): # Search for Empty Squares
					if (source_tile == generals.EMPTY):
						self._target_position = source_pos
						self._target_type = OPP_EMPTY
						self._target_army = source_army
						return True

		return newTarget

	def _clear_target(self):
		self._target_position = None
		self._target_army = 0
		self._target_type = OPP_EMPTY - 1

	######################### Find Path To Primary Target #########################

	def _find_path(self):
		king_y, king_x = self._update['generals'][self._pi]

		self._path = []
		self._path_length = 1
		for y in range(self._rows):
			self._path.append([])
			for x in range(self._cols):
				self._path[y].append(0)

		self._find_path_step(king_x, king_y)
		return

	def _find_path_step(self, x, y):
		# Record Path Step
		if (self._path[y][x] > 0):
			self._path[y][x] = -self._path[y][x]
			self._path_length += -1
		else:
			self._path[y][x] = self._path_length
			self._path_length += 1

		# End Condition
		if (self._target_position == (y,x)):
			return

		# Find Next Move
		try:
			x2, y2 = self._path_move(x,y)
			self._find_path_step(x2, y2)
		except TypeError:
			print("!!!!! ERROR: No Next Path Move!!!!!")

	def _path_move(self, x, y):
		bestTarget = None
		bestTarget_type = OPP_EMPTY - 1

		for dy, dx in self._toward_dest_moves(x,y):
			if (self._validPosition(x+dx,y+dy)):
				dest_tile = self._update['tile_grid'][y+dy][x+dx]
				dest_army = self._update['army_grid'][y+dy][x+dx]
				if (self._path[y+dy][x+dx] == 0): # Never Visited
					if ((y+dy,x+dx) in self._update['generals']): # Target General
						bestTarget = (x+dx,y+dy)
						bestTarget_type = OPP_GENERAL
					elif (bestTarget_type < OPP_CITY and (y+dy,x+dx) in self._update['cities']): # Target Cities
						bestTarget = (x+dx,y+dy)
						bestTarget_type = OPP_CITY
					elif (bestTarget_type < OPP_ARMY and dest_tile >= 0 and dest_tile != self._pi): # Target Opponents
						bestTarget = (x+dx,y+dy)
						bestTarget_type = OPP_ARMY
					elif (bestTarget_type < OPP_EMPTY): # Target Empties
						bestTarget = (x+dx,y+dy)
						bestTarget_type = OPP_EMPTY
				elif (self._path[y+dy][x+dx] > 0): # Backtracing
					if (bestTarget_type < OPP_EMPTY):
						bestTarget = (x+dx,y+dy)

		return bestTarget

	######################### Move Forward Along Path #########################

	def _move_path_forward(self):
		try:
			x,y = self._path_coordinates(self._path_position)
		except TypeError:
			print("Invalid Current Path Position")
			return self._restart_path()

		source_tile = self._update['tile_grid'][y][x]
		source_army = self._update['army_grid'][y][x]

		if (source_tile != self._pi or source_army < 2): # Out of Army, Restart Path
			print("Path Error: Out of Army (%d,%d,%d)" % (self._path_position, source_tile, source_army))
			return self._restart_path()

		print("Path Move (%d)" % (self._path_position))
		try:
			x2,y2 = self._path_coordinates(self._path_position+1) # Determine Destination
			dest_tile = self._update['tile_grid'][y2][x2]
			dest_army = self._update['army_grid'][y2][x2] + 1
			if (dest_tile == self._pi or source_army > dest_army):
				self._place_move(y, x, y2, x2)
			else:
				print("Path Error: Out of Army To Attack")
				return self._restart_path()
		except TypeError:
			print("Path Error: Invalid Target Destination")
			return self._restart_path()



		self._path_position = self._path_position + 1
		return True

	def _path_coordinates(self, i):
		for y in range(self._rows):
			for x in range(self._cols):
				if (self._path[y][x] == i):
					return (x,y)
		return None

	def _restart_path(self): # Always returns False
		self._path_position = 1
		return False

	######################### Move Outward #########################

	def _move_outward(self):
		return True

	######################### Collect To Path #########################

	def _move_collect_to_path(self):
		return True
	

	######################### Movement Helpers #########################


	def _toward_dest_moves(self, source_x, source_y, dest_x=-1, dest_y=-1):
		# Determine Destination
		if (dest_x == -1):
			dest_x = self._target_position[1]
			dest_y = self._target_position[0]

		# Compute X/y Directions
		dir_y = 1
		if source_y > dest_y:
			dir_y = -1

		dir_x = 1
		if source_x > dest_x:
			dir_x = -1

		# Return List of Moves
		moves = random.sample([(0, dir_x), (dir_y, 0)],2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)],2))
		return moves

	def _away_king_moves(self, x, y):
		king_y, king_x = self._update['generals'][self._pi]

		if (y == king_y and x == king_x): # Moving from king
			return self._moves_random()

		dir_y = 1
		if y < king_y:
			dir_y = -1

		dir_x = 1
		if x < king_x:
			dir_x = -1

		moves = random.sample([(0, dir_x), (dir_y, 0)],2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)],2))
		return moves

	def _moves_random(self):
		return random.sample([(1, 0), (-1, 0), (0, 1), (0, -1)], 4)

	def _place_move(self, y1, x1, y2, x2, move_half=False):
		if (self._validPosition(x2, y2)):
			self._game.move(y1, x1, y2, x2, move_half)
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