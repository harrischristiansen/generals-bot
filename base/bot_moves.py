'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals Bot: Common Move Logic
'''

from base import bot_base

######################### Move Outward #########################

def move_outward(map, path=[]):
	for source in map.tiles[map.player_index]: # Check Each Owned Tile
		if source.army >= 2 and source not in path: # Find One With Armies
			for neighbor in bot_base._shuffle(source.neighbors()):
				if ((neighbor.tile != map.player_index and source.army > neighbor.army + 1) or neighbor in path) and not neighbor.isSwamp: # Capture Somewhere New
					return (source, neighbor)
	return (False, False)