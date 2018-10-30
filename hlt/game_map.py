from . import collision, entity, constants
import logging
from .entity import Position, Vector
from .tactic import *

class Map:
    """
    Map which houses the current game information/metadata.
    
    :ivar my_id: Current player id associated with the map
    :ivar width: Map width
    :ivar height: Map height
    """
    class InstanceIdentity(Enum):
        ALLYSHIP = 0
        ENEMYSHIP = 1
        PLANET = 2
        ROADBLOCK = 3

    def __init__(self, my_id, width, height):
        """
        :param my_id: User's id (tag)
        :param width: Map width
        :param height: Map height
        """
        self.my_id = my_id
        self.width = width
        self.height = height
        self.midPoint = Position(self.width/2, self.height/2)
        self.size = self.width * self.height
        self._players = {}
        self._planets = {}
        # number of players
        self.np = 0

        self.steal_team = []
        self.n_steal_allow = 0

        self._roadblocks = []
        self.corners = [
        Position(0,0),Position(self.width,0),Position(0,self.height),Position(self.width,self.height)
        ]
        self.rb_dir_from_corners = [
            [Position(0,1), Position(1,0)],
            [Position(-1,0), Position(0,1)],
            [Position(0,-1), Position(1,0)],
            [Position(-1,0), Position(0,-1)],
        ]
        self.rb_length_from_corners = [
            [self.height/2, self.width/2],
            [self.width/2, self.height/2],
            [self.height/2, self.width/2],
            [self.width/2, self.height/2],
        ]

        self.dict_id_to_instance_ship = {}
        self.dict_id_to_instance_planet = {}

        self.distances_dict_ally = {} # A matrix (dict of list) recording the closest enemy ship for each our ship
        self.distances_dict_enemy = {} # A matrix (dict of list) recording the closest enemy ship for each our ship
        self.distances_dict_all = {} # A matrix (dict of list) recording the closest enemy ship for each our ship

    def get_by_id_ship(self, instance_id):
        if instance_id in self.dict_id_to_instance_ship:
            return self.dict_id_to_instance_ship[instance_id]
        else:
            return None

    def get_by_id_planet(self, instance_id):
        if instance_id in self.dict_id_to_instance_planet:
            return self.dict_id_to_instance_planet[instance_id]
        else:
            return None

    def update_itself(self):

        # update dict_id_to_instance
        self.dict_id_to_instance_planet = {}
        all_instances = self.all_planets()
        for i in all_instances:
            self.dict_id_to_instance_planet[i.id] = i
        all_instances = self._all_ships()
        for i in all_instances:
            self.dict_id_to_instance_ship[i.id] = i

        # update the number of players
        self.np = len(self._players)

        # update: add blocking things along the borders
        self._roadblocks = []
        for i in range(len(self.corners)):
            for j in range(len(self.rb_dir_from_corners[0])):
                steps = int(self.rb_length_from_corners[i][j] / ((constants.UNIT_DIST_RB_CORNER+ constants.UNIT_DIST_RB_BORDER)/2) )
                H = constants.UNIT_DIST_RB_BORDER
                L = constants.UNIT_DIST_RB_CORNER
                delta = (H-L)*(H+L)/2/self.rb_length_from_corners[i][j]
                for k in range(steps):
                    pos = Position(self.corners[i].x + (k * delta + L) * self.rb_dir_from_corners[i][j].x, self.corners[i].y + (k * delta + L) * self.rb_dir_from_corners[i][j].y)
                    self._roadblocks.append(pos)

        # update field score
        myships = self.get_me().all_ships()
        enemyships = self._all_enemy_ships()
        for i in myships:
            i.battle_field_score = i.field_score(self.distances_dict_ally, self.distances_dict_enemy, self.np)
        for i in enemyships:
            i.battle_field_score = i.field_score(self.distances_dict_enemy, self.distances_dict_ally, self.np)

        self.n_steal_allow = min(len(myships)/10, 5)
        self.steal_team = []

        return 

    def update_last_turn_database(self):
        # record last turn's enemy's ships' position

        lt_ship_db = {}
        all_ships = self._all_ships()
        for i in all_ships:
            lt_ship_db[i.id] = (Position(i.x, i.y), i.current_task, i.current_target_id)
        return lt_ship_db

    def update_current_info_based_in_last_turn_database(self,lt_ship_db):

        all_ships = self._all_ships()
        for i in all_ships:
            if i.id in lt_ship_db:
                pos = lt_ship_db[i.id][0]
                i.lastx, i.lasty = pos.x, pos.y
                i.assigned_task = lt_ship_db[i.id][1]
                i.assigned_target_id = lt_ship_db[i.id][2]
            else:
                i.lastx, i.lasty = i.x, i.y

        for ship in all_ships:
            if len(self.distances_dict_ally[ship.id]) >0:
                ship.targetShip = self.distances_dict_ally[ship.id][0][0]
                if ship.targetShip:
                    attackVector = Vector(ship.targetShip.x - ship.x, ship.targetShip.y - ship.y)
                    attackVector = attackVector.normalized() * constants.MAX_SPEED
                    ship.dummyAttacker1 = entity.DummyShip(ship.x, ship.y, attackVector.x, attackVector.y)
            
            attackVector = Vector(ship.x - ship.lastx, ship.y - ship.lasty)
            attackVector = attackVector.normalized() * constants.MAX_SPEED
            ship.dummyAttacker2 = entity.DummyShip(ship.x, ship.y, attackVector.x, attackVector.y)
        return


    def get_me(self):
        """
        :return: The user's player
        :rtype: Player
        """
        return self._players.get(self.my_id)

    def get_player(self, player_id):
        """
        :param int player_id: The id of the desired player
        :return: The player associated with player_id
        :rtype: Player
        """
        return self._players.get(player_id)

    def all_players(self):
        """
        :return: List of all players
        :rtype: list[Player]
        """
        return list(self._players.values())

    def get_planet(self, planet_id):
        """
        :param int planet_id:
        :return: The planet associated with planet_id
        :rtype: entity.Planet
        """
        return self._planets.get(planet_id)

    def all_planets(self):
        """
        :return: List of all planets
        :rtype: list[entity.Planet]
        """
        return list(self._planets.values())

    def all_free_planets(self):
        plist = self.all_planets()
        planets = [] 
        for planet in plist:
            if not planet.is_owned():
                planets.append(planet)
        return planets

    def all_enemy_planets(self):
        plist = self.all_planets()
        planets = []
        for planet in plist:
            if planet.is_owned() and planet.owner != self.get_me():
                planets.append(planet)
        return planets

    def owned_planets(self, playerid):
        plist = self.all_planets()
        planets = []
        for planet in plist:
            if planet.is_owned() and planet.owner.id == playerid:
                planets.append(planet)
        return planets

    def docking_planets(self, playerid):
        ldp = set()
        slist = self.get_me().all_docking_ships()
        for ship in slist:
            if ship.owner == playerid:
                planet = closest_planets_by_distance(self, ship)[0]
                ldp.add(planet)
        return list(ldp)

    def all_planets_by_power(self):
        l_planets = self.all_planets()

    def nearby_entities_by_distance(self, entity):
        """
        :param entity: The source entity to find distances from
        :return: Dict containing all entities with their designated distances
        :rtype: dict
        """
        result = {}
        for foreign_entity in self._all_ships() + self.all_planets():
            if entity == foreign_entity:
                continue
            result.setdefault(entity.calculate_distance_between(foreign_entity), []).append(foreign_entity)
        return result

    def _link(self):
        """
        Updates all the entities with the correct ship and planet objects

        :return:
        """
        for celestial_object in self.all_planets() + self._all_ships():
            celestial_object._link(self._players, self._planets)

    def _parse(self, map_string):
        """
        Parse the map description from the game.

        :param map_string: The string which the Halite engine outputs
        :return: nothing
        """
        tokens = map_string.split()

        self._players, tokens = Player._parse(tokens)
        self._planets, tokens = entity.Planet._parse(tokens)

        assert(len(tokens) == 0)  # There should be no remaining tokens at this point
        self._link()

    def _all_ships(self):
        """
        Helper function to extract all ships from all players

        :return: List of ships
        :rtype: List[Ship]
        """
        all_ships = []
        for player in self.all_players():
            all_ships.extend(player.all_ships())
        return all_ships

    def _all_enemy_ships(self):
        all_ships = []
        for player in self.all_players():
            if player != self.get_me():
                all_ships.extend(player.all_ships())
        return all_ships


    def _intersects_entity(self, target):
        """
        Check if the specified entity (x, y, r) intersects any planets. Entity is assumed to not be a planet.

        :param entity.Entity target: The entity to check intersections with.
        :return: The colliding entity if so, else None.
        :rtype: entity.Entity
        """
        for celestial_object in self._all_ships() + self.all_planets():
            if celestial_object is target:
                continue
            d = celestial_object.calculate_distance_between(target)
            if d <= celestial_object.radius + target.radius + 0.1:
                return celestial_object
        return None

    def obstacles_between(self, ship, target, ignore=(), avoid_enemy = False):
        """
        Check whether there is a straight-line path to the given point, without planetary obstacles in between.

        :param entity.Ship ship: Source entity
        :param entity.Entity target: Target entity
        :param entity.Entity ignore: Which entity type to ignore
        :return: True: obstacle found. False: no obstacle
        :rtype: bool
        """

        xInRange = (0 + ship.radius +  constants.MAP_EDGE_FUDGE <= target.x <= self.width - ship.radius - constants.MAP_EDGE_FUDGE)
        yInRange = (0 + ship.radius +  constants.MAP_EDGE_FUDGE <= target.y <= self.height - ship.radius - constants.MAP_EDGE_FUDGE)
        if not (xInRange and yInRange):
            return True

        entities = ([] if issubclass(entity.Planet, ignore) else self.all_planets()) \
            + ([] if issubclass(entity.Ship, ignore) else self._all_ships())    
        
        foreign_ship = self._all_ships()
        
        # logging.info("old: %d, new: %d" % (len(oldEntities), len(entities)))

        for foreign_entity in entities:
            if foreign_entity == ship or foreign_entity == target:
                continue
            if collision.intersect_segment_circle(ship, target, foreign_entity, fudge=ship.radius + 0.1):
                return True

        for foreign_entity in foreign_ship:
            if foreign_entity == ship or foreign_entity == target:
                continue
            col, time = collision.collision_time(ship.radius + foreign_entity.radius + 0.1, ship, foreign_entity)
            if col and 0<=time<=1:
            # if col: 
                return True

        return False

    def obstacles_between_forDistractor(self, ship, target):
        xInRange = (0 + ship.radius +  constants.MAP_EDGE_FUDGE <= target.x <= self.width - ship.radius - constants.MAP_EDGE_FUDGE)
        yInRange = (0 + ship.radius +  constants.MAP_EDGE_FUDGE <= target.y <= self.height - ship.radius - constants.MAP_EDGE_FUDGE)
        if not (xInRange and yInRange):
            return True

        foreign_ship = self._all_ships()
        foreign_planet = self.all_planets()
        
        # logging.info("old: %d, new: %d" % (len(oldEntities), len(entities)))

        for foreign_entity in foreign_planet:
            if foreign_entity == ship or foreign_entity == target:
                continue
            if collision.intersect_segment_circle(ship, target, foreign_entity, fudge=ship.radius + 0.1):
                return True

        for foreign_entity in foreign_ship:
            if foreign_entity == ship or foreign_entity == target:
                continue
            col, time = collision.collision_time(ship.radius + foreign_entity.radius + 0.1, ship, foreign_entity)
            if col and 0<=time<=1:
            # if col: 
                return True

        list1 = [fs.dummyAttacker1 for fs in foreign_ship if fs!=ship and fs!=target and fs.dummyAttacker1 and fs.owner != ship.owner]
        list2 = [fs.dummyAttacker1 for fs in foreign_ship if fs!=ship and fs!=target and fs.dummyAttacker2 and fs.owner != ship.owner]
        for foreign_entity in list1+list2:
            col, time = collision.collision_time(ship.radius + foreign_entity.radius + constants.DISTRACTOR_EXTRA_DISTANCE + 0.1, ship, foreign_entity)
            if col and 0<=time<=1:
            # if col: 
                return True

        return False




    def obstacles_between_ori(self, ship, target, ignore=()):
        """
        Check whether there is a straight-line path to the given point, without planetary obstacles in between.

        :param entity.Ship ship: Source entity
        :param entity.Entity target: Target entity
        :param entity.Entity ignore: Which entity type to ignore
        :return: The list of obstacles between the ship and target
        :rtype: list[entity.Entity]
        """
        obstacles = []
        entities = ([] if issubclass(entity.Planet, ignore) else self.all_planets()) \
            + ([] if issubclass(entity.Ship, ignore) else self._all_ships())
        for foreign_entity in entities:
            if foreign_entity == ship or foreign_entity == target:
                continue
            if collision.intersect_segment_circle(ship, target, foreign_entity, fudge=ship.radius + 0.1):
                obstacles.append(foreign_entity)
        return obstacles

    def enemies_near_target(self, target, range):
        # enemy ships numbers near the entity within the range

        entities_by_distance = self.nearby_entities_by_distance(target)
        # logging.info(entities_by_distance)
        targets = []
        for distance in sorted(entities_by_distance):
            if distance>range: break
            for item in entities_by_distance[distance]:
                if isinstance(item, entity.Ship) and item.owner != self.get_me():
                    targets.append(item)
        return targets

    def get_invading_ships(self):
        pLowned = self.owned_planets(self.my_id)
        pLdocking = self.docking_planets(self.my_id)
        sLenemy = self._all_enemy_ships()
        returnList = set()
        for planet in (pLdocking + pLowned):
            for ship in sLenemy:
                if ship.calculate_distance_between(planet) < constants.getALL_DEFENSE_RANGE(self.np):
                    returnList.add(ship)
        return list(returnList)


    def get_all_enemies_by_distance(self):
        # Compute the ditance matrix, sort by distance
        self.distances_dict_enemy = {}

        
        myships = self._all_ships()
        # myships = self.get_me().all_ships()
        enemy_ships = self._all_enemy_ships()

        for shipi in myships:
            distanc_i = []
            for shipj in enemy_ships:
                distanc_i.append((shipj, shipi.calculate_distance_between(shipj)))
            distanc_i.sort(key= lambda x: x[1])
            self.distances_dict_enemy[shipi.id] = distanc_i
        # logging.info("All enemy: my ships number:"+ str(len(myships))+", allies_ships number:"+ str(len(enemy_ships)))
        return self.distances_dict_enemy

    def get_all_allies_by_distance(self):
        # Compute the ditance matrix, sort by distance
        self.distances_dict_ally = {}

        myships = self._all_ships()
        # myships = self.get_me().all_ships()
        allies_ships = self.get_me().all_ships()

        for shipi in myships:
            distanc_i = []
            for shipj in allies_ships:
                if shipi.id != shipj.id:
                    distanc_i.append((shipj, shipi.calculate_distance_between(shipj)))
            distanc_i.sort(key= lambda x: x[1])
            self.distances_dict_ally[shipi.id] = distanc_i
        # logging.info("All allies: my ships number:"+ str(len(myships))+", allies_ships number:"+ str(len(allies_ships)))

        return self.distances_dict_ally

    def get_all_instances_by_distance(self):
        # Compute the ditance matrix, sort by distance
        self.distances_dict_all = {}

        myships = self.get_me().all_ships()

        enemy_ships = self._all_enemy_ships()
        allies_ships = self.get_me().all_ships()
        planets = self.all_planets()
        rbs = self._roadblocks

        for shipi in myships:
            distanc_i = []
            for shipj in allies_ships:
                if shipi.id != shipj.id:
                    distanc_i.append((shipj, shipi.calculate_distance_between(shipj), self.InstanceIdentity.ALLYSHIP))
            for shipj in enemy_ships:
                distanc_i.append((shipj, shipi.calculate_distance_between(shipj), self.InstanceIdentity.ENEMYSHIP))
            for shipj in planets:
                distanc_i.append((shipj, shipi.calculate_distance_between(shipj), self.InstanceIdentity.PLANET))
            for shipj in rbs:
                distanc_i.append((shipj, shipi.calculate_distance_between(shipj), self.InstanceIdentity.ROADBLOCK))
            distanc_i.sort(key= lambda x: x[1])
            self.distances_dict_all[shipi.id] = distanc_i
        
        # logging.info("All instance: my ships number:"+ str(len(myships))+", allies_ships number:"+ str(len(allies_ships)))
        # logging.info("All instance: enemy_ships number:"+ str(len(enemy_ships))+", planets number:"+ str(len(planets)))
        # logging.info("All instance: rbs number:"+ str(len(rbs)))

        return self.distances_dict_all   


