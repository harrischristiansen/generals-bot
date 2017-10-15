'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Common Move Logic
'''
import random

from base import bot_base

######################### Move Outward #########################

def move_outward(map, path=[]):
	for source in map.tiles[map.player_index]: # Check Each Owned Tile
		if source.army >= 2 and source not in path: # Find One With Armies
			for neighbor in bot_base._shuffle(source.neighbors()):
				if ((neighbor.tile != map.player_index and source.army > neighbor.army + 1) or neighbor in path) and not neighbor.isSwamp: # Capture Somewhere New
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

def should_move_half(map, source):
	moveHalf = False
	if map.turn > 150:
		if source in map.generals:
			moveHalf = True
		elif source in map.cities:
			moveHalf = random.choice([False, False, False, True])
			if map.turn - source.turn_captured < 16:
				moveHalf = True
	return moveHalf

######################### Proximity Targeting - Pathfinding #########################

def path_proximity_target(bot, map):
	# Find path from largest tile to closest target
	source = bot.find_largest_tile(includeGeneral=True)
	target = bot.find_closest_target(source)
	path = source.path_to(target)

	army_total = 0
	for tile in path: # Verify can obtain every tile in path
		if tile.tile == map.player_index:
			army_total += tile.army - 1
		elif tile.army + 1 > army_total: # Cannot obtain tile, draw path from largest city to largest tile
			source = bot.find_city(includeGeneral=True)
			target = bot.find_largest_tile(notInPath=[source])
			if source and target and source != target:
				path = source.path_to(target)
			break

	return path