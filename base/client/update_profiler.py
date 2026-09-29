'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Update Profiler: Measure how evenly the server delivers game_update messages

	The server should send one game_update per turn, every 0.5s. Each update is timestamped
	the moment the socket read returns, and compared against the previous one. Updates that
	arrive within BUNCH_THRESHOLD of each other are counted as one burst.
'''

import logging
import os
import time

EXPECTED_INTERVAL = 0.5		# Seconds between game updates at normal speed
BUNCH_THRESHOLD = 0.1		# Updates closer together than this arrived as a burst
SUMMARY_EVERY = 20			# Log a summary every N updates


class UpdateProfiler(object):
	def __init__(self):
		self.reset()

	def reset(self):
		self._last_arrival = None
		self._last_turn = None
		self._gaps = []			# Seconds between consecutive updates
		self._bursts = []		# Sizes of each burst of back-to-back updates
		self._burst = 0
		self._skipped_turns = 0
		self._rows = []			# (turn, arrival, gap, waited) for the CSV

	def record(self, turn, arrival, waited):
		'''arrival: time.monotonic() when recv() returned. waited: seconds recv() blocked for.'''
		gap = None
		if self._last_arrival != None:
			gap = arrival - self._last_arrival
			self._gaps.append(gap)

			if gap < BUNCH_THRESHOLD:
				self._burst += 1
			else:
				self._bursts.append(self._burst)
				self._burst = 1
		else:
			self._burst = 1

		if self._last_turn != None and turn - self._last_turn > 1:
			self._skipped_turns += turn - self._last_turn - 1

		logging.info("[update] turn %4d  gap %7s  waited %6.1fms%s" % (
			turn,
			"%.1fms" % (gap * 1000) if gap != None else "-",
			waited * 1000,
			"  <- bunched" if gap != None and gap < BUNCH_THRESHOLD else ""))

		self._rows.append((turn, arrival, gap, waited))
		self._last_arrival = arrival
		self._last_turn = turn

		if len(self._rows) % SUMMARY_EVERY == 0:
			self.log_summary()

	def summary(self):
		if not self._gaps:
			return None

		gaps = sorted(self._gaps)
		bursts = self._bursts + ([self._burst] if self._burst else [])
		mean = sum(gaps) / len(gaps)
		return {
			'updates': len(self._rows),
			'mean_ms': mean * 1000,
			'stdev_ms': (sum((g - mean) ** 2 for g in gaps) / len(gaps)) ** 0.5 * 1000,
			'p50_ms': gaps[len(gaps) // 2] * 1000,
			'p95_ms': gaps[min(len(gaps) - 1, int(len(gaps) * 0.95))] * 1000,
			'max_ms': gaps[-1] * 1000,
			'bunched': sum(1 for g in gaps if g < BUNCH_THRESHOLD),
			'late': sum(1 for g in gaps if g > EXPECTED_INTERVAL * 1.5),
			'max_burst': max(bursts) if bursts else 0,
			'burst_sizes': {size: bursts.count(size) for size in sorted(set(bursts))},
			'skipped_turns': self._skipped_turns,
		}

	def log_summary(self):
		s = self.summary()
		if s == None:
			return
		logging.info("[update summary] %d updates | gap mean %.0fms stdev %.0fms p50 %.0fms p95 %.0fms max %.0fms | "
			"bunched %d (<%dms), late %d (>%dms), max burst %d, bursts %s, skipped turns %d" % (
			s['updates'], s['mean_ms'], s['stdev_ms'], s['p50_ms'], s['p95_ms'], s['max_ms'],
			s['bunched'], BUNCH_THRESHOLD * 1000, s['late'], EXPECTED_INTERVAL * 1500,
			s['max_burst'], s['burst_sizes'], s['skipped_turns']))

	def save_csv(self, path):
		if not self._rows:
			return
		directory = os.path.dirname(path)
		if directory and not os.path.isdir(directory):
			os.makedirs(directory)

		start = self._rows[0][1]
		with open(path, 'w') as f:
			f.write("turn,seconds_since_first,gap_ms,recv_waited_ms\n")
			for turn, arrival, gap, waited in self._rows:
				f.write("%d,%.4f,%s,%.2f\n" % (turn, arrival - start,
					"%.2f" % (gap * 1000) if gap != None else "", waited * 1000))
		logging.info("[update profiler] timing saved to %s" % path)
