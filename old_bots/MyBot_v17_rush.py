import hlt
import logging
from hlt.tactic import *
from hlt.strategy import *
from hlt.constants import *
import time

task_priority = [
"combat", # has enemy within one step, attack if in "strong" or "balance" position, retreat if in "weak" position
"resume", # resume the previous conquer task 
"rescue", # heads to closest's week allie's cloeset availble enemy
"weak_enemy_closeby", # docked enemy or impaired enemy in middle range
"defense", # defense any incoming enemy into our terriority 
"conquer", # goes to next most valuable planet
"anyship_with_ratio", # attack cloeset enemy without limitation on n_to_1 threshold
"anyship_without_ratio" # attack cloeset enemy without limitation on n_to_1 threshold
]

game = hlt.Game("NR7-Attacker-v17")
logging.info("Starting my Settler bot!")

# When only 2 players and small map, only RUSH!
ALLOW_DOCK = False
# PRINT_ACTION_LOG = False


lt_ship_db = {}
# record last turn's enemy's ships' information

turn = -1

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    startTime = time.time()

    game_map = game.update_map()
    game_map.get_me().update_ship_database()
    game_map.update_current_info_based_in_last_turn_database(lt_ship_db)
    game_map.update_itself()

    turn += 1
    logging.info("Turn:%d"%(turn))

    compute_planet_scores(game_map, game_map.all_planets())
    freePlanet = game_map.all_free_planets()
    myPlanet = game_map.owned_planets(game_map.get_me().id)
    enemyShips = game_map._all_enemy_ships()

    potentialDockPlanet = [planet for planet in freePlanet + myPlanet if (not planet.is_full())]

    if turn == 1 and if_rush_from_beginning(game, game_map):
        ALLOW_DOCK = False

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []

    # Compute closest enemies for all ships
    closest_enemies = game_map.get_all_enemies_by_distance()

    # Let all floating ship goes to attack
    AllFreeShips = game_map.get_me().all_free_ships(sortedby = closest_enemies)
    AllDockedShips = game_map.get_me().all_docked_ships()
    AllDockingShips = game_map.get_me().all_docking_ships()
    MyNewShips = game_map.get_me().new_ships
    logging.info("Free Ships Number: "+ str(len(AllFreeShips)))
    logging.info("My New Ships Number: "+ str(len(MyNewShips)))
    logging.info("My Planet Number: "+ str(len(myPlanet)))
    # logging.info("Potential DockPlanet Number: "+ str(len(potentialDockPlanet)) + str([i.id for i in potentialDockPlanet]))
    # logging.info("List of Free Planet: " + str([i.id for i in freePlanet]))
    # logging.info("List of my Planet: " + str([i.id for i in myPlanet]))

    # Counter Rush!
    # If enemy has no planets and we have more ships than them, and they are approaching, undock all ships and forbid docking!
    if len(game_map._players)==2 and len(game_map.all_enemy_planets())==0 \
        and len(game_map.get_me().all_ships()) > len(game_map._all_enemy_ships()) and any_enemy_ship_within_range(AllDockedShips, closest_enemies, UNDOCKING_FOR_COMBAT_RANGE_LOWER, UNDOCKING_FOR_COMBAT_RANGE_UPPER):
        ALLOW_DOCK = False
        for ship in AllDockedShips+AllDockingShips:
            ship.issueCommand(ship.undock(), "Undock", None)

    # explore and conquer
    # Command each ship by priority

    for task in task_priority:

        if time.time() - startTime > TimeThreshold:
            break

        for ship in AllFreeShips:
        
            navigate_command = None

            # close combat control
            # for each free ship, first determine if there are enemy close by, and determine whether attack or rethreat based on power balance
            
            if task == "combat":
                if not ship.command and len(closest_enemies[ship.id])>0 and closest_enemies[ship.id][0][1] < COMBAT_RANGE:
                    for (enemyship, dist) in closest_enemies[ship.id]:
                        if dist >= COMBAT_RANGE: break
                        if len(enemyship.targeted) < combat_nto1_threshold:
                            enemyship.targeted.add(ship)
                            ship.issueCommand(ship.navigate(ship.closest_point_to(enemyship.predict_next_pos()),game_map), task, enemyship.id)
                            break

            # only resuming conquer task here
            if task =="resume":
                if not ship.command and (ship.assigned_task =="conquer-heading" or ship.assigned_task =="re-conquer-heading"):
                    target_planet = game_map.get_by_id_planet(ship.assigned_target_id)
                    if target_planet and planet_allow_new_conquer(target_planet):
                        target_planet.incoming_ships.add(ship)
                        if ship.can_dock(target_planet):
                            ship.issueCommand(ship.dock(target_planet), "re-conquer-docking", target_planet.id)
                        else:
                            ship.issueCommand(ship.navigate(ship.closest_point_to(target_planet),game_map), "re-conquer-heading", target_planet.id)
                if not ship.command and (ship.assigned_task =="defense" or ship.assigned_task =="re-defense"):
                    target_ship = game_map.get_by_id_ship(ship.assigned_target_id)
                    if target_ship:
                        target_ship.targeted.add(ship)
                        ship.issueCommand(ship.navigate(ship.closest_point_to(target_ship.predict_next_pos()),game_map), "re-defense", target_ship.id)

            elif task == "weak_enemy_closeby":
                if not ship.command:
                    target_ship = attackable_docking_ship(game_map, ship)
                    if target_ship:
                        target_ship.targeted.add(ship)
                        ship.issueCommand(ship.navigate(ship.closest_point_to(target_ship),game_map), task, target_ship.id)

            # defense range control
            # see if any enemy ship approaching our planet
            elif task =="defense":
                invading_ships = game_map.get_invading_ships()
                if not ship.command and len(invading_ships)>0:
                    for enemyship in invading_ships:
                        if len(enemyship.targeted) < combat_nto1_threshold:
                            enemyship.targeted.add(ship)
                            ship.issueCommand(ship.navigate(ship.closest_point_to(enemyship.predict_next_pos()),game_map), task, enemyship.id)
                            break

            # Explore new planets
            elif task =="conquer":
                if ALLOW_DOCK and not ship.command:
                    # Make sure in first turn all ships goes towards the same planet
                    target_planet = best_next_planets(game_map, ship, potentialDockPlanet)
                    if target_planet:
                        target_planet.incoming_ships.add(ship)
                        if ship.can_dock(target_planet):
                            ship.issueCommand(ship.dock(target_planet), "conquer-docking", target_planet.id)
                        else:
                            ship.issueCommand(ship.navigate(ship.closest_point_to(target_planet),game_map), "conquer-heading", target_planet.id)

            # Hunts for docked ship
            # This must be some far away ship, otherwise the control is taken by close combat

            # Hunts for any ship, keep n to 1 threshold

            elif task == "anyship_with_ratio":
                if not ship.command:
                    target_ship = closest_enemy_ship(game_map, ship)
                    if target_ship is not None:
                        target_ship.targeted.add(ship)
                        ship.issueCommand(ship.navigate(ship.closest_point_to(target_ship),game_map), task, target_ship.id)

            # Hunts for any ship, remove n to 1 threshold
            elif task == "anyship_without_ratio":
                if not ship.command:
                    target_ship = closest_enemy_ship(game_map, ship, no_limit = True)
                    if target_ship is not None:
                        target_ship.targeted.add(ship)
                        ship.issueCommand(ship.navigate(ship.closest_point_to(target_ship),game_map), task ,target_ship.id)

    command_queue = [ship.command for ship in AllFreeShips if ship.command]
    
    logging.info("Command Numebrs: "+str(len(command_queue)))
    for i in command_queue:
        logging.info(i)
    if len(command_queue) < len(game_map.get_me().all_free_ships()):
        logging.info("!!! Alert: Command less than ship number !!!")

    # Send our set of commands to the Halite engine for this turn

    logging.info("Time consumed this turn:"+ str(time.time() - startTime))

    game.send_command_queue(command_queue)

    lt_ship_db = game_map.update_last_turn_database()

    navigate_command = None
    # TURN END
# GAME END
