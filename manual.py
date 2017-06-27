import numpy as np
from survivalbox import SurvivalBox 
import pygame
import matplotlib.pyplot as plt

agent_view_port = {
                    "grid_points_left" : 9,
                    "grid_points_right": 10,
                    "grid_points_front": 9,
                    "grid_points_back" : 10,
                  }

game = SurvivalBox(grid_width =50, 
                   grid_height=50,
                   tile_size=4, 
                   water_percentage=0.5, 
                   num_agents=1,
                   agent_life=500,
                   num_sheep=1,
                   num_wolf=1,
                   num_fire=1,
                   view_port_dimensions=agent_view_port,
                   turn_actions=True,
                   always_new_map=True,
                   human_game=True,
                   full_map_observation=False)


game._setup()
actions = list(game.getActions())
print("Actions: {}".format(actions))

game.init()
# def init(self, rng, num_agents=1, view_port_dimensions={}, num_sheep=0, num_wolf=0, num_fire=0):


rewards = {
            "positive":  1.0, # same as pygamewrapper
            "negative": -1.0, # same as pygamewrapper
            "tick"    :  0.0, # same as pygamewrapper
            "loss"    : -5.0, # same as pygamewrapper
            "win"     :  5.0, # same as pygamewrapper
            "grass"   :  1.0,
            "sheep"   :  1.0,
            "fire"    :  1.0,
            "wolf"    :  1.0
        }

game.adjustRewards(rewards)



previous_score = 0
while True:
    if game.game_over():
        game.reset()
        previous_score = 0

    dt = game.tick(20)
    game.step(dt)

    reward = game.getScore() - previous_score
    previous_score = game.getScore()
    observation = game.getScreenRGB()[0]
   
    #print(reward)
    #print(env.getFrameNumber())
