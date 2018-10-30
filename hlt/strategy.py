import logging
import abc
import math
from enum import Enum
from . import collision, constants, entity, game_map, networking
import numpy as np

def compute_planet_scores(Game_map, PlanetList):

    d = {}
    for planet in PlanetList:
        thisScore = np.sum(1.0 / planet.calculate_distance_list([pp for pp in Game_map.all_planets() if planet != pp]))
        d[planet.id] = thisScore
    # normalization
    mx = np.max(list(d.values()))
    # logging.info("planet score max %lf" % mx)

    for key in d.keys():
        d[key] /= mx

    # logging.info("planet score list normalized: " + str(d))

    for target in PlanetList:
        target.density_score = d[target.id]
        target.far_from_center_score = target.calculate_distance_between(Game_map.midPoint)+0.01