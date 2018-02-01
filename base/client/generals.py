'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals.io Web Socket Communication
'''

import logging
import json
import threading
import time
from websocket import create_connection, WebSocketConnectionClosedException

from .constants import *
from . import bot_cmds
from . import map

class Generals(object):
	def __init__(self, userid, username, mode="1v1", gameid=None,
				 force_start=True, public_server=False):
		self._connect_and_join(userid, username, mode, gameid, force_start, public_server)

		self.username = username
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
		if self.handle_command(msg):
			return
		
		try:
			if self._seen_update:
				self._send(["chat_message", self._start_data['chat_room'], msg, None, ""])
			elif self._gameid != None:
				self._send(["chat_message", "chat_custom_queue_"+self._gameid, msg, None, ""])
		except WebSocketConnectionClosedException:
			pass

	######################### PRIVATE FUNCTIONS - PRIVATE FUNCTIONS #########################

	######################### Server -> Client #########################

	def _log_queue_update(self, msg):
		self.teams = {}
		if "teams" in msg:
			for i in range(len(msg['teams'])):
				if msg['teams'][i] not in self.teams:
					self.teams[msg['teams'][i]] = []
				self.teams[msg['teams'][i]].append(msg['usernames'][i])
		
		if 'map_title' in msg:
			mapname = msg['map_title']
			if mapname and len(mapname) > 1:
				logging.info("Queue [%s] %d/%d %s" % (mapname, msg['numForce'], msg['numPlayers'], self.teams))
				return
		
		logging.info("Queue %d/%d %s" % (msg['numForce'], msg['numPlayers'], self.teams))

	def _make_update(self, data):
		if not self._seen_update:
			self._seen_update = True
			self._map = map.Map(self._start_data, data)
			self._bot_cmds().setMap(self._map)
			logging.info("Joined Game: %s - %s" % (self._map.replay_url, self._map.usernames))
			return self._map

		return self._map.update(data)

	def _make_result(self, update, data):
		return self._map.updateResult(update)

	def _handle_chat(self, chat_msg):
		if "username" in chat_msg:
			self.handle_command(chat_msg["text"], from_chat=True, username=chat_msg["username"])
			logging.info("From %s: %s" % (chat_msg["username"], chat_msg["text"]))
		else:
			logging.info("Message: %s" % chat_msg["text"])

	def handle_command(self, msg, from_chat=False, username=""):
		return self._bot_cmds().handle_command(msg, from_chat, username)
	def _bot_cmds(self):
		if not "_commands" in dir(self):
			self._commands = bot_cmds.BotCommands(self)
		return self._commands

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

		if force_start:
			_spawn(self.send_forcestart)

	def _start_sending_heartbeat(self):
		while True:
			try:
				with self._lock:
					self._ws.send("2")
			except WebSocketConnectionClosedException:
				break
			time.sleep(0.1)

	def send_forcestart(self, delay=20):
		time.sleep(delay)
		self._send(["set_force_start", self._gameid, True])
		logging.info("Sent force start")

	def set_game_speed(self, speed="1"):
		speed = int(speed)
		if speed in [1, 2, 3, 4]:
			self._send(["set_custom_options", self._gameid, {"game_speed":speed}])

	def set_game_team(self, team="1"):
		team = int(team)
		if team in range(1, MAX_NUM_TEAMS+1):
			self._send(["set_custom_team", self._gameid, team])

	def set_game_public(self):
		self._send(["make_custom_public", self._gameid])

	def set_game_map(self, mapname=""):
		if len(mapname) > 1:
			self._send(["set_custom_options", self._gameid, {"map":mapname}])

	def set_normal_map(self, width=-1, height=-1, city=-1, mountain=-1, swamp=-1):
		self._send(["set_custom_options", self._gameid, {"map":None}])
		if width >= 0 and width <=1:
			self._send(["set_custom_options", self._gameid, {"width":width}])
		if height >= 0 and height <=1:
			self._send(["set_custom_options", self._gameid, {"height":height}])
		if city >= 0 and city <=1:
			self._send(["set_custom_options", self._gameid, {"city_density":city}])
		if mountain >= 0 and mountain <=1:
			self._send(["set_custom_options", self._gameid, {"mountain_density":mountain}])
		if swamp >= 0 and swamp <=1:
			self._send(["set_custom_options", self._gameid, {"swamp_density":swamp}])

	def send_surrender(self):
		self._send(["surrender"])

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
