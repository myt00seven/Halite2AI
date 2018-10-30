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

START_RUSH_DISTANCE_THRESHOLD = 100

TimeThreshold = 1.75

ATTACKING_RANGE_FOR_DOCK_SHIPS = 70

DOCKING_TIME_RANGE = 35

# When our ships start defense
CLOSE_DEFENSE_RANGE = 40.0 
CLOSE_DEFENSE_RANGE4 = 40.0 

# absolute safe range to dock (5+12)*7 = 119
ALL_DEFENSE_RANGE = 80.0

# When enemy appears within this range, engages battle
# determine if this ship is controled by "combat" task
COMBAT_RANGE = 15.0

# the distance the ships within this range will try to get close to each other
GROUPING_DISTANCE = 21.0
GROUPING_NAVI_FACTOR = 0.4

# the range to determine the balance of power
# the basis of deciding if we assign "weak" or "strong" to the ship
SHORT_ASSESS_RANGE = 30.0
# the range that free ship will goes to rescue ship in weak
RESCUE_RANGE = 70.0

# Planet explore ships ratio
# How many more ship we allow to go to each planet comparing to is population threshold
PLANET_EXPLORE_SHIP_RATIO = 3

# if counter rush is activated, if any enemy ship appears with in this range, all ships will start undock
UNDOCKING_FOR_COMBAT_RANGE_LOWER = 0.0
UNDOCKING_FOR_COMBAT_RANGE_UPPER = 42.0

SAFE_REDOCK_DISTANCE = 84.0

combat_nto1_threshold = 2

RUSH_MAP_SIZE = 264*176

PRINT_ACTION_LOG = True

adjustFactorSize = 1
adjustFactorDensity = 1
adjustFactorCenter = 1
adjustFactorDistance = 0.2

adjustFactorSize4 = 1
adjustFactorDensity4 = 0.9
adjustFactorCenter4 = 2
adjustFactorDistance4 = 0.01	

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





