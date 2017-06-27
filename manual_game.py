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
# IF OPTION: human_game=True
#
# UP, DOWN, LEFT, RIGHT -> Control Agent Movement
# COMMA, PERIOD ---------> Turn L/R: Requires also `turn_actions=True`
#
# 1 -> Scale Down TileSize
# 2 -> Scale UP   TileSize
# 7 -> Scale Down MapSize
# 8 -> Scale UP   MapSize
# 9 -> Scale Down MapHeight
# 0 -> Scale UP   MapHeight
# R -----> Reset Map       
# SPACE -> New Map:                Requires also `always_new_map=True`
# TAB ---> Switch Agent Control 
# ####################################################################


# define observation window, requires option: full_map_observation=False to be applied
agent_view_port = {
                    "grid_points_left" : 9,
                    "grid_points_right": 10,
                    "grid_points_front": 9,
                    "grid_points_back" : 10,
                  }

# general game configuration
game = SurvivalBox(grid_width =50, grid_height=50, tile_size=8, water_percentage=0.5, 
                   num_agents=3,   agent_life=700, num_sheep=1, num_wolf=1, num_fire=1,
                   turn_actions=True, view_port_dimensions=agent_view_port, full_map_observation=False,
                   always_new_map=False,  human_game=True,
                   )

# call setup manually
game._setup()

# print available action keys
actions = list(game.getActions())
print("Actions: {}".format(actions))

# init the game
game.init()

# define custom rewards and inject them
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


# set initial score to 0 
previous_score = 0

# game loop
while True:
    # if the game is over, reset
    if game.game_over():
        game.reset()
        previous_score = 0

    # control frames per second in manual mode
    dt = game.tick(20)
    # step the game forward one time step
    game.step(dt)

    # receive the reward like a RL agent
    reward = game.getScore() - previous_score
    previous_score = game.getScore()
    #print(reward)

    # receive the observation
    observation = game.getScreenRGB()[0]
