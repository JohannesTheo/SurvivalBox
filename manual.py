import numpy as np
from evonet import EvoNet 
import pygame
import matplotlib.pyplot as plt

agent_view_port = {
                    "grid_points_left" : 9,
                    "grid_points_right": 10,
                    "grid_points_front": 9,
                    "grid_points_back" : 10,
                  }

game = EvoNet(grid_width =52, 
              grid_height=52,
              tile_size=4, 
              water_percentage=0.5, 
              num_agents=1,
              view_port_dimensions=agent_view_port)

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

#game.save_map("test.map")
#game.load_map("test.map")

previous_score = 0

while True:
    if game.game_over():
        game.reset()

    dt = game.tick(30)
    game.step(dt)

    reward = game.getScore() - previous_score
    previous_score = game.getScore()
    observation = game.getScreenRGB()[0]
   
    print(reward)
    #print(env.getFrameNumber())
