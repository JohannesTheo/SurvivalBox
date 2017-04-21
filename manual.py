import numpy as np
from evonet import EvoNet

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
              num_agents=2,
              view_port_dimensions=agent_view_port)

#nv = PLE(game, display_screen=True,
 #              fps=100,
  #             force_fps=False, 
   #            num_steps=1, 
    #           frame_skip=1, 
     #          add_noop_action=False)

game._setup()
game.init()

actions = list(game.getActions())
print("Actions: {}".format(actions))

while True:

    if game.game_over():
        game.reset()

    dt = game.tick(100)
    reward = game.step(dt)

   #print(env.getFrameNumber())
