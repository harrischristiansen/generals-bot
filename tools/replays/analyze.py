'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Replay Analysis: Learn from real games by comparing our play against our opponents'

	Usage:
		python3 -m tools.replays.analyze --bot overshadow --limit 50
		python3 -m tools.replays.analyze --replay RDBB_Ay9v --bot overshadow
'''

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from tools.replays import parser, simulate

GAMES_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'games')
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.replay-cache')


def local_replay_ids(games_dir=GAMES_DIR):
	ids = []
	if not os.path.isdir(games_dir):
		return ids
	for name in sorted(os.listdir(games_dir)):
		match = re.search(r'replays\.(.+)\.txt$', name)
		if match:
			ids.append(match.group(1))
	return ids


######################### Per-Game Metrics #########################

def analyze(replay): # Per-player metrics for one game
	game = simulate.SimulatedGame(replay)
	players = range(game.num_players)

	move_turns = [set() for _ in players]
	for move in replay.moves:
		move_turns[move.index].add(move.turn)

	general_share = [[] for _ in players]	# army fraction sitting on our general
	land_at = [[] for _ in players]
	death_turn = [None for _ in players]

	def on_turn(g):
		scores = g.scores()
		for p in players:
			if not g.alive[p]:
				if death_turn[p] is None:
					death_turn[p] = g.turn
				continue
			land_at[p].append(scores[p]['land'])
			general = g.generals[p]
			if general != simulate.DEAD_GENERAL and scores[p]['army'] > 0:
				general_share[p].append(g.armies[general] / float(scores[p]['army']))

	game.run(on_turn=on_turn)
	final = game.scores()
	last_turn = game.turn

	results = []
	for p in players:
		alive_until = death_turn[p] if death_turn[p] is not None else last_turn
		turns = max(alive_until, 1)

		idle, longest_idle, streak = 0, 0, 0
		for turn in range(turns):
			if turn in move_turns[p]:
				streak = 0
			else:
				idle += 1
				streak += 1
				longest_idle = max(longest_idle, streak)

		results.append({
			'player': p,
			'name': replay.usernames[p],
			'won': game.winner() == p,
			'died_turn': death_turn[p],
			'turns': turns,
			'moves': len(move_turns[p]),
			'idle_turns': idle,
			'idle_pct': 100.0 * idle / turns,
			'longest_idle': longest_idle,
			'final_land': final[p]['land'],
			'final_army': final[p]['army'],
			'land_at_100': land_at[p][99] if len(land_at[p]) > 99 else None,
			'land_at_300': land_at[p][299] if len(land_at[p]) > 299 else None,
			'avg_general_share': (sum(general_share[p]) / len(general_share[p])) if general_share[p] else 0.0,
		})

	return {'id': replay.id, 'turns': last_turn, 'players': results,
			'winner': game.winner(), 'afks': replay.afks}


######################### Reporting #########################

def print_game(result, bot_name=None):
	print("replay %s  (%d turns)" % (result['id'], result['turns']))
	for p in result['players']:
		tag = " <- us" if bot_name and p['name'] == bot_name else ""
		print("  %-18s %s land=%-4d army=%-6d moves=%-5d idle=%5.1f%% (longest %-4d) genShare=%4.0f%%%s" % (
			p['name'], "WON " if p['won'] else "lost",
			p['final_land'], p['final_army'], p['moves'],
			p['idle_pct'], p['longest_idle'], 100 * p['avg_general_share'], tag))


def aggregate(results, bot_name):
	us, them = [], []
	wins = 0
	for result in results:
		for p in result['players']:
			(us if p['name'] == bot_name else them).append(p)
			if p['name'] == bot_name and p['won']:
				wins += 1

	if not us:
		print("No games found for %s" % bot_name)
		return

	def avg(rows, key):
		vals = [r[key] for r in rows if r[key] is not None]
		return sum(vals) / len(vals) if vals else 0.0

	print()
	print("===== %d games as %s: %d wins (%.0f%%) =====" % (len(us), bot_name, wins, 100.0*wins/len(us)))
	print("%-22s %12s %12s" % ("metric", bot_name, "opponents"))
	for label, key in (("final land", 'final_land'), ("final army", 'final_army'),
						("land @ turn 100", 'land_at_100'), ("land @ turn 300", 'land_at_300'),
						("moves made", 'moves'), ("idle %", 'idle_pct'),
						("longest idle streak", 'longest_idle')):
		print("%-22s %12.1f %12.1f" % (label, avg(us, key), avg(them, key)))
	print("%-22s %11.0f%% %11.0f%%" % ("army on general", 100*avg(us,'avg_general_share'), 100*avg(them,'avg_general_share')))

	stalled = [r for r in us if r['longest_idle'] >= 25]
	if stalled:
		print()
		print("games where we stalled 25+ turns straight: %d of %d" % (len(stalled), len(us)))
		for r in sorted(stalled, key=lambda r: -r['longest_idle'])[:5]:
			print("   longest idle %-5d moves %-5d land %-4d %s" % (
				r['longest_idle'], r['moves'], r['final_land'], "WON" if r['won'] else "lost"))


def main():
	argp = argparse.ArgumentParser(description="Analyze generals.io replays to compare our bot against human opponents")
	argp.add_argument('--bot', default='overshadow', help="Our username in these replays")
	argp.add_argument('--replay', help="Analyze a single replay id")
	argp.add_argument('--limit', type=int, default=25, help="How many local replays to analyze")
	argp.add_argument('--region', default='na')
	argp.add_argument('--quiet', action='store_true', help="Only print the aggregate table")
	args = argp.parse_args()

	ids = [args.replay] if args.replay else local_replay_ids()[:args.limit]

	results = []
	for replay_id in ids:
		try:
			replay = parser.fetch(replay_id, region=args.region, cache_dir=CACHE_DIR)
			result = analyze(replay)
		except Exception as e:
			print("  %s: skipped (%s)" % (replay_id, e))
			continue
		results.append(result)
		if not args.quiet:
			print_game(result, args.bot)

	if results:
		aggregate(results, args.bot)


if __name__ == '__main__':
	main()
