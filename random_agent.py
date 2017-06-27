import numpy as np
from ple import PLE
from survivalbox import SurvivalBox

# ####################################################################
# GENERAL GAME CONTROL KEYS:
#
# Control-C -> QUIT GAME
# 3 -> ON/OFF observation window grid 
# 4 -> ON/OFF orientation marker
# 5 -> ON/OFF scaled map rendering if TileSize < 8
# 6 -> ON/OFF Meta Info Cards 
#
# ####################################################################

# define observation window, requires option: full_map_observation=False to be applied
agent_view_port = {
                    "grid_points_left" : 9,
                    "grid_points_right": 10,
                    "grid_points_front": 9,
                    "grid_points_back" : 10,
                  }

# general game configuration
game = SurvivalBox(grid_width =40, grid_height=40, tile_size=4, water_percentage=0.5, 
                   num_agents=1,   agent_life=500, num_sheep=1, num_wolf=1, num_fire=1,
                   turn_actions=True, view_port_dimensions=agent_view_port, full_map_observation=False,
                   always_new_map=False,  human_game=False,
                   )

# PLE configuration
env = PLE(game, display_screen=True,
                fps=20,          # maximum frames per second 
                force_fps=False, 
                num_steps=1,     # don't skip game steps
                frame_skip=1,    # don't skip frames
                add_noop_action=False) # do not add extra noop action

# Load Demo Map from current directory
game.load_map("exp1.map")

# Init Environment
env.init()

# save and print available action keys
actions = list(env.game.getActions())
print("Actions: {}".format(actions))

# game loop
while True:

    # if the game is over, reset
    if env.game_over():
        env.reset_game()

    # choose a random action
    next_action = np.random.choice(actions)
    
    # apply the action to the environment and receive the reward
    reward = env.act(next_action)

    # receive the observation for training
    observation = game.getScreenRGB()[0]
