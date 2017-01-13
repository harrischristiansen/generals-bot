'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot_blob: Creates a blob of troops.
'''

import bot_base

_bot = None
_map = None

######################### Move Making #########################

def make_move(currentBot, currentMap):
	global _bot, _map
	_bot = currentBot
	_map = currentMap

	if (_map.turn % 3 == 0):
		move_outward()
	elif (_map.turn % 3 == 1):
		None
	else:
		None
	return

######################### Move Outward #########################

def move_outward():
	for x in bot_base._shuffle(range(_map.cols)): # Check Each Square
		for y in bot_base._shuffle(range(_map.rows)):
			source = _map.grid[y][x]

			if (source.tile == _map.player_index and source.army >= 2 and source not in _path): # Find One With Armies
				for dy, dx in _bot._toward_dest_moves(source):
					if (_bot.validPosition(x+dx,y+dy)):
						dest = _map.grid[y+dy][x+dx]
						if (dest.tile != _map.player_index and source.army > (dest.army+1)): # Capture Somewhere New
							_bot.place_move(source, dest)
							return True
	return False

######################### Main #########################

# Start Game
#bot_base.GeneralsBot(make_move, name="PurdueBot-Path", gameType="private")
bot_base.GeneralsBot(make_move, name="PurdueBot-Path", gameType="1v1")
#bot_base.GeneralsBot(make_move, name="PurdueBot-Path", gameType="ffa")
