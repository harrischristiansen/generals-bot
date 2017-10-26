'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Generals.io Web API Requests
'''

import requests

######################### Public Methods #########################

_list_top = None
def list_top():
	global _list_top
	if (_list_top == None):
		_list_top = _get_list_maps("http://generals.io/api/maps/lists/top")
	return _list_top

_list_hot = None
def list_hot():
	global _list_hot
	if (_list_hot == None):
		_list_hot = _get_list_maps("http://generals.io/api/maps/lists/hot")
	return _list_hot

def list_both():
	maps = list_top()
	maps.extend(list_hot())
	return maps

def list_search(query):
		return _get_list_maps("http://generals.io/api/maps/search?q="+query)

######################### Private Methods #########################

def _get_list_maps(url):
	data = _get_url(url)
	maps = []
	for custommap in data:
		if _is_valid_name(custommap['title']):
			maps.append(custommap['title'])
	return maps

def _get_url(url):
	return requests.get(url).json()

def _is_valid_name(name):
	return all(ord(c) < 128 for c in name)
