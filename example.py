import numpy as np

from ple import PLE
from survivalbox import SurvivalBox

agent_view_port = {
                    "grid_points_left" : 9,
                    "grid_points_right": 10,
                    "grid_points_front": 9,
                    "grid_points_back" : 10,
                  }

game = SurvivalBox(grid_width =52, 
              grid_height=52,
              tile_size=4, 
              water_percentage=0.5, 
              num_agents=2,
              view_port_dimensions=agent_view_port)

env = PLE(game, display_screen=True,
                fps=100,
                force_fps=False, 
                num_steps=1, 
                frame_skip=1, 
                add_noop_action=False)
env.init()

actions = list(env.game.getActions())
print("Actions: {}".format(actions))

while True:

    if env.game_over():
        env.reset_game()

    next_action = np.random.choice(actions)
    reward = env.act(next_action)

   #print(env.getFrameNumber())
