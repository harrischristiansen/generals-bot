'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Replay Parser: Read generals.io .gior replay files

	.gior files are a JSON array compressed with lz-string's compressToUint8Array.
	Field order follows the official utils (github.com/vzhou842/generals.io-Replay-Utils);
	newer replay versions append extra fields (deserts, swamps, lookouts, ...) which are
	kept in .extra and are empty for standard games.
'''

import json
import os

import lzstring
import requests

REPLAY_URLS = {
	'na': "https://generalsio-replays-na.s3.amazonaws.com/%s.gior",
	'eu': "https://generalsio-replays-eu.s3.amazonaws.com/%s.gior",
	'bot': "https://generalsio-replays-bot.s3.amazonaws.com/%s.gior",
}

FIELDS = ["version", "id", "mapWidth", "mapHeight", "usernames", "stars", "cities",
			"cityArmies", "generals", "mountains", "moves", "afks", "teams", "map_title"]


class Move(object):
	def __init__(self, serialized):
		self.index = serialized[0]		# Player index
		self.start = serialized[1]		# Source tile index
		self.end = serialized[2]		# Destination tile index
		self.is50 = serialized[3]		# Move half
		self.turn = serialized[4]		# Turn the move was made

	def __repr__(self):
		return "Move(p%d, %d->%d, turn %d%s)" % (self.index, self.start, self.end, self.turn, ", half" if self.is50 else "")


class Replay(object):
	def __init__(self, obj):
		for i, name in enumerate(FIELDS):
			setattr(self, name, obj[i] if i < len(obj) else None)

		self.extra = obj[len(FIELDS):]
		self.moves = [Move(m) for m in (self.moves or [])]
		self.afks = [{'index': a[0], 'turn': a[1]} for a in (self.afks or [])]

	def size(self):
		return self.mapWidth * self.mapHeight

	def coords(self, index): # Tile index -> (row, col)
		return (index // self.mapWidth, index % self.mapWidth)

	def player_of(self, username):
		if username in self.usernames:
			return self.usernames.index(username)
		return None

	def __repr__(self):
		return "Replay(%s, %dx%d, %s, %d moves)" % (
			self.id, self.mapWidth, self.mapHeight, self.usernames, len(self.moves))


def decode(data): # Raw .gior bytes -> Replay
	chars = ''.join(chr((data[i*2] << 8) | data[i*2+1]) for i in range(len(data)//2))
	decompressed = lzstring.LZString().decompress(chars)
	if not decompressed:
		raise ValueError("Could not decompress replay (not a valid .gior file?)")

	return Replay(json.loads(decompressed))


def load(path):
	with open(path, 'rb') as f:
		return decode(f.read())


def fetch(replay_id, region='na', cache_dir=None): # Download a replay by id, caching to disk
	if cache_dir:
		cached = os.path.join(cache_dir, "%s.gior" % replay_id)
		if os.path.exists(cached):
			return load(cached)

	response = requests.get(REPLAY_URLS[region] % replay_id, timeout=30)
	response.raise_for_status()

	if cache_dir:
		if not os.path.isdir(cache_dir):
			os.makedirs(cache_dir)
		with open(os.path.join(cache_dir, "%s.gior" % replay_id), 'wb') as f:
			f.write(response.content)

	return decode(response.content)
