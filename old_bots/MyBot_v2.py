"""
Update Version:
v0: conquer unmanned planets √
v1: attack to closest enemy planet when all planets occupied √
v2: if in docking range but can't dock, aim at nearby enemy ships √
    improve collision detect from huizew √
    Search and Attack in all cases √

future features:
    when begins close enough, rush B!

"""

"""
Welcome to your first Halite-II bot!

This bot's name is Settler. It's purpose is simple (don't expect it to win complex games :) ):
1. Initialize game
2. If a ship is not docked and there are unowned planets
2.a. Try to Dock in the planet if close enough
2.b If not, go towards the planet

Note: Please do not place print statements here as they are used to communicate with the Halite engine. If you need
to log anything use the logging module.
"""
# Let's start by importing the Halite Starter Kit so we can interface with the Halite engine
import hlt
# Then let's import the logging module so we can print out information
import logging
from hlt.tactic import *

# GAME START
# Here we define the bot's name as Settler and initialize the game, including communication with the Halite engine.
game = hlt.Game("NR7-Attacker-v2")
# Then we print our start message to the logs
logging.info("Starting my Settler bot!")


# When only 2 players and small map, only RUSH!
ALLOW_DOCK = True
if game.map.width * game.map.height <= 240*160 +1 and len(game.map._players)<=2:
    ALLOW_DOCK = False

turn = 0

while True:
    # TURN START
    # Update the map for the new turn and get the latest version
    game_map = game.update_map()
    turn += 1
    logging.info("Turn:%d"%(turn))

    # Here we define the set of commands to be sent to the Halite engine at the end of the turn
    command_queue = []
    # For every ship that I control

    logging.info("Search and Attack Mode")

    planets_docked = []

    # Let all floating ship goes to attack
    AllFreeShips = game_map.get_me().all_free_ships()

    for ship in AllFreeShips:

        if ALLOW_DOCK:

            target_planet = closest_not_mine_planet(game_map, ship)
            logging.info(target_planet)
            navigate_command = None

            if target_planet:
                # in range of docking
                if ship.can_dock(target_planet):
                    # if not target_planet.is_owned():
                        # command_queue.append(ship.dock(target_planet))
                    if (not target_planet.is_owned()) and (target_planet not in planets_docked):
                        command_queue.append(ship.dock(target_planet))
                        planets_docked.append(target_planet)
                    else:
                        # attack closest ship
                        target_ship = closest_enemy_ship(game_map, target_planet)
                        if target_planet:
                            navigate_command = ship.navigate(ship.closest_point_to(target_ship),game_map)
                else:
                    navigate_command = ship.navigate(ship.closest_point_to(target_planet),game_map)
        else:
            target_ship_zero = closest_enemy_ship(game_map, AllFreeShips[0])
            navigate_command = ship.navigate(ship.closest_point_to(target_ship_zero),game_map)



        
        if navigate_command:
            command_queue.append(navigate_command)

    logging.info("Command Numebrs: "+str(len(command_queue)))
    for i in command_queue:
        logging.info(i)
    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
