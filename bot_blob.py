'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_blob: Creates a blob of troops.
'''

import logging

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
	elif (_map.turn % 3 == 1):
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

			if (source.tile == _map.player_index and source.army >= 2): # Find One With Armies
				for dy, dx in _bot.toward_dest_moves(source):
					if (_bot.validPosition(x+dx,y+dy)):
						dest = _map.grid[y+dy][x+dx]
						if (dest.tile != _map.player_index and source.army > (dest.army+1)): # Capture Somewhere New
							_bot.place_move(source, dest)
							return True
	return False

def move_toward():
	source = _bot.find_largest_tile(includeGeneral=True)
	target = _bot.find_closest_target(source)

	path = _bot.find_path(source=source, dest=target)
	_bot._path = path
	if (len(path) >= 2):
		dest = path[1]
		if (dest.tile == _map.player_index or source.army > (dest.army+1)):
			_bot.place_move(source, dest)
			return True

	return False

######################### Main #########################

# Start Game
bot_base.GeneralsBot(make_move, name="PurdueBot-B", gameType="private")
#bot_base.GeneralsBot(make_move, name="PurdueBot-B", gameType="1v1")
#bot_base.GeneralsBot(make_move, name="PurdueBot-B", gameType="ffa")