class Player:
    """
    :ivar id: The player's unique id
    """
    def __init__(self, player_id, ships={}):
        """
        :param player_id: User's id
        :param ships: Ships user controls (optional)
        """
        self.id = player_id
        self._ships = ships
        self.seen_ships = {}
        self.new_ships = {}

    def update_ship_database(self):
        for ship in self.all_ships():
            ship.ordered = False
        for ship in self.new_ships:
            self.seen_ships[ship.id] = True
        self.new_ships = []
        for ship in self.all_ships() :
            if ship.id not in self.seen_ships:
                self.new_ships.append(ship)

    def all_ships(self):
        """
        :return: A list of all ships which belong to the user
        :rtype: list[entity.Ship]
        """
        return list(self._ships.values())

    def all_free_ships(self, sortedby = None):
        AllShips = self.all_ships()
        AllFreeShips = []
        for ship in AllShips:
            if ship.docking_status == ship.DockingStatus.UNDOCKED:
                AllFreeShips.append(ship)
        if sortedby:
            AllFreeShips.sort(key = lambda x: sortedby[x.id][0][1])
        return AllFreeShips

    def all_docked_ships(self):
        AllShips = self.all_ships()
        AllDockedShips = []
        for ship in AllShips:
            if ship.docking_status == ship.DockingStatus.DOCKED:
                AllDockedShips.append(ship)
        return AllDockedShips

    def all_docking_ships(self):
        AllShips = self.all_ships()
        AllDockingShips = []
        for ship in AllShips:
            if ship.docking_status == ship.DockingStatus.DOCKING:
                AllDockingShips.append(ship)
        return AllDockingShips

    def get_ship(self, ship_id):
        """
        :param int ship_id: The ship id of the desired ship.
        :return: The ship designated by ship_id belonging to this user.
        :rtype: entity.Ship
        """
        return self._ships.get(ship_id)

    @staticmethod
    def _parse_single(tokens):
        """
        Parse one user given an input string from the Halite engine.

        :param list[str] tokens: The input string as a list of str from the Halite engine.
        :return: The parsed player id, player object, and remaining tokens
        :rtype: (int, Player, list[str])
        """
        player_id, *remainder = tokens
        player_id = int(player_id)
        ships, remainder = entity.Ship._parse(player_id, remainder)
        player = Player(player_id, ships)
        return player_id, player, remainder

    @staticmethod
    def _parse(tokens):
        """
        Parse an entire user input string from the Halite engine for all users.

        :param list[str] tokens: The input string as a list of str from the Halite engine.
        :return: The parsed players in the form of player dict, and remaining tokens
        :rtype: (dict, list[str])
        """
        num_players, *remainder = tokens
        num_players = int(num_players)
        players = {}

        for _ in range(num_players):
            player, players[player], remainder = Player._parse_single(remainder)

        return players, remainder

    def __str__(self):
        return "Player {} with ships {}".format(self.id, self.all_ships())

    def __repr__(self):
        return self.__str__()
