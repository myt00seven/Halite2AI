import hlt
import logging
from hlt.tactic import *
from hlt.strategy import *
from hlt.constants import *
import time

task_priority = [
"combat", # has enemy within one step, attack if in "strong" or "balance" position, retreat if in "weak" position
"resume_defense", # resume the previous defense task 
"weak_enemy_closeby", # docked enemy or impaired enemy in middle range
"close_defense", # defense any close enemy
"resume_conquer", # resume the previous conquer task 
"rescue", # heads to closest's week allie's cloeset availble enemy
"conquer", # goes to next most valuable planet
"all_defense", # defense any incoming enemy into our terriority 
"anyship_with_ratio", # attack cloeset enemy with limitation on n_to_1 threshold
"anyship_without_ratio" # attack cloeset enemy without limitation on n_to_1 threshold
]

game = hlt.Game("NR7-Attacker-v24")
if PRINT_ACTION_LOG: logging.info("Starting my Settler bot!")

# When only 2 players and small map, only RUSH!
ALLOW_DOCK = True
RUSH_FROM_BEGIN = False

PRINT_ACTION_LOG = True


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
    if PRINT_ACTION_LOG: logging.info("Turn:%d"%(turn))
    # constants of  number of players
    cnp = game_map.np

    compute_planet_scores(game_map, game_map.all_planets())
    freePlanet = game_map.all_free_planets()
    myPlanet = game_map.owned_planets(game_map.get_me().id)
    enemyShips = game_map._all_enemy_ships()

    potentialDockPlanet = [planet for planet in freePlanet + myPlanet if (not planet.is_full())]

    if turn == 0 and if_rush_from_beginning(game, game_map):
        ALLOW_DOCK = False
        RUSH_FROM_BEGIN = True
        combat_nto1_threshold = 1<<10

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []

    # Compute closest enemies for all ships
    closest_enemies = game_map.get_all_enemies_by_distance()
    closest_allies = game_map.get_all_allies_by_distance()

    # Let all floating ship goes to attack
    AllFreeShips = game_map.get_me().all_free_ships(sortedby = closest_enemies)
    AllDockedShips = game_map.get_me().all_docked_ships()
    AllDockingShips = game_map.get_me().all_docking_ships()
    MyNewShips = game_map.get_me().new_ships
    if PRINT_ACTION_LOG: logging.info("Free Ships Number: "+ str(len(AllFreeShips)))
    if PRINT_ACTION_LOG: logging.info("My New Ships Number: "+ str(len(MyNewShips)))
    if PRINT_ACTION_LOG: logging.info("My Planet Number: "+ str(len(myPlanet)))
    # if PRINT_ACTION_LOG: logging.info("Potential DockPlanet Number: "+ str(len(potentialDockPlanet)) + str([i.id for i in potentialDockPlanet]))
    # if PRINT_ACTION_LOG: logging.info("List of Free Planet: " + str([i.id for i in freePlanet]))
    # if PRINT_ACTION_LOG: logging.info("List of my Planet: " + str([i.id for i in myPlanet]))
    if PRINT_ACTION_LOG: logging.info("List of enemy ships: " + str([i.id for i in enemyShips]))

    # Counter Rush!
    # If enemy has no planets and we have more ships than them, and they are approaching, undock all ships and forbid docking!
    if len(game_map._players)==2 and len(game_map.all_enemy_planets())==0 \
        and len(game_map.get_me().all_ships()) > len(game_map._all_enemy_ships())+1 and any_enemy_ship_within_range(AllDockedShips, closest_enemies, UNDOCKING_FOR_COMBAT_RANGE_LOWER, UNDOCKING_FOR_COMBAT_RANGE_UPPER):
        ALLOW_DOCK = False
        for ship in AllDockedShips+AllDockingShips:
            ship.issueCommand(ship.undock(),"undock",None)

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
                    if ship.field_score(closest_allies, closest_enemies) <= -0.75:
                        # retreat 
                        enemyship = closest_enemies[ship.id][0][0]
                        ship.issueCommand(ship.navigate(ship.keep_distance_from(enemyship, closest_enemies, closest_allies, number_of_players = cnp),game_map), "combat-retreat", enemyship.id)
                    elif -0.75< ship.field_score(closest_allies, closest_enemies) < 0:
                        enemyship = closest_enemies[ship.id][0][0]
                        enemyship.targeted.add(ship)
                        ship.issueCommand(ship.navigate(enemyship.predict_next_pos(),game_map), "combat-strike", enemyship.id)
                    else:
                        for (enemyship, dist) in closest_enemies[ship.id]:
                            if dist >= COMBAT_RANGE: break
                            if len(enemyship.targeted) < combat_nto1_threshold:
                                enemyship.targeted.add(ship)
                                ship.issueCommand(ship.navigate(ship.closest_point_to(enemyship.predict_next_pos()),game_map), task, enemyship.id)
                                break

            if task =="resume_defense" and ship.assigned_task:
                if not ship.command and ("defense" in ship.assigned_task) and (ship.assigned_target_id in enemyShips):
                    target_ship = game_map.get_by_id_ship(ship.assigned_target_id)
                    if target_ship and target_ship.health>0:
                        target_ship.targeted.add(ship)
                        ship.issueCommand(ship.navigate(ship.closest_point_to(target_ship.predict_next_pos(), grouping = True, closest_allies = closest_allies, number_of_players = cnp),game_map), "re-defense", target_ship.id)

            elif task =="close_defense":
                if not ship.command:
                    thisid = ship.id if not RUSH_FROM_BEGIN else AllFreeShips[0].id
                    for (enemyship, dist) in closest_enemies[thisid]:
                        if dist>constants.getCLOSE_DEFENSE_RANGE(cnp):
                            break
                        if len(enemyship.targeted) < combat_nto1_threshold:
                            enemyship.targeted.add(ship)
                            ship.issueCommand(ship.navigate(ship.closest_point_to(enemyship.predict_next_pos()),game_map), task, enemyship.id)
                            break

            # only resuming conquer task here
            if task =="resume_conquer" and ship.assigned_task and ALLOW_DOCK:
                if not ship.command and "conquer-heading" in ship.assigned_task:
                    target_planet = game_map.get_by_id_planet(ship.assigned_target_id)
                    if target_planet and planet_allow_new_conquer(target_planet):
                        target_planet.incoming_ships.add(ship)
                        if ship.can_dock(target_planet):
                            ship.issueCommand(ship.dock(target_planet), "re-conquer-docking", target_planet.id)
                        else:
                            ship.issueCommand(ship.navigate(ship.closest_point_to(target_planet),game_map), "re-conquer-heading", target_planet.id)

            # elif task == "weak_enemy_closeby":
            #     if not ship.command:
            #         target_ship = attackable_docking_ship(game_map, ship)
            #         if target_ship:
            #             target_ship.targeted.add(ship)
            #             ship.issueCommand(ship.navigate(ship.closest_point_to(target_ship),game_map), task, target_ship.id)

            # rescue ship in weak position
            elif task == "rescue":
                if not ship.command:
                    ally_ship = if_rescuable_ally_ship(ship, closest_allies, closest_enemies)
                    if ally_ship:
                        for (enemyship, dist) in closest_enemies[ally_ship.id]:
                            if len(enemyship.targeted) < combat_nto1_threshold:
                                enemyship.targeted.add(ship)
                                ship.issueCommand(ship.navigate(ship.closest_point_to(enemyship.predict_next_pos()),game_map), task, enemyship.id)
                                ally_ship.assisted += ship.health / constants.MAX_SHIP_HEALTH
                                break


            # Explore new planets
            elif task =="conquer" and ALLOW_DOCK:
                if ALLOW_DOCK and not ship.command:
                    # Make sure in first turn all ships goes towards the same planet
                    target_planet = best_next_planets(game_map, ship, potentialDockPlanet)
                    if target_planet:
                        target_planet.incoming_ships.add(ship)
                        if ship.can_dock(target_planet):
                            ship.issueCommand(ship.dock(target_planet), "conquer-docking", target_planet.id)
                        else:
                            ship.issueCommand(ship.navigate(ship.closest_point_to(target_planet),game_map), "conquer-heading", target_planet.id)

            # all terriorty's incoming enemy defense 
            # see if any enemy ship approaching our planet
            elif task =="all_defense":
                invading_ships = game_map.get_invading_ships()
                if not ship.command and len(invading_ships)>0:
                    for enemyship in invading_ships:
                        if len(enemyship.targeted) < combat_nto1_threshold:
                            enemyship.targeted.add(ship)
                            ship.issueCommand(ship.navigate(ship.closest_point_to(enemyship.predict_next_pos()),game_map), task, enemyship.id)
                            break

            # Hunts for docked ship
            # This must be some far away ship, otherwise the control is taken by close combat

            # Hunts for any ship, keep n to 1 threshold

            elif task == "anyship_with_ratio":
                if not ship.command:
                    for (enemyship, dist) in closest_enemies[ship.id]:
                        if len(enemyship.targeted) < combat_nto1_threshold:
                            enemyship.targeted.add(ship)
                            ship.issueCommand(ship.navigate(ship.closest_point_to(enemyship.predict_next_pos()),game_map), task, enemyship.id)
                            break

            # Hunts for any ship, remove n to 1 threshold
            elif task == "anyship_without_ratio":
                if not ship.command:
                    for (enemyship, dist) in closest_enemies[ship.id]:
                        enemyship.targeted.add(ship)
                        ship.issueCommand(ship.navigate(ship.closest_point_to(enemyship.predict_next_pos()),game_map), task, enemyship.id)
                        break
                if (time.time()-startTime > constants.TimeThreshold_2):
                    break

        if PRINT_ACTION_LOG: logging.info("Time consumed by command:\t"+ task +'\t'+ str(time.time() - startTime))


    command_queue = [ship.command for ship in AllFreeShips if ship.command]
    
    if PRINT_ACTION_LOG: logging.info("Command Numebrs: "+str(len(command_queue)))
    for i in command_queue:
        if PRINT_ACTION_LOG: logging.info(i)
    if len(command_queue) < len(game_map.get_me().all_free_ships()):
        if PRINT_ACTION_LOG: logging.info("!!! Alert: Command less than ship number !!!")

    # Send our set of commands to the Halite engine for this turn

    if PRINT_ACTION_LOG: logging.info("Time consumed this turn:"+ str(time.time() - startTime))

    game.send_command_queue(command_queue)

    lt_ship_db = game_map.update_last_turn_database()

    navigate_command = None
    # TURN END
# GAME END
