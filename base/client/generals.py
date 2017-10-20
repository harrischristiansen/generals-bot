'''
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Client Adopted from @toshima Generals Python Client - https://github.com/toshima/generalsio
'''

import logging
import json
import random
import threading
import time
from websocket import create_connection, WebSocketConnectionClosedException

from .constants import *
from . import generals_api
from . import map

class Generals(object):
	def __init__(self, userid, username, mode="1v1", gameid=None,
				 force_start=True, public_server=False):
		self._connect_and_join(userid, username, mode, gameid, force_start, public_server)

		self._seen_update = False
		self._move_id = 1
		self._start_data = {}
		self._stars = []
		self._cities = []

	def close(self):
		with self._lock:
			self._ws.close()

	######################### Get updates from server #########################

	def get_updates(self):
		while True:
			try:
				msg = self._ws.recv()
			except WebSocketConnectionClosedException:
				break

			if not msg.strip():
				break

			# ignore heartbeats and connection acks
			if msg in {"3", "40"}:
				continue

			# remove numeric prefix
			while msg and msg[0].isdigit():
				msg = msg[1:]

			msg = json.loads(msg)
			if not isinstance(msg, list):
				continue

			if msg[0] == "error_user_id":
				logging.info("Exit: User already in game queue")
				return
			elif msg[0] == "queue_update":
				self._log_queue_update(msg[1])
			elif msg[0] == "pre_game_start":
				logging.info("pre_game_start")
			elif msg[0] == "game_start":
				self._start_data = msg[1]
			elif msg[0] == "game_update":
				yield self._make_update(msg[1])
			elif msg[0] in ["game_won", "game_lost"]:
				yield self._make_result(msg[0], msg[1])
			elif msg[0] == "chat_message":
				self._handle_chat(msg[2])
			elif msg[0] == "error_set_username":
				None
			elif msg[0] == "game_over":
				None
			elif msg[0] == "notify":
				None
			else:
				logging.info("Unknown message type: {}".format(msg))

	######################### Make Moves #########################

	def move(self, y1, x1, y2, x2, move_half=False):
		if not self._seen_update:
			raise ValueError("Cannot move before first map seen")

		cols = self._map.cols
		a = y1 * cols + x1
		b = y2 * cols + x2
		self._send(["attack", a, b, move_half, self._move_id])
		self._move_id += 1

	######################### Send Chat Messages #########################

	def send_chat(self, msg):
		if self._handle_command(msg):
			return
		
		try:
			if self._seen_update:
				self._send(["chat_message", self._start_data['chat_room'], msg, None, ""])
			elif self._gameid != None:
				self._send(["chat_message", "chat_custom_queue_"+self._gameid, msg, None, ""])
		except WebSocketConnectionClosedException:
			pass

	######################### PRIVATE FUNCTIONS - PRIVATE FUNCTIONS #########################

	######################### Bot Commands #########################

	def _handle_command(self, msg, from_chat=False, username=""):
		msg_lower = msg.lower()
		if len(msg) < 12 and any(keyword in msg_lower for keyword in START_KEYWORDS):
			self._send_forcestart(delay=0)
			return True
		if len(msg) < 2:
			return True

		command = msg.split(' ')
		if len(command) == 1:
			command = command[0].split(':') # Handle : delimiters
		base_command = command[0].lower()

		if "help" in base_command:
			self._print_command_help(from_chat)
			return True
		if "setup" in base_command:
			self._set_game_speed(4)
			self._set_game_map()
			self._set_game_public()
			return True
		elif "speed" in base_command and len(command) >= 2 and command[1][0].isdigit():
			self._set_game_speed(command[1][0])
			return True
		elif "team" in base_command:
			if len(command) >= 2 and len(command[1]) == 1:
				self._set_game_team(command[1])
			else:
				return self._add_teammate(username)
			return True
		elif "public" in base_command:
			self._set_game_public()
			return True
		elif "surrender" in base_command:
			self._map.exit_on_game_over = False
			self._send(["surrender"])
			return True
		elif "map" in base_command:
			if len(command) >= 2:
				self._set_game_map(" ".join(command[1:]))
			else:
				self._set_game_map()
			return True
		elif from_chat and len(msg) < 12 and "map" in msg_lower:
			self._set_game_map()
			return True

		return False

	def _print_command_help(self, from_chat=False):
		if from_chat:
			for txt in GAME_HELP_TEXT if "_map" in dir(self) else PRE_HELP_TEXT:
				self.send_chat(txt)
				time.sleep(0.34)
		else:
			print("\n".join(GAME_HELP_TEXT if "_map" in dir(self) else PRE_HELP_TEXT))

	######################### Custom Config #########################

	def _add_teammate(self, username):
		if "_map" in dir(self) and "usernames" in dir(self._map):
			if username != "" and username != self._map.usernames[self._map.player_index]:
				self._map.do_not_attack_players.append(self._map.usernames.index(username))
				return True
		return False

	######################### Server -> Client #########################

	def _log_queue_update(self, msg):
		teams = {}
		if "teams" in msg:
			for i in range(len(msg['teams'])):
				if msg['teams'][i] not in teams:
					teams[msg['teams'][i]] = []
				teams[msg['teams'][i]].append(msg['usernames'][i])
		
		if 'map_title' in msg:
			mapname = msg['map_title']
			if mapname and len(mapname) > 1:
				logging.info("Queue [%s] %d/%d %s" % (mapname, msg['numForce'], msg['numPlayers'], teams))
				return
		
		logging.info("Queue %d/%d %s" % (msg['numForce'], msg['numPlayers'], teams))

	def _make_update(self, data):
		if not self._seen_update:
			self._seen_update = True
			self._map = map.Map(self._start_data, data)
			logging.info("Joined Game: %s - %s" % (self._map.replay_url, self._map.usernames))
			return self._map

		return self._map.update(data)

	def _make_result(self, update, data):
		return self._map.updateResult(update)

	def _handle_chat(self, chat_msg):
		if "username" in chat_msg:
			self._handle_command(chat_msg["text"], from_chat=True, username=chat_msg["username"])
			logging.info("From %s: %s" % (chat_msg["username"], chat_msg["text"]))
		else:
			logging.info("Message: %s" % chat_msg["text"])

	######################### Client -> Server #########################

	def _connect_and_join(self, userid, username, mode, gameid, force_start, public_server):
		logging.debug("Creating connection")
		self._ws = create_connection(ENDPOINT_BOT if not public_server else ENDPOINT_PUBLIC)
		self._lock = threading.RLock()
		_spawn(self._start_sending_heartbeat)
		self._send(["set_username", userid, username, BOT_KEY])

		logging.info("Joining game")
		self._gameid = None
		if mode == "private":
			self._gameid = gameid
			if gameid is None:
				raise ValueError("Gameid must be provided for private games")
			self._send(["join_private", gameid, userid, BOT_KEY])
		elif mode == "1v1":
			self._send(["join_1v1", userid, BOT_KEY])
		elif mode == "team":
			self._send(["join_team", userid, BOT_KEY])
		elif mode == "ffa":
			self._send(["play", userid, BOT_KEY])
		else:
			raise ValueError("Invalid mode")

		if (force_start):
			_spawn(self._send_forcestart)

	def _start_sending_heartbeat(self):
		while True:
			try:
				with self._lock:
					self._ws.send("2")
			except WebSocketConnectionClosedException:
				break
			time.sleep(0.1)

	def _send_forcestart(self, delay=20):
		time.sleep(delay)
		self._send(["set_force_start", self._gameid, True])
		logging.info("Sent force start")

	def _set_game_speed(self, speed="1"):
		speed = int(speed)
		if speed in [1, 2, 3, 4]:
			self._send(["set_custom_options", self._gameid, {"game_speed":speed}])

	def _set_game_team(self, team="1"):
		team = int(team)
		if team in range(1, MAX_NUM_TEAMS+1):
			self._send(["set_custom_team", self._gameid, team])

	def _set_game_public(self):
		self._send(["make_custom_public", self._gameid])

	def _set_game_map(self, mapname=""):
		if len(mapname) > 1:
			maplower = mapname.lower()
			if maplower in ["win", "good"]:
				self._send(["set_custom_options", self._gameid, {"map":random.choice(GENERALS_MAPS)}])
			elif maplower == "top":
				self._send(["set_custom_options", self._gameid, {"map":random.choice(generals_api.list_top())}])
			elif maplower == "hot":
				self._send(["set_custom_options", self._gameid, {"map":random.choice(generals_api.list_hot())}])
			else:
				self._send(["set_custom_options", self._gameid, {"map":mapname}])
		else:
			self._send(["set_custom_options", self._gameid, {"map":random.choice(generals_api.list_top())}])

	def _send(self, msg):
		try:
			with self._lock:
				self._ws.send("42" + json.dumps(msg))
		except WebSocketConnectionClosedException:
			pass


def _spawn(f):
	t = threading.Thread(target=f)
	t.daemon = True
	t.start()
