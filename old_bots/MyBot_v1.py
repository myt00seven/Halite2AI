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
game = hlt.Game("NR7-Settler")
# Then we print our start message to the logs
logging.info("Starting my Settler bot!")

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

    if if_all_planet_owned(game_map):
        # Into Attack Mode
        logging.info("Attack Mode")

        # Let all full planets send half ships out
        # for planet in game_map.all_planets():
        #     # logging.info(planet)
        #     if planet.owner == game_map.get_me():
        #         ships = planet.all_docked_ships()
        #         for i in range(0,len(ships)>>1):
        #             ship = ships[i]
        #             ship.undock()


        # Let all floating ship goes to attack
        for ship in game_map.get_me().all_ships():

            if ship.docking_status == ship.DockingStatus.UNDOCKED:
                
                target_planet = closest_enemy_planet(game_map, ship)

                if target_planet:
                    if ship.can_dock(target_planet):
                        navigate_command = ship.navigate_ori(
                            target_planet,
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=True)
                    else:
                        navigate_command = ship.navigate_ori(
                            ship.closest_point_to(target_planet),
                            game_map,
                            speed=int(hlt.constants.MAX_SPEED),
                            ignore_ships=True)
                    if navigate_command:
                        command_queue.append(navigate_command)

    else:
        # Settler Mode
        logging.info("Settler Mode")

        for ship in game_map.get_me().all_ships():
            # If the ship is docked
            if ship.docking_status != ship.DockingStatus.UNDOCKED:
                # Skip this ship
                continue

            # entities_by_distance = game_map.nearby_entities_by_distance(ship)
            # nearest_planet = None
            # for distance in sorted(entities_by_distance):
            #     nearest_planet = next( (nearest_entity for nearest_entity in entities_by_distance[distance] if isinstance(nearest_entity, hlt.entity.Planet)) , None )

            target_list = closest_planets_by_distance(game_map, ship)
            # logging.info("len of target_list:"+ str(len(target_list)))
            for planet in target_list:

                # If the planet is owned
                if planet.is_owned():
                    continue

                if ship.can_dock(planet):
                    command_queue.append(ship.dock(planet))
                else:
                    navigate_command = ship.navigate_ori(
                        ship.closest_point_to(planet),
                        game_map,
                        speed=int(hlt.constants.MAX_SPEED),
                        ignore_ships=True)
                    if navigate_command:
                        command_queue.append(navigate_command)
                break


    # Send our set of commands to the Halite engine for this turn
    game.send_command_queue(command_queue)
    # TURN END
# GAME END
