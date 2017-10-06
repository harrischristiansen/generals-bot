'''
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Client Adopted from @toshima Generals Python Client - https://github.com/toshima/generalsio
'''

import logging
import json
import threading
import time
from websocket import create_connection, WebSocketConnectionClosedException

from . import map

_ENDPOINT = "ws://botws.generals.io/socket.io/?EIO=3&transport=websocket"
_ENDPOINT_PUBLIC = "ws://ws.generals.io/socket.io/?EIO=3&transport=websocket"
_BOT_KEY = "O13f0dijsf"

_START_KEYWORDS = ["start", "go", "force"]

class Generals(object):
	def __init__(self, userid, username, mode="1v1", gameid=None,
				 force_start=True, public_server=False):
		logging.debug("Creating connection")
		self._ws = create_connection(_ENDPOINT if not public_server else _ENDPOINT_PUBLIC)
		self._lock = threading.RLock()
		_spawn(self._start_sending_heartbeat)
		self._send(["set_username", userid, username, _BOT_KEY])
		self._gameid = None

		logging.debug("Joining game")
		if mode == "private":
			self._gameid = gameid # Set Game ID
			if gameid is None:
				raise ValueError("Gameid must be provided for private games")
			self._send(["join_private", gameid, userid, _BOT_KEY])
		elif mode == "1v1":
			self._send(["join_1v1", userid, _BOT_KEY])
		elif mode == "team":
			self._send(["join_team", userid, _BOT_KEY])
		elif mode == "ffa":
			self._send(["play", userid, _BOT_KEY])
		else:
			raise ValueError("Invalid mode")

		if (force_start):
			_spawn(self._send_forcestart)

		self._seen_update = False
		self._move_id = 1
		self._start_data = {}
		self._stars = []
		self._map = []
		self._cities = []

	def send_chat(self, msg):
		if any(keyword in msg for keyword in _START_KEYWORDS):
			self._send_forcestart(delay=0)
			return

		if len(msg) < 2:
			return

		if self._seen_update:
			self._send(["chat_message", self._start_data['chat_room'], msg, None, ""])
		elif self._gameid != None:
			self._send(["chat_message", "chat_custom_queue_"+self._gameid, msg, None, ""])

	def move(self, y1, x1, y2, x2, move_half=False):
		if not self._seen_update:
			raise ValueError("Cannot move before first map seen")

		cols = self._map.cols
		a = y1 * cols + x1
		b = y2 * cols + x2
		self._send(["attack", a, b, move_half, self._move_id])
		self._move_id += 1

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
				raise ValueError("Already in game")
			elif msg[0] == "game_start":
				logging.info("Game info: {}".format(msg[1]))
				self._start_data = msg[1]
			elif msg[0] == "game_update":
				yield self._make_update(msg[1])
			elif msg[0] in ["game_won", "game_lost"]:
				yield self._make_result(msg[0], msg[1])
			elif msg[0] == "chat_message":
				self._handle_chat(msg[2])
			elif msg[0] == "error_set_username":
				None
			else:
				logging.info("Unknown message type: {}".format(msg))

	def close(self):
		self._ws.close()

	def _make_update(self, data):
		if not self._seen_update:
			self._seen_update = True
			self._map = map.Map(self._start_data, data)
			return self._map

		return self._map.update(data)

	def _make_result(self, update, data):
		return self._map.updateResult(update)

	def _handle_chat(self, chat_msg):
		if any(keyword in chat_msg["text"] for keyword in _START_KEYWORDS): # Force Start Requests
			self._send_forcestart(delay=0)
		if "username" in chat_msg:
			logging.info("From %s: %s" % (chat_msg["username"], chat_msg["text"]))
		else:
			logging.info("Message: %s" % chat_msg["text"])

	def _send_forcestart(self, delay=20):
		time.sleep(delay)
		self._send(["set_force_start", self._gameid, True])
		logging.info("Sent force_start")

	def _start_sending_heartbeat(self):
		while True:
			try:
				with self._lock:
					self._ws.send("2")
			except WebSocketConnectionClosedException:
				break
			time.sleep(0.1)

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
