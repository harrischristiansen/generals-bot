'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Common Move Logic
'''
import random

from base import bot_base

######################### Move Outward #########################

def move_outward(gamemap, path=[]):
	for source in gamemap.tiles[gamemap.player_index]: # Check Each Owned Tile
		if source.army >= 2 and source not in path: # Find One With Armies
			for neighbor in bot_base._shuffle(source.neighbors()):
				if ((neighbor.tile != gamemap.player_index and source.army > neighbor.army + 1) or neighbor in path) and not neighbor.isSwamp: # Capture Somewhere New
					return (source, neighbor)
	return (False, False)

######################### Move Path Forward #########################

def move_path(path):
	if len(path) < 2:
		return (None, None)

	# Find largest tile in path to move forward
	largest = path[0]
	largest_index = 0
	for i, tile in enumerate(path):
		if tile == path[-1]:
			break
		if tile.tile == path[0].tile and tile > largest:
			largest = tile
			largest_index = i

	dest = path[largest_index+1]
	return (largest, dest)

######################### Move Path Forward #########################

def should_move_half(gamemap, source):
	moveHalf = False
	if gamemap.turn > 150:
		if source in gamemap.generals:
			moveHalf = True
		elif source in gamemap.cities:
			moveHalf = random.choice([False, False, False, True])
			if gamemap.turn - source.turn_captured < 16:
				moveHalf = True
	return moveHalf

######################### Proximity Targeting - Pathfinding #########################

def path_proximity_target(gamemap):
	# Find path from largest tile to closest target
	source = gamemap.find_largest_tile(includeGeneral=True)
	target = source.nearest_target_tile()
	path = source.path_to(target)

	if not gamemap.canCompletePath(path):
		path = path_gather(gamemap, elsoDo=path)
	return path

def path_gather(gamemap, elsoDo=[]):
	source = gamemap.find_city(includeGeneral=True)
	target = gamemap.find_largest_tile(notInPath=[source])
	if source and target and source != target:
		return source.path_to(target)
	return elsoDo