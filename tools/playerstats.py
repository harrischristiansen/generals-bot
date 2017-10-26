'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals.io Player Replay Statistics
'''

import requests
import lzstring

NUM_REPLAYS_TO_USE = 400

URL_REPLAYS_FOR_USER = "http://generals.io/api/replaysForUsername?u="
URL_REPLAY = "https://generalsio-replays-na.s3.amazonaws.com/"
COUNT_BY = 200

######################### Public Methods #########################

def mapstats(playername):
	replays = _get_list_replays(playername, NUM_REPLAYS_TO_USE)

	maps = {}
	for replay in replays:
		if replay['type'] == "custom":
			mapName = _get_map_name(replay['id'])

def opponentstats(playername, mingames=0):
	replays = _get_list_replays(playername, NUM_REPLAYS_TO_USE)

	opponents = {}
	for replay in replays:
		if replay['type'] == "custom":
			didBeatPlayer = True
			for opponent in replay['ranking']:
				name = opponent['name']
				if not _is_valid_name(name):
					continue
				if name != playername:
					if name not in opponents:
						opponents[name] = {"games":1, "wins":(1 if didBeatPlayer else 0)}
					else:
						opponents[name]['games'] += 1
						if didBeatPlayer:
							opponents[name]['wins'] += 1
				else:
					didBeatPlayer = False

	opponents_selected = {}
	for (name, opponent) in opponents.items():
		opponents[name]['winPercent'] = opponent['wins'] / opponent['games']
		if opponent['games'] > mingames:
			opponents_selected[name] = opponents[name]

	opponents_sorted = sorted(opponents_selected.items(), key=lambda x:x[1]['winPercent'], reverse=True)
	return opponents_sorted


######################### Private Methods #########################

def _get_list_replays(playername, count):
	replays = []
	for offset in range(0, count, COUNT_BY):
		data = _get_json_url(URL_REPLAYS_FOR_USER+playername+"&offset="+str(offset)+"&count="+str(COUNT_BY))
		if len(data) > 0:
			replays.extend(data)
	return replays

def _get_map_name(replay_id):
	data = _get_url(URL_REPLAY+replay_id+".gior")
	lz = lzstring.LZString()
	#return bytes(data.text, "utf-8")
	return lz.decompress(data.content)
	return list(data.text)

def _get_json_url(url):
	return _get_url(url).json()

def _get_url(url):
	return requests.get(url)

def _is_valid_name(name):
	return all(ord(c) < 128 for c in name)

#print(_get_map_name("HY43dQdab"))
print(opponentstats("myssix", 10))
