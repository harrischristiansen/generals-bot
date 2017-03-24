'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_blob: Creates a blob of troops.
'''

import logging
import sys

from base import bot_base

# Show all logging
logging.basicConfig(level=logging.DEBUG)

######################### Move Making #########################

_bot = None
_map = None
def make_move(currentBot, currentMap):
	global _bot, _map
	_bot = currentBot
	_map = currentMap

	if (_map.turn % 3 == 0):
		if not move_outward():
			make_primary_move()
	else:
		make_primary_move()
	return

def make_primary_move():
	if not move_toward():
		move_outward()

######################### Move Outward #########################

def move_outward():
	for x in bot_base._shuffle(range(_map.cols)): # Check Each Square
		for y in bot_base._shuffle(range(_map.rows)):
			source = _map.grid[y][x]

			if (source.tile == _map.player_index and source.army >= 2 and source not in _path): # Find One With Armies
				for dy, dx in _bot.toward_dest_moves(source):
					if (_bot.validPosition(x+dx,y+dy)):
						dest = _map.grid[y+dy][x+dx]
						if (dest.tile != _map.player_index and source.army > (dest.army+1)) or (dest in  _path): # Capture Somewhere New
							_bot.place_move(source, dest)
							return True
	return False

_path = []
def move_toward():
	# Find path from largest tile to closest target
	source = _bot.find_largest_tile(includeGeneral=True)
	target = _bot.find_closest_target(source)
	path = _bot.find_path(source=source, dest=target)

	army_total = 0
	for tile in path: # Verify can obtain every tile in path
		if (tile.tile == _map.player_index):
			army_total += (tile.army - 1)
		elif (tile.army+1 > army_total): # Cannot obtain tile, draw path from largest city to largest tile
			source = _bot.find_city(includeGeneral=True)
			target = _bot.find_largest_tile()
			if (source and target and source != target):
				path = _bot.find_path(source=source, dest=target)
			break

	# Place Move
	_path = path
	_bot._path = path
	(move_from, move_to) = _bot.path_forward_moves(path)
	if (move_from != None):
		_bot.place_move(move_from, move_to)
		return True

	return False

######################### Main #########################

# Start Game
if len(sys.argv) > 1: # Game Type Argument: "1v1" or "ffa"
	bot_base.GeneralsBot(make_move, name="PurdueBot-B", gameType=sys.argv[1])
else:
	bot_base.GeneralsBot(make_move, name="PurdueBot-B", gameType="private", privateRoomID="PurdueBot") # Private Game - http://generals.io/games/HyI4d3_rl
	#bot_base.GeneralsBot(make_move, name="PurdueBot-B", gameType="1v1")
	#bot_base.GeneralsBot(make_move, name="PurdueBot-B", gameType="ffa")
