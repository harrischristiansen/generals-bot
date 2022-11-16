'''
	@ Harris Christiansen (code@HarrisChristiansen.com)
	Generals.io Automated Client - https://github.com/harrischristiansen/generals-bot
	Constants: Constants used throughout the code
'''

SHOULD_DIRTY_MAP_ON_MOVE = True

ENDPOINT_BOT = "wss://botws.generals.io/socket.io/?EIO=3&transport=websocket"
ENDPOINT_PUBLIC = "wss://ws.generals.io/socket.io/?EIO=3&transport=websocket"
BOT_KEY = "sd09fjd203i0ejwi"

BANNED_PLAYERS = [
	"hanwi4",
'''
	"lilBlakey",
	"hunterjacksoncarr@"
	"ExpiredCat",
	"hunter2.0",
	"okloveme",
	"hunterjacksoncarr@",
	"creeded",
	"Centro2",
	"hunter4.0",
'''
]

BANNED_CHAT_PLAYERS = [
	"UYHS4J",
]

REPLAY_URLS = {
	'na': "http://generals.io/replays/",
	'eu': "http://eu.generals.io/replays/",
	'bot': "http://bot.generals.io/replays/",
}

START_KEYWORDS = ["start", "go", "force", "play", "ready", "rdy"]
HELLO_KEYWORDS = ["hi", "hello", "hey", "sup", "myssix"]
HELP_KEYWORDS = ["help", "config", "change"]

GENERALS_MAPS = [
	"KILL A KING",
	"Plots",
	"Speed",
	"Experiment G",
	"WIN or LOSE",
	"The Inquisitor",
	"Kingdom of Branches",
	"Hidden 1",
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


PRE_HELP_TEXT = [
	"| Hi, I am Myssix - a generals.io bot",
	"| ======= Available Commands =======",
	"| start: send force start",
	"| speed 4: set game play speed [1, 2, 3, 4]",
	"| map [top, hot]: set a random map (optionally from the top or hot list)",
	"| map Map Name: set map by name",
	"| team 1: join a team [1 - 8]",
	"| normal: set map to default (no map)",
	"| swamp 0.5: set swamp value for normal map",
	"| Code available at: git.io/myssix",
]
GAME_HELP_TEXT = [
	"| ======= Available Commands =======",
	"| team: request not to be attacked",
	"| unteam: cancel team",
	"| pause: pause army movement",
	"| unpause: unpause army movement",
	"| Code available at: git.io/myssix",
]
HELLO_TEXT = [
	" Hi, I am Myssix - a generals.io bot",
	" Say 'go' to start, or 'help' for a list of additional commands",
	" Code available at: git.io/myssix",
]
GAME_HELLO_TEXT = [
	" Hi, I am Myssix - a generals.io bot",
	" Say 'help' for available commands - Code available at: git.io/myssix",
]