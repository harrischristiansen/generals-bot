'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals.io Bot Commands
'''

import random
import threading
import time

from .constants import *
from . import generals_api

class BotCommands(object):
	def __init__(self, bot):
		self._bot = bot
		self._permitted_username = ""

	def setMap(self, gamemap):
		self._map = gamemap

	######################### Bot Commands #########################

	def handle_command(self, msg, from_chat=False, username=""):
		msg_lower = msg.lower()
		if len(msg) < 12 and any(k in msg_lower for k in START_KEYWORDS):
			self._bot.send_forcestart(delay=0)
			return True
		if len(msg) < 2:
			return True

		command = msg.split(' ')
		if len(command) == 1:
			command = command[0].split(':') # Handle : delimiters
		base_command = command[0].lower()
		arg_command = " ".join(command[1:])

		if self._handlePlayerCommand(msg, username):
			return True

		if base_command.startswith(tuple(HELP_KEYWORDS)):
			self._print_command_help(from_chat)
			return True
		if base_command.startswith(tuple(HELLO_KEYWORDS)):
			self._print_command_hello()
			return True
		if "setup" in base_command:
			self._bot.set_game_speed(4)
			self._set_game_map()
			self._bot.set_game_public()
			return True
		elif "speed" in base_command and len(command) >= 2 and command[1][0].isdigit():
			self._bot.set_game_speed(command[1][0])
			return True
		elif "public" in base_command:
			self._bot.set_game_public()
			return True
		else: # OPTIONALLY-RESTRICTED Commands
			if self._permitted_username != "" and self._permitted_username != username: # Only allow permitted user
				return False

			if "take" in base_command and username != "":
				self._permitted_username = username
			elif "team" in base_command:
				if len(command) >= 2:
					if len(command[1]) == 1:
						self._bot.set_game_team(command[1])
					else:
						return self._add_teammate(arg_command)
				elif base_command in ["unteamall"]:
					self._remove_all_teammates()
				elif base_command in ["unteam", "cancelteam"]:
					self._remove_teammate(username)
				elif base_command in ["noteam"]:
					_spawn(self._start_avoiding_team)
				else:
					return self._add_teammate(username)
				return True
			elif "surrender!" in base_command:
				if "_map" in dir(self):
					#self._map.exit_on_game_over = False # Wait 2 minutes before exiting
					self._bot.send_surrender()
				return True
			elif "map" in base_command:
				if len(command) >= 2:
					self._set_game_map(arg_command)
				else:
					self._set_game_map()
				return True
			elif "normal" in base_command:
				self._set_normal_map()
				return True
			elif "swamp" in base_command:
				if len(command) == 2:
					try:
						self._set_swamp_map(float(arg_command))
						return True
					except ValueError:
						None
				self._set_swamp_map()
				return True
			elif from_chat and len(msg) < 12 and "map" in msg_lower:
				self._set_game_map()
				return True

		return False

	def _print_command_help(self, from_chat=False):
		if from_chat:
			self._bot.sent_hello = True
			for txt in GAME_HELP_TEXT if "_map" in dir(self) else PRE_HELP_TEXT:
				self._bot.send_chat(txt)
				time.sleep(0.34)
		else:
			print("\n".join(GAME_HELP_TEXT if "_map" in dir(self) else PRE_HELP_TEXT))

	def _print_command_hello(self):
		if "sent_hello" in dir(self._bot):
			return True
		self._bot.sent_hello = True

		for txt in HELLO_TEXT:
			self._bot.send_chat(txt)
			time.sleep(0.34)

	######################### Teammates #########################

	def _add_teammate(self, username):
		if "_map" in dir(self) and "usernames" in dir(self._map):
			if username != "" and username != self._map.usernames[self._map.player_index] and username in self._map.usernames:
				self._map.do_not_attack_players.append(self._map.usernames.index(username))
				return True
		return False

	def _remove_teammate(self, username):
		if "_map" in dir(self) and "usernames" in dir(self._map):
			if username != "" and username != self._map.usernames[self._map.player_index]:
				if self._map.usernames.index(username) in self._map.do_not_attack_players:
					self._map.do_not_attack_players.remove(self._map.usernames.index(username))
					return True
		return False

	def _remove_all_teammates(self):
		self._map.do_not_attack_players = []
		return True

	def _start_avoiding_team(self):
		while True:
			if not "teams" in dir(self._bot):
				time.sleep(0.1)
				continue
			for i, members in self._bot.teams.items():
				if self._bot.username in members:
					if len(members) > 1: # More than 1 person on bots team
						for team in range(1, MAX_NUM_TEAMS+1):
							if not team in self._bot.teams:
								self._bot.set_game_team(team)
								break

			time.sleep(0.1)

	######################### Set Custom Gamemap #########################

	def _set_game_map(self, mapname=""):
		if len(mapname) > 1:
			maplower = mapname.lower()
			if maplower in ["win", "good"]:
				self._bot.set_game_map(random.choice(GENERALS_MAPS))
			elif maplower == "top":
				self._bot.set_game_map(random.choice(generals_api.list_top()))
			elif maplower == "hot":
				self._bot.set_game_map(random.choice(generals_api.list_hot()))
			else:
				maps = generals_api.list_search(mapname)
				if mapname in maps:
					self._bot.set_game_map(mapname)
				elif len(maps) >= 1:
					self._bot.set_game_map(maps[0])
					self._bot.send_chat("I could not find "+mapname+", so I set the map to "+maps[0]+" (Note: names are case sensitive)")
				else:
					self._bot.send_chat("Could not find map named "+mapname+" (Note: names are case sensitive)")
		else:
			self._bot.set_game_map(random.choice(generals_api.list_both()))

	def _set_normal_map(self):
		width = round(random.uniform(0, 1), 2)
		height = round(random.uniform(0, 1), 2)
		city = round(random.uniform(0, 1), 2)
		mountain = round(random.uniform(0, 1), 2)
		self._bot.set_normal_map(width, height, city, mountain)

	def _set_swamp_map(self, swamp=-1):
		if swamp == -1:
			swamp = round(random.uniform(0, 1), 2)
		if swamp >= 0 and swamp <= 1:
			self._bot.set_normal_map(swamp=swamp)

	######################### Player Requested Commands #########################

	def _handlePlayerCommand(self, msg, username):
		if username == "Plots85":
			self._bot.send_chat("HI PLOTS85, I LOVE YOU!")
			return True

		if "eetin" in username:
			if "yeet" in msg:
				self._bot.send_chat("YEETINATOR IS THE BEST! ALL HAIL YEETINATOR! /bowdown")
				return True

		return False

def _spawn(f):
	t = threading.Thread(target=f)
	t.daemon = True
	t.start()
