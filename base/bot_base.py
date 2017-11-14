'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Base Bot Class
'''

import logging
import os
from queue import Queue
import random
import threading
import time

from .client import generals
from .client.constants import *
from .viewer import GeneralsViewer

class GeneralsBot(object):
	def __init__(self, moveMethod, moveEvent=None, name="PurdueBot", gameType="private", privateRoomID=None, showGameViewer=True, public_server=False, start_msg_cmd=""):
		# Save Config
		self._moveMethod = moveMethod
		self._name = name
		self._gameType = gameType
		self._privateRoomID = privateRoomID
		self._public_server = public_server
		self._start_msg_cmd = start_msg_cmd

		# ----- Start Game -----
		self._running = True
		self._move_event = threading.Event()
		_create_thread(self._start_game_thread)
		_create_thread(self._start_chat_thread)
		_create_thread(self._start_moves_thread)

		# Start Game Viewer
		if showGameViewer:
			window_title = "%s (%s)" % (self._name, self._gameType)
			if self._privateRoomID != None:
				window_title = "%s (%s - %s)" % (self._name, self._gameType, self._privateRoomID)
			self._viewer = GeneralsViewer(window_title, moveEvent=moveEvent)
			self._viewer.mainViewerLoop() # Consumes Main Thread
			self._exit_game()

		while self._running:
			time.sleep(10)

		self._exit_game()

	######################### Handle Updates From Server #########################

	def _start_game_thread(self):
		# Create Game
		self._game = generals.Generals(self._name, self._name, self._gameType, gameid=self._privateRoomID, public_server=self._public_server)
		_create_thread(self._send_start_msg_cmd)

		# Start Receiving Updates
		for gamemap in self._game.get_updates():
			self._set_update(gamemap)

			if not gamemap.complete:
				self._move_event.set() # Permit another move

		self._exit_game()

	def _set_update(self, gamemap):
		self._map = gamemap
		selfDir = dir(self)

		# Update GeneralsViewer Grid
		if '_viewer' in selfDir:
			if '_path' in selfDir:
				self._map.path = self._path
			if '_collect_path' in selfDir:
				self._map.collect_path = self._collect_path
			if '_moves_realized' in selfDir:
				self._map.bottomText = "Realized: "+str(self._moves_realized)
			viewer = self._viewer.updateGrid(gamemap)

		# Handle Game Complete
		if gamemap.complete and not self._has_completed:
			logging.info("!!!! Game Complete. Result = " + str(gamemap.result) + " !!!!")
			if '_moves_realized' in selfDir:
				logging.info("Moves: %d, Realized: %d" % (self._map.turn, self._moves_realized))
			_create_thread(self._exit_game)
		self._has_completed = gamemap.complete

	def _exit_game(self):
		time.sleep(1.1)
		if not self._map.exit_on_game_over:
			time.sleep(100)
		self._running = False
		os._exit(0) # End Program

	######################### Move Generation #########################

	def _start_moves_thread(self):
		self._moves_realized = 0
		while self._running:
			self._move_event.wait()
			self._move_event.clear()
			self._make_move()
			self._moves_realized+=1

	def _make_move(self):
		self._moveMethod(self, self._map)

	######################### Chat Messages #########################

	def _start_chat_thread(self):
		# Send Chat Messages
		while self._running:
			msg = str(input('Send Msg:'))
			self._game.send_chat(msg)
			time.sleep(0.7)
		return

	def _send_start_msg_cmd(self):
		time.sleep(0.2)
		for cmd in self._start_msg_cmd.split("\\n"):
			self._game.handle_command(cmd)

	######################### Tile Finding #########################

	def find_primary_target(self, target=None):
		target_type = OPP_EMPTY - 1
		if target != None and target.shouldNotAttack(): # Acquired Target
			target = None
		if target != None: # Determine Previous Target Type
			target_type = OPP_EMPTY
			if target.isGeneral:
				target_type = OPP_GENERAL
			elif target.isCity:
				target_type = OPP_CITY
			elif target.army > 0:
				target_type = OPP_ARMY

		# Determine Max Target Size
		largest = self._map.find_largest_tile(includeGeneral=True)
		max_target_size = largest.army * 1.25

		for x in _shuffle(range(self._map.cols)): # Check Each Tile
			for y in _shuffle(range(self._map.rows)):
				source = self._map.grid[y][x]
				if not source.isValidTarget() or source.tile == self._map.player_index: # Don't target invalid tiles
					continue

				if target_type <= OPP_GENERAL: # Search for Generals
					if source.tile >= 0 and source.isGeneral and source.army < max_target_size:
						return source

				if target_type <= OPP_CITY: # Search for Smallest Cities
					if source.isCity and source.army < max_target_size:
						if target_type < OPP_CITY or source.army < target.army:
							target = source
							target_type = OPP_CITY

				if target_type <= OPP_ARMY: # Search for Largest Opponent Armies
					if source.tile >= 0 and (target == None or source.army > target.army) and not source.isCity:
						target = source
						target_type = OPP_ARMY

				if target_type < OPP_EMPTY: # Search for Empty Squares
					if source.tile == TILE_EMPTY and source.army < largest.army:
						target = source
						target_type = OPP_EMPTY

		return target
	
	######################### Movement Helpers #########################

	def toward_dest_moves(self, source, dest=None):
		# Determine Destination
		if dest == None:
			dest = self.find_primary_target()
			if dest == None:
				return self.away_king_moves(source)

		# Compute X/Y Directions
		dir_y = 1
		if source.y > dest.y:
			dir_y = -1

		dir_x = 1
		if source.x > dest.x:
			dir_x = -1

		# Return List of Moves
		moves = random.sample([(0, dir_x), (dir_y, 0)], 2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)], 2))
		return moves

	def away_king_moves(self, source):
		general = self._map.generals[self._map.player_index]

		if source == general: # Moving from General
			return self.moves_random()

		dir_y = 1
		if source.y < general.y:
			dir_y = -1

		dir_x = 1
		if source.x < general.x:
			dir_x = -1

		moves = random.sample([(0, dir_x), (dir_y, 0)],2)
		moves.extend(random.sample([(0, -dir_x), (-dir_y, 0)],2))
		return moves

	def moves_random(self):
		return random.sample(DIRECTIONS, 4)

	def place_move(self, source, dest, move_half=False):
		if self._map.isValidPosition(dest.x, dest.y):
			self._game.move(source.y, source.x, dest.y, dest.x, move_half)
			if SHOULD_DIRTY_MAP_ON_MOVE:
				self._update_map_dirty(source, dest, move_half)
			return True
		return False

	def _update_map_dirty(self, source, dest, move_half):
		army = source.army if not move_half else source.army/2
		source.update(self._map, source.tile, 1)

		if dest.isOnTeam(): # Moved Internal Tile
			dest_army = army - 1 + dest.army
			dest.update(self._map, source.tile, dest_army)
			return True
		
		elif army > dest.army+1: # Captured Tile
			dest_army = army - 1 - dest.army
			dest.update(self._map, source.tile, dest_army, isCity=dest.isGeneral)
			return True
		return False

######################### Global Helpers #########################

def _create_thread(f):
	t = threading.Thread(target=f)
	t.daemon = True
	t.start()

def _shuffle(seq):
	shuffled = list(seq)
	random.shuffle(shuffled)
	return iter(shuffled)
