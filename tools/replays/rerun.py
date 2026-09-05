'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Replay Rerun: Feed a real game back through our bot's own Map, one turn at a time,
	so we can ask "what did the bot see, and what would it do?" at any point in a real game.

	The bot only ever sees a fog-of-war view built the same way the server builds it,
	so its decisions here match what it actually faced.
'''

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from base.client.map import Map
from tools.replays import simulate

TILE_FOG = -3
TILE_MOUNTAIN = -2


class BotView(object):
	'''Maintains our bot's Map for one player across a replayed game.'''

	def __init__(self, replay, player):
		self.replay = replay
		self.player = player
		self.width = replay.mapWidth
		self.height = replay.mapHeight
		self.known_cities = []
		self._known_city_set = set()
		self.known_mountains = set()
		self.known_generals = {player: replay.generals[player]}
		self.gamemap = None

	def _visible(self, game):
		visible = set()
		for i, owner in enumerate(game.tiles):
			if owner != self.player:
				continue
			r, c = i // self.width, i % self.width
			for dr in (-1, 0, 1):
				for dc in (-1, 0, 1):
					nr, nc = r + dr, c + dc
					if 0 <= nr < self.height and 0 <= nc < self.width:
						visible.add(nr * self.width + nc)
		return visible

	def _observe(self, game, visible):
		for i in visible:
			if i in self._known_city_set:
				continue
			if i in game.cities:
				self._known_city_set.add(i)
				self.known_cities.append(i)
		for i in visible:
			if game.tiles[i] == TILE_MOUNTAIN:
				self.known_mountains.add(i)
		for p, index in enumerate(game.generals):
			if p not in self.known_generals and index != simulate.DEAD_GENERAL and index in visible:
				self.known_generals[p] = index

	def _diff(self, values):
		return [0, len(values)] + list(values) + [0]

	def sync(self, game): # Update our bot's Map from the true game state, through fog
		visible = self._visible(game)
		self._observe(game, visible)

		size = self.width * self.height
		army_flat = [0] * size
		type_flat = [0] * size
		for i in range(size):
			if i in visible:
				army_flat[i] = game.armies[i]
				type_flat[i] = game.tiles[i]
			elif i in self.known_mountains:
				type_flat[i] = TILE_MOUNTAIN
			else:
				type_flat[i] = TILE_FOG

		scores = game.scores()
		data = {
			'turn': game.turn,
			'map_diff': self._diff([self.width, self.height] + army_flat + type_flat),
			'cities_diff': self._diff(self.known_cities),
			'generals': [self.known_generals.get(p, -1) for p in range(game.num_players)],
			'scores': [{'i': p, 'total': scores[p]['army'], 'tiles': scores[p]['land'],
						'dead': not game.alive[p]} for p in range(game.num_players)],
		}

		if self.gamemap is None:
			start_data = {'playerIndex': self.player, 'usernames': self.replay.usernames,
							'replay_id': self.replay.id, 'swamps': []}
			self.gamemap = Map(start_data, data)
		else:
			self.gamemap.update(data)

		return self.gamemap


class StubBot(object):
	def __init__(self, gameType="1v1"):
		self._gameType = gameType
		self.pending_move = None

	def place_move(self, source, dest, move_half=False):
		self.pending_move = (source, dest, bool(move_half))


def rerun(replay, player, on_turn=None, until_turn=None, move_method=None):
	'''Replay the game, syncing our bot's view each turn. on_turn(game, gamemap, stub) is
	called after the bot has decided its move for that turn.'''
	game = simulate.SimulatedGame(replay)
	view = BotView(replay, player)
	stub = StubBot()

	last_turn = until_turn if until_turn is not None else (
		max(m.turn for m in replay.moves) + 1 if replay.moves else 0)

	while game.turn <= last_turn and game.alive[player]:
		gamemap = view.sync(game)
		stub.pending_move = None
		if move_method:
			move_method(stub, gamemap)
		if on_turn:
			on_turn(game, gamemap, stub)
		game.step()

	return game
