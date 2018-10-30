"""
Update Version:
v0: conquer unmanned planets √

v1: attack to closest enemy planet when all planets occupied √

v2: if in docking range but can't dock, aim at nearby enemy ships √
    improve collision detect from huizew √
    Search and Attack in all cases √

v3: first priority attack docking/docked ships within 84 units √
    timeout control √

v4: Improve judge starting with rush with distance threshold
    - before docking, if enemy exists nearby, don't dock -> attack enemy ship (not best choice but still better than docking )
    - count rush (undock all and charge)
    - simple close combat, attack nearby enemies

v5: 
    - better planet finding 
    - redock within safe redock distance and with prob.


tactics features:
    - active combat with incoming ships (2vs1)


future features:
    - penalize distance of planets for four players
    - differnt hunting range for 2p and 4p (play more conservative for 4p)
    - dock more when 4p
    - keep in group when rush
    - new ships dock with probability
    - follow enemy ship to see what they are doing
    - build defense area, first attack the shiping coming into my defence area
    - run away when getting chased
    - have a call for help stack, each ship can call for backup when facing more enemy
    - when new ship is built, first see if somewhere needs backup, then check if should redock

Some idea:
    - For close combat, compute the power balance between our side and all enemy's side in a small range (maybe use 2D segment tree to accelerate the computation), if in favor of us, then attack, otherwise 
    - Compute a threat level for each of enemy ship by summing the inverse of distance of it to all our estate. 
    - maybe track all entity's movement between terms, it make it easier for prediction

"""

import hlt
import logging
from hlt.tactic import *
from hlt.strategy import *
from hlt.constants import *
import time

game = hlt.Game("NR7-Attacker-v4")
logging.info("Starting my Settler bot!")

# When only 2 players and small map, only RUSH!
ALLOW_DOCK = True
PRINT_ACTION_LOG = False

turn = 0

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    startTime = time.time()

    game_map = game.update_map()
    game_map.get_me().update_ship_database()

    turn += 1
    logging.info("Turn:%d"%(turn))

    if turn == 1 and if_rush_from_beginning(game, game_map):
        ALLOW_DOCK = False

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    # For every ship that I control

    logging.info("Search and Attack Mode")

    planets_docked = []

    # Let all floating ship goes to attack
    AllFreeShips = game_map.get_me().all_free_ships()
    AllDockedShips = game_map.get_me().all_docked_ships()
    AllDockingShips = game_map.get_me().all_docking_ships()

    MyNewShips = game_map.get_me().new_ships

    logging.info("Free Ships Number: "+ str(len(AllFreeShips)))
    # logging.info("My Planet Number: "+ str(len(AllFreeShips)))

    closest_enemies = game_map.get_all_enemies_by_distance()

    # Counter Rush!
    # If enemy has no planets and we have more ships than them, and they are approaching, undock and battle!
    if len(game_map._players)==2 and len(game_map.all_enemy_planets())==0 \
        and len(game_map.get_me().all_ships()) > len(game_map._all_enemy_ships()) and any_enemy_ship_within_range(AllDockedShips, closest_enemies, UNDOCKING_FOR_COMBAT_RANGE_LOWER, UNDOCKING_FOR_COMBAT_RANGE_UPPER):
        ALLOW_DOCK = False
        for ship in AllDockedShips+AllDockingShips:
            navigate_command = ship.undock()
            if navigate_command and not ship.ordered:
                ship.ordered = True
                command_queue.append(navigate_command)


    # close combat control
    # for each free ship, first determine if there are enemy close by, and determine whether attack or rethreat based on power balance
    for ship in AllFreeShips:
        if ship.ordered: continue
        navigate_command = None
        if len(closest_enemies[ship.id])>0 and closest_enemies[ship.id][0][1] < COMBAT_RANGE:
            target_ship = closest_enemies[ship.id][0][0]
            navigate_command = ship.navigate(ship.closest_point_to(target_ship),game_map)
            if navigate_command and not ship.ordered:
                command_queue.append(navigate_command)
                AllFreeShips.remove(ship)
                ship.ordered = True

    # for new ships:
        # if ready to counter rush, dont move
        # redock when condition is met

    # for all freeships: defense incoming enemy ships
        # remove ship from AllFreeShips after being called to defence

    # explore and conquer
    for ship in AllFreeShips:
        if PRINT_ACTION_LOG: 
            logging.info("Action of Ship:"+str(ship.id))

        if time.time() - startTime > TimeThreshold:
            break

        if ship.ordered:
            continue

        navigate_command = None
        target_ship = attackable_docking_ship(game_map, ship)

        if target_ship:
            navigate_command = ship.navigate(ship.closest_point_to(target_ship),game_map)
            if navigate_command:                
                if PRINT_ACTION_LOG: 
                    logging.info("Hunts Docking Ship")
                command_queue.append(navigate_command)
                continue

        if ALLOW_DOCK:

            # Make sure in first turn all ships goes towards the same planet
            if turn == 1:
                target_planet = closest_not_mine_planet(game_map, AllFreeShips[0])
            else:
                target_planet = closest_not_mine_planet(game_map, ship)
            # logging.info(target_planet)

            if target_planet:
                if PRINT_ACTION_LOG: 
                    logging.info("Has a target planet")
                # if in range of docking or have enemy near by
                close_by_enemies = game_map.enemies_near_target(target_planet, DOCKING_TIME_RANGE)

                # attack enemies near target planet
                if len(close_by_enemies)>0:
                    if PRINT_ACTION_LOG: 
                        logging.info("Heads for enemy near target planet")
                    navigate_command = ship.navigate(ship.closest_point_to(close_by_enemies[0]),game_map)

                elif ship.can_dock(target_planet):
                    logging.info(planets_docked)
                    if (not target_planet.is_owned()) and ((target_planet not in planets_docked) or len(planets_docked) <= 2):
                        navigate_command = ship.dock(target_planet)
                        if navigate_command and target_planet not in planets_docked:
                            if PRINT_ACTION_LOG: 
                                logging.info("Docking")
                            planets_docked.append(target_planet)
                    else:
                        # attack closest ship
                        target_ship = closest_enemy_ship(game_map, target_planet)
                        if target_planet:
                            if PRINT_ACTION_LOG: 
                                logging.info("Can't Dock, heads to closest enemy")
                            navigate_command = ship.navigate(ship.closest_point_to(target_ship),game_map)
                else:
                    if PRINT_ACTION_LOG: 
                        logging.info("Heading to the planet")
                    navigate_command = ship.navigate(ship.closest_point_to(target_planet),game_map)
        else:
            if PRINT_ACTION_LOG: 
                logging.info("RUSH MODE, NO DOCKING")
            target_ship_zero = closest_enemy_ship(game_map, AllFreeShips[0])
            navigate_command = ship.navigate(ship.closest_point_to(target_ship_zero),game_map)
        
        if navigate_command:
            command_queue.append(navigate_command)

    logging.info("Command Numebrs: "+str(len(command_queue)))
    for i in command_queue:
        logging.info(i)
        if i == None:
            command_queue.remove(i)
    # Send our set of commands to the Halite engine for this turn
    
    game.send_command_queue(command_queue)
    navigate_command = None
    # TURN END
# GAME END
