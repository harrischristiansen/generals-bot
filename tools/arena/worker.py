'''
	Runs inside its own subprocess, with sys.path pointed at one git worktree checkout
	of the bot repo, so it imports that checkout's OWN copy of base.client.map / bot_moves
	/ the chosen move-method script - unmodified, exactly as that commit's code behaves.

	This is what makes comparing two different commits safe: each subprocess only ever
	sees one version's modules, so there is no import-namespace collision between commits
	that may define the Map/Tile classes differently.

	Protocol (line-delimited JSON over stdin/stdout, mirroring the real generals.io
	server<->client wire format):
	  <- {"start_data": {...}, "data": {...}}   (first message)
	  <- {"data": {...}}                        (every message after)
	  -> {"move": [source_row, source_col, dest_row, dest_col, move_half]} or {"move": null}
	  <- {"stop": true}                         (ends the worker)
'''

import importlib
import io
import json
import os
import sys

os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1') # Keep pygame's import banner off the JSON stdout protocol


class StubBot(object):
	def __init__(self):
		self._gameType = "private"
		self.pending_move = None

	def place_move(self, source, dest, move_half=False):
		self.pending_move = (source.y, source.x, dest.y, dest.x, bool(move_half))


def main():
	worktree_dir = sys.argv[1]
	bot_script = sys.argv[2]

	sys.path.insert(0, worktree_dir)

	real_stdout = sys.stdout
	sys.stdout = io.StringIO() # Some imports (e.g. pygame) print a banner; keep it off the JSON protocol stream
	try:
		map_mod = importlib.import_module('base.client.map')
		bot_mod = importlib.import_module(bot_script)
	finally:
		sys.stdout = real_stdout

	gamemap = None
	stub = StubBot()

	for line in sys.stdin:
		line = line.strip()
		if not line:
			continue
		msg = json.loads(line)
		if msg.get('stop'):
			break

		stub.pending_move = None
		if gamemap is None:
			gamemap = map_mod.Map(msg['start_data'], msg['data'])
		else:
			gamemap.update(msg['data'])

		bot_mod.make_move(stub, gamemap)

		sys.stdout.write(json.dumps({'move': list(stub.pending_move) if stub.pending_move else None}) + "\n")
		sys.stdout.flush()


if __name__ == '__main__':
	main()
