'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals.io Web Socket Communication
'''

import certifi
import logging
import json
import ssl
import threading
import time
import requests
from websocket import create_connection, WebSocketConnectionClosedException

from .constants import *
from . import bot_cmds
from . import map

class Generals(object):
	def __init__(self, userid, username, mode="1v1", gameid=None, public_server=False, start_command=""):
		self._should_forcestart = mode == "private" or mode == "team"
		self.userid = userid
		self.username = username
		self.gamemode = mode
		self.roomid = gameid
		self.public_server = public_server
		self._start_msg_cmd = start_command
		self.isPaused = False
		self._seen_update = False
		self._move_id = 1
		self._start_data = {}
		self._stars = []
		self._cities = []
		self._messagesToSave = []
		self._numberPlayers = 0

		self._connect_and_join(userid, username, mode, gameid, self._should_forcestart)
		_spawn(self._send_start_msg_cmd)

	def close(self):
		with self._lock:
			self._ws.close()

	######################### Get updates from server #########################

	def get_updates(self):
		while True:
			try:
				msg = self._ws.recv()
			except WebSocketConnectionClosedException:
				logging.info("Connection Closed")
				break
			
			# logging.info("Received message type: {}".format(msg))

			if not msg.strip():
				continue

			# ignore heartbeats and connection acks
			if msg in {"2", "3", "40"}:
				continue

			# remove numeric prefix
			while msg and msg[0].isdigit():
				msg = msg[1:]

			if msg == "probe":
				continue

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
				self._messagesToSave.append(msg)
				self._start_data = msg[1]
			elif msg[0] == "game_update":
				#self._messagesToSave.append(msg)
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

		if self.isPaused:
			return False

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
		if 'queueTimeLeft' in msg:
			logging.info("Queue (%ds) %s/%s" % (msg['queueTimeLeft'], str(len(msg['numForce'])), str(msg['numPlayers'])))
			return

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
		
		logging.info("Queue %s/%s %s" % (str(len(msg['numForce'])), str(msg['numPlayers']), self.teams))

		numberPlayers = msg['numPlayers']
		if self._numberPlayers != numberPlayers:
			self._numberPlayers = numberPlayers
			if self._should_forcestart:
				_spawn(self.send_forcestart)

		if "usernames" in msg:
			for username in BANNED_PLAYERS:
				for userInMatch in msg['usernames']:
					if userInMatch != None:
						if userInMatch.lower().find(username.lower()) != -1:
							logging.info("Found banned player: %s" % username)
							self.changeToNewRoom()

	def _make_update(self, data):
		if not self._seen_update:
			self._seen_update = True
			self._map = map.Map(self._start_data, data)
			self._bot_cmds().setMap(self._map)
			logging.info("Joined Game: %s - %s" % (self._map.replay_url, self._map.usernames))
			return self._map

		return self._map.update(data)

	def _make_result(self, update, data):
		self._saveMessagesToDisk()
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

	def _endpointWS(self):
		return "wss" + (ENDPOINT_BOT if not self.public_server else ENDPOINT_PUBLIC) + "&transport=websocket"

	def _endpointRequests(self):
		return "https" + (ENDPOINT_BOT if not self.public_server else ENDPOINT_PUBLIC) + "&transport=polling"

	def _getSID(self):
		request = requests.get(self._endpointRequests() + "&t=ObyKmaZ")
		result = request.text
		while result and result[0].isdigit():
			result = result[1:]

		msg = json.loads(result)
		sid = msg["sid"]
		self._gio_sessionID = sid
		_spawn(self._verifySID)
		return sid

	def _verifySID(self):
		sid = self._gio_sessionID
		checkOne = requests.post(self._endpointRequests() + "&t=ObyKmbC&sid=" + sid, data="40")
		# checkTwo = requests.get(self._endpointRequests() + "&t=ObyKmbC.0&sid=" + sid)
		# logging.debug("Check two: %s" % checkTwo.text)

	def _connect_and_join(self, userid, username, mode, gameid, force_start):
		endpoint = self._endpointWS() + "&sid=" + self._getSID()
		logging.debug("Creating connection with endpoint %s: %s" % (endpoint, certifi.where()))
		# ssl_context = ssl.create_default_context(cafile=certifi.where())
		ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLSv1_2)
		ssl_context.load_verify_locations(certifi.where())
		# ctx.load_cert_chain(certfile=certifi.where())
		# self._ws = create_connection(endpoint, ssl=ssl_context)
		self._ws = create_connection(endpoint, sslopt={"cert_reqs": ssl.CERT_NONE})
		self._lock = threading.RLock()
		self._ws.send("2probe")
		self._ws.send("5")
		_spawn(self._start_sending_heartbeat)
		# logging.debug("Setting Username: %s" % username)
		# self._send(["set_username", userid, username, BOT_KEY])

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

	def _start_sending_heartbeat(self):
		while True:
			try:
				with self._lock:
					self._ws.send("3")
			except WebSocketConnectionClosedException:
				logging.info("Connection Closed - heartbeat")
				break
			time.sleep(19)

	def send_forcestart(self, delay=10):
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

	def _send(self, msg, prefix="42"):
		try:
			with self._lock:
				self._ws.send(prefix + json.dumps(msg))
		except WebSocketConnectionClosedException:
			pass

	######################### Game Replay #########################

	def _saveMessagesToDisk(self):
		fileName = "game_" + self._map.replay_url + ".txt"
		fileName = fileName.replace("/", ".")
		fileName = fileName.replace(":", "")

		with open("games/"+fileName, 'w+') as file:
			file.write(str(self._messagesToSave))

	######################### Change Rooms #########################


	def _send_start_msg_cmd(self):
		time.sleep(0.2)
		for cmd in self._start_msg_cmd.split("\\n"):
			self.handle_command(cmd)

	def changeToNewRoom(self):
		self.close()
		self.roomid = self.roomid + "x"
		self._connect_and_join(self.userid, self.username, self.gamemode, self.roomid, self._should_forcestart)
		_spawn(self._send_start_msg_cmd)



def _spawn(f):
	t = threading.Thread(target=f)
	t.daemon = True
	t.start()
