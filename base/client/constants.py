'''
	@ Harris Christiansen (Harris@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Constants: Constants used throughout the code
'''

ENDPOINT_BOT = "ws://botws.generals.io/socket.io/?EIO=3&transport=websocket"
ENDPOINT_PUBLIC = "ws://ws.generals.io/socket.io/?EIO=3&transport=websocket"
BOT_KEY = "O13f0dijsf"

REPLAY_URLS = {
	'na': "http://generals.io/replays/",
	'eu': "http://eu.generals.io/replays/",
}

START_KEYWORDS = ["start", "go", "force", "play"]

GENERALS_MAPS = [
	"who will win the best",
	"1v1 Ultimate",
	"King of the Hill (FFA)",
	"KILL A KING",
	"The War of Classes",
	"Plots",
	"City",
	"Speed",
	"Experiment G",
	"WIN or LOSE",
	"Russian Roulette ",
]

DIRECTIONS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

TILE_EMPTY = -1
TILE_MOUNTAIN = -2
TILE_FOG = -3
TILE_OBSTACLE = -4

# Opponent Type Definitions
OPP_EMPTY = 0
OPP_ARMY = 1
OPP_CITY = 2
OPP_GENERAL = 3

MAX_NUM_TEAMS = 8