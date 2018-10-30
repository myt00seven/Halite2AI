#: Max number of units of distance a ship can travel in a turn
MAX_SPEED = 7
#: Radius of a ship
SHIP_RADIUS = 0.5
#: Starting health of ship, also its max
MAX_SHIP_HEALTH = 255.0
#: Starting health of ship, also its max
BASE_SHIP_HEALTH = 255.0
#: Weapon cooldown period
WEAPON_COOLDOWN = 1
#: Weapon damage radius
WEAPON_RADIUS = 5.0
#: Weapon damage
WEAPON_DAMAGE = 64
#: Radius in which explosions affect other entities
EXPLOSION_RADIUS = 10.0
#: Distance from the edge of the planet at which ships can try to dock
DOCK_RADIUS = 4.0
#: Number of turns it takes to dock a ship
DOCK_TURNS = 5
#: Number of production units per turn contributed by each docked ship
BASE_PRODUCTIVITY = 6
#: Distance from the planets edge at which new ships are created
SPAWN_RADIUS = 2.0

DEFAULT_SPEED = int(MAX_SPEED)

MAP_EDGE_FUDGE = 0.5

START_RUSH_DISTANCE_THRESHOLD = 120

TimeThreshold = 1.6
TimeThreshold_2 = 1.95

ATTACKING_RANGE_FOR_DOCK_SHIPS = 150

DOCKING_TIME_RANGE = 35

EPS = 0.01

RADIUS_ESCAPE = WEAPON_RADIUS + MAX_SPEED +1

# When our ships start defense
CLOSE_DEFENSE_RANGE = 50.0 
CLOSE_DEFENSE_RANGE4 = 50.0 

# absolute safe range to dock (5+12)*7 = 119
ALL_DEFENSE_RANGE = 80.0
ALL_DEFENSE_RANGE4 = 80.0

# When enemy appears within this range, engages battle
# determine if this ship is controled by "combat" task
COMBAT_RANGE = 15.0

# the range to determine the balance of power
# the basis of deciding if we assign "weak" or "strong" to the ship
SHORT_ASSESS_RANGE = 15.0
SHORT_ASSESS_RANGE4 = 15.0
# the range that free ship will goes to rescue ship in weak
RESCUE_RANGE = 80.0

# Planet explore ships ratio
# How many more ship we allow to go to each planet comparing to is population threshold
PLANET_EXPLORE_SHIP_RATIO = 3

# if counter rush is activated, if any enemy ship appears with in this range, all ships will start undock
UNDOCKING_FOR_COMBAT_RANGE_LOWER = 0.0
UNDOCKING_FOR_COMBAT_RANGE_UPPER = 42.0

SAFE_REDOCK_DISTANCE = 84.0

combat_nto1_threshold = 3

RUSH_MAP_SIZE = 25000
RUSH_TURN_ALLOWED = 7.5

PRINT_ACTION_LOG = True

adjustFactorSize = 1.0
adjustFactorDensity = 1.5
adjustFactorCenter = 0.5
adjustFactorDistance = 0.1

adjustFactorSize4 = 0.5
adjustFactorDensity4 = 1
adjustFactorCenter4 = 0.5
adjustFactorDistance4 = 1

# The maximum ratio of your ship on "steal_weak_enemy" task
RATIO_STEAL_WEAK_ENEMY = 0.1

# Roadblocks and movement Field
# Unit distance of Road Block
UNIT_DIST_RB_BORDER = 5.0
UNIT_DIST_RB_CORNER = 1.0

# Fushion Movement Ratio Parametets:
AWAY_FROM_RANGE = 50
CLOSE_POINT_RANGE = 50
STEAL_ASSESS_RANGE = 100

# the distance the ships within this range will try to get close to each other
GROUPING_DISTANCE = 25.0
GROUPING_DISTANCE4 = 30

GROUPING_NAVI_FACTOR = 0.4
GROUPING_NAVI_FACTOR4 = 0.6

# when retreat, 
# the ratio of leaning to ally
RETREAT_ALLY_SPOT_RATIO = 0.25
# RETREAT_ALLY_SPOT_RATIO = 0
RETREAT_ALLY_SPOT_RATIO4 = 0.25

# threshold of how much lower will lead to combat
COMBAT_THRESHOLD = 0.5

DISTRACTOR_EXTRA_DISTANCE = WEAPON_RADIUS + 2

ALLOW_RESCUE = True


def getadjustFactorSize(pn=2):
	return adjustFactorSize if pn==2 else adjustFactorSize4

def getadjustFactorDensity(pn=2):
	return adjustFactorDensity if pn==2 else adjustFactorDensity4

def getadjustFactorCenter(pn=2):
	return adjustFactorCenter if pn==2 else adjustFactorCenter4

def getadjustFactorDistance(pn=2):
	return adjustFactorDistance if pn==2 else adjustFactorDistance4

def getCLOSE_DEFENSE_RANGE(pn=2):
	return CLOSE_DEFENSE_RANGE if pn==2 else CLOSE_DEFENSE_RANGE4

def getGROUPING_DISTANCE(pn=2):
	return GROUPING_DISTANCE if pn==2 else GROUPING_DISTANCE4

def getGROUPING_NAVI_FACTOR(pn=2):
	return GROUPING_NAVI_FACTOR if pn==2 else GROUPING_NAVI_FACTOR4

def getRETREAT_ALLY_SPOT_RATIO(pn=2):
	return RETREAT_ALLY_SPOT_RATIO if pn==2 else RETREAT_ALLY_SPOT_RATIO4

def getALL_DEFENSE_RANGE(pn=2):
	return ALL_DEFENSE_RANGE if pn==2 else ALL_DEFENSE_RANGE4

def getSHORT_ASSESS_RANGE(pn=2):
	return SHORT_ASSESS_RANGE if pn==2 else SHORT_ASSESS_RANGE4
