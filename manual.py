import numpy as np
from evonet import EvoNet 
import pygame
import matplotlib.pyplot as plt

agent_view_port = {
                    "grid_points_left" : 9,
                    "grid_points_right": 9,
                    "grid_points_front": 5,
                    "grid_points_back" : 5,
                  }

game = EvoNet(grid_width =50, 
              grid_height=50,
              tile_size=8, 
              water_percentage=0.5, 
              num_agents=1,
              view_port_dimensions=agent_view_port,
              human_game=True)

#nv = PLE(game, display_screen=True,
 #              fps=100,
  #             force_fps=False, 
   #            num_steps=1, 
    #           frame_skip=1, 
     #          add_noop_action=False)

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

#game.save_map("test.map")
#game.load_map("test.map")

previous_score = 0

while True:
    if game.game_over():
        game.reset()

    dt = game.tick(100)
    game.step(dt)

    reward = game.getScore() - previous_score
    previous_score = game.getScore()
    observation = game.getScreenRGB()[0]
   
    #print(reward)
    #print(env.getFrameNumber())
