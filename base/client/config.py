'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Bot Config: Every behaviour added after f9eff1c is toggleable here, so a bot script can
	pick exactly which improvements it plays with.

	BotConfig.legacy()  - the original behaviour, before any of the 2026 changes
	BotConfig.strong()  - everything on (the default for a new Map)

	Lives on the Map (gamemap.config) so both bot_moves and Tile can reach it.
'''

from .constants import *


class BotConfig(object):
	def __init__(self,
					discover8=True,					# Treat all 8 neighbours as discovery/vision, not just the 4 move directions
					stealth_neutral_cities=True,	# Don't grab a neutral city an enemy can see
					gather_paths=True,				# path_to breaks equal-length ties toward routes that pick up more army
					hold_active_path=True,			# move_outward won't displace a tile the active path needs
					commit_to_capture=True,			# Don't peel army off to expand while running at a general/city
					defend_general=True,			# Reactive garrison + reinforcement when a threat nears our general
					smart_gather=True,				# Score whole gather routes instead of always sourcing the largest tile
					defend_general_radius=DEFEND_GENERAL_RADIUS,
					defend_general_margin=DEFEND_GENERAL_MARGIN,
					defend_general_max_share=DEFEND_GENERAL_MAX_SHARE,
					defend_general_arrival_slack=DEFEND_GENERAL_ARRIVAL_SLACK,
					gather_candidates=GATHER_CANDIDATES,
					gather_delay_factor=GATHER_DELAY_FACTOR,
					gather_urgent_multiplier=GATHER_URGENT_MULTIPLIER):
		self.discover8 = discover8
		self.stealth_neutral_cities = stealth_neutral_cities
		self.gather_paths = gather_paths
		self.hold_active_path = hold_active_path
		self.commit_to_capture = commit_to_capture
		self.defend_general = defend_general
		self.smart_gather = smart_gather

		self.defend_general_radius = defend_general_radius
		self.defend_general_margin = defend_general_margin
		self.defend_general_max_share = defend_general_max_share
		self.defend_general_arrival_slack = defend_general_arrival_slack
		self.gather_candidates = gather_candidates
		self.gather_delay_factor = gather_delay_factor
		self.gather_urgent_multiplier = gather_urgent_multiplier

	def __repr__(self):
		flags = [name for name in ("discover8", "stealth_neutral_cities", "gather_paths",
									"hold_active_path", "commit_to_capture", "defend_general",
									"smart_gather") if getattr(self, name)]
		return "BotConfig(%s)" % (", ".join(flags) if flags else "legacy")

	@classmethod
	def legacy(cls, **overrides): # How the bot played before the 2026 changes
		settings = dict(discover8=False, stealth_neutral_cities=False, gather_paths=False,
						hold_active_path=False, commit_to_capture=False, defend_general=False,
						smart_gather=False)
		settings.update(overrides)
		return cls(**settings)

	@classmethod
	def strong(cls, **overrides): # Everything we have added since
		return cls(**overrides)
