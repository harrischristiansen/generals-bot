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

class Generals(object):
	def __init__(self, userid, username, mode="1v1", gameid=None,
				 force_start=True):
		logging.debug("Creating connection")
		self._ws = create_connection(_ENDPOINT)
		self._lock = threading.RLock()
		self._gameid = gameid

		logging.debug("Starting heartbeat thread")
		_spawn(self._start_sending_heartbeat)

		logging.debug("Joining game")
		self._send(["star_and_rank", userid])
		if "[Bot]" not in username:
			username = "[Bot]"+username
		self._send(["set_username", userid, username])

		if mode == "private":
			if gameid is None:
				raise ValueError("Gameid must be provided for private games")
			self._send(["join_private", gameid, userid])
		elif mode == "1v1":
			self._send(["join_1v1", userid])
		elif mode == "team":
			self._send(["join_team", userid])
		elif mode == "ffa":
			self._send(["play", userid])
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
		# 42["chat_message", "game_148479560460049JgP8O3TPIwDNpgAEBB", "ship", null, ""]
		if not self._seen_update:
			raise ValueError("Cannot chat before game starts")

		if len(msg) < 2:
			return

		self._send(["chat_message", self._start_data['chat_room'], msg, None, ""])

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
				break
			elif msg[0] == "chat_message":
				chat_msg = msg[2]
				if "username" in chat_msg:
					logging.info("From %s: %s" % (chat_msg["username"],chat_msg["text"]))
				else:
					logging.info("Message: %s" % chat_msg["text"])
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

	def _send_forcestart(self):
		time.sleep(20)
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
