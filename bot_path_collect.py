'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	January 2016
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Path Collect Both: Collects troops along a path, and attacks outward using path.
'''

import botBase

_bot = None
_map = None
_target = None
_path = []
_path_position = 0

######################### Move Making #########################

def make_move(currentBot, currentMap):
	global _bot, _map
	_bot = currentBot
	_map = currentMap

	if (_map.turn % 2 == 0):
		make_primary_move()
	else:
		if not move_outward():
			make_primary_move()
	return

######################### Primary Move Making #########################

def make_primary_move():
		update_primary_target()
		if (len(_path) > 0):
			move_primary_path_forward()

######################### Primary Targeting #########################

def update_primary_target():
	global _target, _path, _path_position
	if (_target != None):
		_target = _map.grid[_target.y][_target.x] # Update Target Tile State
	newTarget = _bot.find_primary_target(_target)
	if _target != newTarget:
		_target = newTarget
		oldPosition = None
		if (_path_position > 0 and len(_path) > 0): # Store old path position
			oldPosition = _path[_path_position]
		_path = _bot.find_path(dest=_target) # Find new path to target
		_bot._path = _path
		restart_primary_path(oldPosition) # Check if old path position part of new path
		print("New Path: " + str(_path))

######################### Move Forward Along Path #########################

def move_primary_path_forward():
	global _path_position
	try:
		source = _path[_path_position]
	except IndexError:
		logging.debug("Invalid Current Path Position")
		return restart_primary_path()

	if (source.tile != _map.player_index or source.army < 2): # Out of Army, Restart Path
		#logging.debug("Path Error: Out of Army (%d,%d)" % (source.tile, source.army))
		return restart_primary_path()

	try:
		dest = _path[_path_position+1] # Determine Destination
		if (dest.tile == _map.player_index or source.army > (dest.army+1)):
			_bot.place_move(source, dest)
		else:
			#logging.debug("Path Error: Out of Army To Attack (%d,%d,%d,%d)" % (dest.x,dest.y,source.army,dest.army))
			return restart_primary_path()
	except IndexError:
		#logging.debug("Path Error: Invalid Target Destination")
		return restart_primary_path()

	_path_position += 1
	return True

def restart_primary_path(old_tile=None):
	global _path_position
	_path_position = 0
	if (old_tile != None):
		for i, tile in enumerate(_path):
			if (tile.x, tile.y) == (old_tile.x, old_tile.y):
				_path_position = i
				return True
	
	return False

######################### Move Outward #########################

def move_outward():
	for x in botBase._shuffle(range(_map.cols)): # Check Each Square
		for y in botBase._shuffle(range(_map.rows)):
			source = _map.grid[y][x]

			if (source.tile == _map.player_index and source.army >= 2 and source not in _path): # Find One With Armies
				for dy, dx in _bot._toward_dest_moves(source):
					if (_bot.validPosition(x+dx,y+dy)):
						dest = _map.grid[y+dy][x+dx]
						if ((dest.tile != _map.player_index and source.army > (dest.army+1)) or dest in _path): # Capture Somewhere New
							_bot.place_move(source, dest)
							return True
	return False

######################### Collect To Path #########################

def move_collect_to_path():
	return True

######################### Main #########################

# Start Game
botBase.GeneralsBot(make_move, name="PurdueBot-Path", gameType="private")
#botBase.GeneralsBot(make_move, "PurdueBot-Path", "1v1")
#botBase.GeneralsBot(make_move, "PurdueBot-Path", "ffa")
