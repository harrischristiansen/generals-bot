'''
	Arena: plays two git refs' versions of a bot's move logic against each other,
	many games in a row, headlessly (no network, no viewer), and reports a win tally
	to gauge relative strength.

	Usage:
		python3 -m tools.arena.runner HEAD HEAD~3 --games 50
		python3 -m tools.arena.runner HEAD my-branch --bot bot_blob --games 20 --rows 25 --cols 25
'''

import argparse
import json
import pathlib
import select
import subprocess
import sys
import time

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2]))

from tools.arena import bridge, loader, mapgen
from tools.arena.engine import TrueBoard

REPO_ROOT = pathlib.Path(__file__).resolve().parents[2]
WORKTREE_ROOT = REPO_ROOT / '.arena-worktrees'
WORKER_SCRIPT = str(pathlib.Path(__file__).resolve().parent / 'worker.py')

MOVE_TIMEOUT_SECONDS = 5.0


class PlayerProcess(object):
	def __init__(self, ref, worktree_dir, bot_script):
		self.ref = ref
		self.proc = subprocess.Popen(
			[sys.executable, WORKER_SCRIPT, str(worktree_dir), bot_script],
			stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, bufsize=1)
		self.alive = True

	def send(self, msg):
		if not self.alive:
			return None
		try:
			self.proc.stdin.write(json.dumps(msg) + "\n")
			self.proc.stdin.flush()
		except (BrokenPipeError, ValueError):
			self.alive = False
			return None

		ready, _, _ = select.select([self.proc.stdout], [], [], MOVE_TIMEOUT_SECONDS)
		if not ready:
			self.alive = False
			return None
		line = self.proc.stdout.readline()
		if not line:
			self.alive = False
			return None
		try:
			return json.loads(line)
		except json.JSONDecodeError:
			self.alive = False
			return None

	def stop(self):
		if self.alive:
			try:
				self.proc.stdin.write(json.dumps({'stop': True}) + "\n")
				self.proc.stdin.flush()
			except (BrokenPipeError, ValueError):
				pass
		try:
			self.proc.wait(timeout=2)
		except subprocess.TimeoutExpired:
			self.proc.kill()
			self.proc.wait()

	def stderr_output(self):
		try:
			self.proc.stderr.close()
		except Exception:
			pass


def run_game(ref_a, ref_b, bot_script="bot_test", rows=25, cols=25, seed=None, max_turns=3000, verbose=False):
	generated = mapgen.generate_map(rows=rows, cols=cols, seed=seed)
	board = TrueBoard(generated, num_players=2)

	alias_a, worktree_a = loader.add_worktree(REPO_ROOT, ref_a, WORKTREE_ROOT)
	alias_b, worktree_b = loader.add_worktree(REPO_ROOT, ref_b, WORKTREE_ROOT)

	players = [
		PlayerProcess(ref_a, worktree_a, bot_script),
		PlayerProcess(ref_b, worktree_b, bot_script),
	]
	usernames = [ref_a, ref_b]
	memories = [bridge.PlayerMemory(0, board), bridge.PlayerMemory(1, board)]

	winner = None
	error = None
	first_turn = True

	while board.turn <= max_turns:
		moves = [None, None]
		for p in (0, 1):
			data = bridge.build_update(board, p, memories[p])
			msg = {'data': data}
			if first_turn:
				msg['start_data'] = bridge.build_start_data(p, usernames)
			reply = players[p].send(msg)
			if reply is None:
				error = "player %d (%s) failed to respond (crashed or timed out)" % (p, players[p].ref)
				winner = 1 - p # Forfeit
				break
			moves[p] = reply.get('move')
		first_turn = False
		if error:
			break

		for p in (0, 1):
			if moves[p] is None or not board.alive[p]:
				continue
			sr, sc, dr, dc, move_half = moves[p]
			board.apply_move(p, (sr, sc), (dr, dc), move_half)

		winner = board.winner()
		if winner is not None:
			break

		board.advance_growth()

		if verbose and board.turn % 50 == 0:
			scores = board.scores()
			print("  turn %d: %s" % (board.turn, scores))

	if winner is None and error is None: # Hit max_turns with no elimination - decide by score instead of leaving it unresolved
		scores = board.scores()
		if scores[0]['total'] != scores[1]['total']:
			winner = 0 if scores[0]['total'] > scores[1]['total'] else 1
		elif scores[0]['tiles'] != scores[1]['tiles']:
			winner = 0 if scores[0]['tiles'] > scores[1]['tiles'] else 1

	for p in players:
		p.stop()

	return {
		'winner': winner,
		'ref_winner': usernames[winner] if winner is not None else None,
		'turns': board.turn,
		'scores': board.scores(),
		'error': error,
	}


def run_match(ref_a, ref_b, games=20, bot_script="bot_test", rows=25, cols=25, base_seed=None, verbose=False):
	wins = {ref_a: 0, ref_b: 0}
	errors = 0
	total_turns = 0

	for i in range(games):
		seed = (base_seed if base_seed is not None else 0) + i
		swap = (i % 2 == 1) # Alternate sides each game to cancel out first-side bias
		a, b = (ref_b, ref_a) if swap else (ref_a, ref_b)

		result = run_game(a, b, bot_script=bot_script, rows=rows, cols=cols, seed=seed, verbose=verbose)
		total_turns += result['turns']

		if result['error']:
			errors += 1
			print("Game %d/%d: ERROR - %s" % (i + 1, games, result['error']))
			continue

		ref_winner = result['ref_winner']
		if ref_winner is not None:
			wins[ref_winner] += 1
		print("Game %d/%d: winner=%s turns=%d (%s vs %s)" % (i + 1, games, ref_winner, result['turns'], a, b))

	print()
	print("===== Results over %d games (bot=%s, %dx%d) =====" % (games, bot_script, rows, cols))
	print("%s: %d wins" % (ref_a, wins[ref_a]))
	print("%s: %d wins" % (ref_b, wins[ref_b]))
	if errors:
		print("errors/aborted: %d" % errors)
	if games - errors > 0:
		print("avg game length: %.1f turns" % (total_turns / games))

	return {'wins': wins, 'errors': errors}


def main():
	parser = argparse.ArgumentParser(description="Play two git refs' bot versions against each other locally")
	parser.add_argument('ref_a', help="First git ref (branch/commit/HEAD~N)")
	parser.add_argument('ref_b', help="Second git ref")
	parser.add_argument('--bot', default='bot_test', help="Move-method script to run (default: bot_test)")
	parser.add_argument('--games', type=int, default=20)
	parser.add_argument('--rows', type=int, default=25)
	parser.add_argument('--cols', type=int, default=25)
	parser.add_argument('--seed', type=int, default=None, help="Base random seed for map generation")
	parser.add_argument('--verbose', action='store_true')
	args = parser.parse_args()

	start = time.time()
	run_match(args.ref_a, args.ref_b, games=args.games, bot_script=args.bot,
				rows=args.rows, cols=args.cols, base_seed=args.seed, verbose=args.verbose)
	print("Elapsed: %.1fs" % (time.time() - start))


if __name__ == '__main__':
	main()
