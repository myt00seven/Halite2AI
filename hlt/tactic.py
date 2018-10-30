import logging
import abc
import math
from enum import Enum
from . import collision, entity, game_map, networking, constants
import numpy as np

def closest_planets_by_distance(gamemap, ship):
    entities_by_distance = gamemap.nearby_entities_by_distance(ship)
    # logging.info("len of entities_by_distance:"+ str(len(entities_by_distance)))
    target_list = []
    for distance in sorted(entities_by_distance):
        for target in entities_by_distance[distance]:
            if isinstance(target, entity.Planet):
                target_list.append(target)
    return target_list

def closest_ships_by_distance(gamemap, ship):
    entities_by_distance = gamemap.nearby_entities_by_distance(ship)
    # logging.info("len of entities_by_distance:"+ str(len(entities_by_distance)))
    target_list = []
    for distance in sorted(entities_by_distance):
        for target in entities_by_distance[distance]:
            if isinstance(target, entity.Ship):
                target_list.append(target)
    return target_list

def closest_enemy_ship(gamemap, ship, no_limit=False):
    # return closest enemy planet
    if isinstance(ship, entity.Ship):
        ships = gamemap.distances_dict_enemy[ship.id]
        for (ship, dist) in ships:
            if no_limit or len(ship.targeted)<constants.combat_nto1_threshold:
                return ship
    elif isinstance(ship, entity.Planet):
        ships = closest_ships_by_distance(gamemap, ship)
        return ships[0]

    logging.info("Assert: no enemy ships\t"+"Current Ship:"+str(ship.id))
    return None

def closest_not_mine_planet(gamemap, ship):
#     # return closest unoccupied planet or enemy planet
    planets = closest_planets_by_distance(gamemap, ship)
    for planet in planets:
        if planet.owner != gamemap.get_me():
            return planet

    logging.info("Assert: no enemy planets")
    return None

def planet_allow_new_conquer(target):
    if target.is_full() is False and (target.num_docking_spots-len(target._docked_ships)) * constants.PLANET_EXPLORE_SHIP_RATIO > len(target.incoming_ships):
        return True
    return False

def best_next_planets(gamemap, ship, targetList):
    # adjust factor: 
    # 1: scale with radius. 0.5: radius difference less important
    # constant of number of players
    cnp = gamemap.np

    adjustFactorSize = constants.getadjustFactorSize(cnp)
    adjustFactorDensity = constants.getadjustFactorDensity(cnp)
    adjustFactorCenter = constants.getadjustFactorCenter(cnp)
    adjustFactorDistance = constants.getadjustFactorDistance(cnp)
    doAdjust = 1

    # logging.info(">>>Caclulating best next planet for ship:%d" % ship.id)
    # for i in targetList:
    #     logging.info("%d, %f, %f, %f"%(i.id, i.radius, i.density_score, i.far_from_center_score))


    distAdjusted = lambda target: ship.calculate_distance_between(ship.closest_point_to(target))/ (
        target.radius ** (adjustFactorSize*doAdjust)
        * target.density_score ** (adjustFactorDensity*doAdjust)
        * target.far_from_center_score ** (adjustFactorCenter*doAdjust)
        ) + ship.calculate_distance_between(ship.closest_point_to(target)) * adjustFactorDistance / (target.radius 
        * target.density_score 
        * target.far_from_center_score )
    
    distList = np.zeros((len(targetList),2))
    distList[:,0] = np.array( list(map(distAdjusted, targetList)) )
    distList[:,1] = np.array( range(len(targetList)) )
    # logging.info(distList)
    distList = distList[distList[:,0].argsort()]
    # logging.info(distList)


    for i in range(len(targetList)):
        target = targetList[int(distList[i][1])]
        if planet_allow_new_conquer(target):
            return target
    return None


def high_value_target_planets(gamemap):

    ship = gamemap.get_me().all_ships()[0]
    entities_by_distance = gamemap.nearby_entities_by_distance(ship)
    # print(entities_by_distance.type)
    target_list = []
    for distance in sorted(entities_by_distance):
        for target in entities_by_distance[distance]:
            if isinstance(target, entity.Planet) and target.owner != gamemap.get_me():
                target_list.append(target)
    return target_list


def if_all_planet_owned(gamemap):
    # return False
    l_all_planets = gamemap.all_planets()
    all_owned = True
    for planet in l_all_planets:
        if planet.is_owned() == False:
            all_owned = False
            break
    return all_owned

# attack docking ship within given range
def attackable_docking_ship(gamemap, entity):

    closest_enemies = gamemap.distances_dict_enemy
    for (ship, dist) in closest_enemies[entity.id]:
        if (ship.docking_status == ship.DockingStatus.DOCKING or ship.docking_status == ship.DockingStatus.DOCKED) \
        and dist < constants.ATTACKING_RANGE_FOR_DOCK_SHIPS + 0.01\
        and len(ship.targeted)<constants.combat_nto1_threshold:
            return ship
    return None

def if_rush_from_beginning(game, gamemap):
    if len(game.map._players) >2:
        return False

    ships = gamemap._all_ships()
    myship = None 
    enemy_ship = None
    for ship in ships:
        if not myship and ship.owner == gamemap.get_me():
            myship = ship
        if not enemy_ship and ship.owner != gamemap.get_me():
            enemy_ship = ship
        if myship and enemy_ship:
            break
    # logging.info(myship)
    # logging.info(enemy_ship)

    my_closest_planet = closest_planets_by_distance(gamemap, myship)[0]

    if gamemap.size <= constants.RUSH_MAP_SIZE:
        return True

    # 9 is 4 turns to produce one more and 5 turns to undock all three
    if int(myship.calculate_distance_between(my_closest_planet) / constants.MAX_SPEED) + constants.RUSH_TURN_ALLOWED > int(enemy_ship.calculate_distance_between(my_closest_planet) / constants.MAX_SPEED):
        return True

    return False

def any_enemy_ship_within_range(myships, dist_dict, range_lower, range_upper = 1<<30):
    for ship in myships:
        for (shipj, distj) in dist_dict[ship.id]:
            if range_lower < distj < range_upper:
                return True
            if distj > range_upper:
                break
    return False

def if_rescuable_ally_ship(ship, closest_allies, closest_enemies, num_of_players = 2):
    for (allyship, dist) in closest_allies[ship.id]:
        if dist > constants.RESCUE_RANGE:
            break
        if len(closest_enemies[allyship.id])>0:
            enemyship = closest_enemies[allyship.id][0][0]
        if allyship.calculate_distance_between(enemyship)< constants.getSHORT_ASSESS_RANGE(num_of_players) and \
            allyship.battle_field_score < enemyship.battle_field_score:
            return allyship
    return None






