"""
SurvivalBox
This is a game for Multi Agent Reinforcement Learning (MARL)
"""
__author__ = 'Johannes Theodoridis'

# standard imports
import sys
import random

# third party imports
import numpy as np
import pygame
from   pygame.constants import *
from   ple.games.base import PyGameWrapper

# local imports
from . import environment
from .game_objects import Survivor

class SurvivalBox(PyGameWrapper):

    PIXEL_SCALES = [1, 2, 4, 8, 16]
    # RENDER_MODES
    MAP_ONLY       = 0
    MAP_CARDS      = 1
    MAP_MINI_CARDS = 2

    def __init__(self, 
                 grid_width=50, grid_height=50, tile_size=8, water_percentage=0.5, 
                 num_agents=2,  agent_life=999, view_port_dimensions={},
                 num_sheep=1,   num_wolf=1,     num_fire=1, 
                 turn_actions=False, always_new_map=False,    human_game=False, full_map_observation=True):


        if ((num_agents > 3) or (num_agents < 1)): raise Exception("Supported number of agents: 1-3. Given: %s" % num_agents)
        print("Welcome to SurvivalBox")


        # Configure available actions
        self.TURN_ACTIONS = turn_actions

        if self.TURN_ACTIONS:
            self.ACTIONS = {
                  "up":         K_UP,
                  "down":       K_DOWN,
                  "left":       K_LEFT,
                  "right":      K_RIGHT,
                  "NOOP"      : K_F15,
                  "turn_left":  K_COMMA,
                  "turn_right": K_PERIOD
                 }

            self.ActionKeyMap = {

                self.ACTIONS["up"]:    "Move Forward",
                self.ACTIONS["down"]:  "Move Backward",
                self.ACTIONS["left"]:  "Move Left",
                self.ACTIONS["right"]: "Move Right",
                self.ACTIONS["NOOP"]:  "Do nothing",
                self.ACTIONS["turn_left"]:  "Turn Left",
                self.ACTIONS["turn_right"]: "Turn Right"
            }
        else:
            self.ACTIONS = {
                  "up":         K_UP,
                  "down":       K_DOWN,
                  "left":       K_LEFT,
                  "right":      K_RIGHT,
                  "NOOP"      : K_F15
                 }

            self.ActionKeyMap = {

                self.ACTIONS["up"]:    "Move Forward",
                self.ACTIONS["down"]:  "Move Backward",
                self.ACTIONS["left"]:  "Move Left",
                self.ACTIONS["right"]: "Move Right",
                self.ACTIONS["NOOP"]:  "Do nothing"
            }

        
        # General Game Init
        self.FULL_MAP_OBSERVATION= full_map_observation
        self.MANUAL_GAME_PLAY = human_game

        self.Grid_Width  = grid_width  #+ 2 # Plus 2 for the border
        self.Grid_Height = grid_height #+ 2 # Plus 2 for the border
        self.TileSize    = tile_size
        self.WATER_PERCENTAGE = water_percentage
        
        self.NUM_AGENTS = num_agents
        self.AGENT_LIFE = agent_life
        self.NUM_SHEEP  = num_sheep
        self.NUM_WOLF   = num_wolf
        self.NUM_FIRE   = num_fire

        self.random_agent = False
        self.env = None
        self.ALWAYS_NEW_MAP = always_new_map
        self.view_port_dimensions = view_port_dimensions

        self.PlayTime = 0
        self.ActivePlayer = 0

        PyGameWrapper.__init__(self, self.Grid_Width * self.TileSize, self.Grid_Height * self.TileSize, actions=self.ACTIONS)

        self.rewards = {
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

        '''
        def __init__(self, width, height, actions={}):

            # Required fields
            self.actions = actions  # holds actions

            self.score = 0.0  # required.
            self.lives = 0  # required. Can be 0 or -1 if not required.
            self.screen = None  # must be set to None
            self.clock = None  # must be set to None
            self.height = height
            self.width = width
            self.screen_dim = (width, height)  # width and height
            self.allowed_fps = None  # fps that the game is allowed to run at.
            self.NOOP = K_F15  # the noop key
            self.rng = None

            self.rewards = {
                "positive": 1.0,
                "negative": -1.0,
                "tick": 0.0,
                "loss": -5.0,
                "win": 5.0
            }
        '''

    # Get's called py PLE.init()
    '''
    def _setup(self):
        """
        Setups up the pygame env, the display and game clock.
        """
        pygame.init()
        self.screen = pygame.display.set_mode(self.getScreenDims(), 0, 32)
        self.clock = pygame.time.Clock()
    '''

    '''
    def _setAction(self, action, last_action):
        """
        Pushes the action to the pygame event queue.
        """
        if action is None:
            action = self.NOOP

        if last_action is None:
            last_action = self.NOOP

        kd = pygame.event.Event(KEYDOWN, {"key": action})
        ku = pygame.event.Event(KEYUP, {"key": last_action})

        pygame.event.post(kd)
        pygame.event.post(ku)
    '''
    '''
    def _draw_frame(self, draw_screen):
        """
        Decides if the screen will be drawn too
        """

        if draw_screen == True:
            pygame.display.update()
    '''
    def save_map(self, file_name, dir="./"):
        self.env.save_map(file_name, dir)        

    def load_map(self, file_name, dir="./"):
        if self.env is None: raise Exception("No Environment yet, init first please!")

        self.Grid_Width, self.Grid_Height, self.WATER_PERCENTAGE = self.env.load_map(file_name, dir)
        self.screen_dim = self.env.get_screen_dimensions()
        self.screen = pygame.display.set_mode(self.getScreenDims(), 0, 32)
        
    
    def getScreenRGB(self):
        """
        Returns the current game screen in RGB format.

        Returns
        --------
        numpy uint8 array
            Returns a numpy array with the shape (width, height, 3).

        """

        #return pygame.surfarray.array3d(
        #    pygame.display.get_surface()).astype(np.uint8)
        return self.env.get_agent_views()  
    '''
    def tick(self, fps):
        """
        This sleeps the game to ensure it runs at the desired fps.
        """
        return self.clock.tick_busy_loop(fps)
    '''
    
    def adjustRewards(self, rewards):
        """

        Adjusts the rewards the game gives the agent

        Parameters
        ----------
        rewards : dict
            A dictonary of reward events to float rewards. Only updates if key matches those specificed in the init function.

        """
        for key in rewards.keys():
            if key in self.rewards:
                self.rewards[key] = rewards[key]

        if self.env.StatisticsCard is not None:
            self.env.StatisticsCard.update_static()
    '''
    def setRNG(self, rng):
        """
        Sets the rng for games.
        """

        if self.rng is None:
            self.rng = rng
    '''
    '''
    def getGameState(self):
        """
        Gets a non-visual state representation of the game.

        Returns
        -------
        dict or None
            dict if the game supports it and None otherwise.

        """
        return None
    '''
    '''
    def getScreenDims(self):
        """
        Gets the screen dimensions of the game in tuple form.

        Returns
        -------
        tuple of int
            Returns tuple as follows (width, height).

        """
        return self.screen_dim
    '''
    '''
    def getActions(self):
        """
        Gets the actions used within the game.

        Returns
        -------
        list of `pygame.constants`

        """
        return self.actions.values()
    '''

    def init(self):
        """
        This is used to initialize the game, such reseting the score, lives, and player position.

        This is game dependent.

        """
        if self.rng is None:
            self.rng = np.random.RandomState(24)

        if not self.env:
            self.env = environment.SandBoxWorld(self.Grid_Width, self.Grid_Height, self.WATER_PERCENTAGE, self.TileSize, self.rewards, self.FULL_MAP_OBSERVATION)
            self.env.init(self.rng, self.NUM_AGENTS, self.AGENT_LIFE, self.view_port_dimensions, self.NUM_SHEEP, self.NUM_WOLF, self.NUM_FIRE)

            # change this also in scale_to...
            # only change screen size if they are different from what we requested.
            self.screen_dim = self.env.get_screen_dimensions()
            self.screen = pygame.display.set_mode(self.getScreenDims(), 0, 32)

        else:
            self.env.reset(self.ALWAYS_NEW_MAP)

        #print("Init")

    def new_map(self):
        print("NEW MAP DIMENSIONS: %s x %s" % (self.Grid_Width, self.Grid_Height))
        self.env = environment.SandBoxWorld(self.Grid_Width, self.Grid_Height, self.WATER_PERCENTAGE, self.TileSize, self.rewards, self.FULL_MAP_OBSERVATION)
        self.env.init(self.rng, self.NUM_AGENTS, self.AGENT_LIFE, self.view_port_dimensions, self.NUM_SHEEP, self.NUM_WOLF, self.NUM_FIRE)

        # change this also in scale_to...
        # only change screen size if they are different from what we requested.
        self.screen_dim = self.env.get_screen_dimensions()
        self.screen = pygame.display.set_mode(self.getScreenDims(), 0, 32)
    
    def reset(self):
        """
        Wraps the init() function, can be setup to reset certain poritions of the game only if needed.
        """
        self.init()
    
    def getScore(self):
        """
        Return the current score of the game.

        Returns
        -------
        int
            The current reward the agent has received since the last init() or reset() call.
        """
        return self.env.getScore()

    def game_over(self):
        return self.env.game_over()

    def scale_to(self, tile_size):

        # Scale everything here!
        if self.MANUAL_GAME_PLAY:
            if tile_size not in SurvivalBox.PIXEL_SCALES: return
            print("New Scale: {}".format(tile_size))

            #if(tile_size <= 0 or (tile_size*self.Grid_Height) > 1920): return
            self.TileSize = tile_size
            self.env.scale_to(self.TileSize)
            self.reset_screen()
        else:
            print("RESCALING NOT ALLOWED!")
        
    def reset_screen(self):
        #self.screen.fill((0,0,0))
        self.screen_dim = self.env.get_screen_dimensions()
        self.screen = pygame.display.set_mode(self.getScreenDims(), 0, 32)

    def step(self, dt):
        """
        This method steps the game forward one step in time equal to the dt parameter. The game does not run unless this method is called.

        Parameters
        ----------
        dt : integer
            This is the amount of time elapsed since the last frame in milliseconds.

        """
        self.PlayTime += dt / 1000

        # Print some basic info in window title
        text = "FPS: {0:.2f}   Playtime: {1:.2f}".format(self.clock.get_fps(), self.PlayTime)
        #text = "FPS: {0:.2f}".format(clock.get_fps())
        pygame.display.set_caption(text)
        
        # get all user events
        action_list = []

        # if random agent is activated choose Actions for every agent
        self.random_agent = False
        if self.random_agent:
            action_list = [np.random.choice(list( self.ACTIONS.values())) for i in range(self.NUM_AGENTS)]
        else:
            action_list = [self.ACTIONS["NOOP"] for i in range(self.NUM_AGENTS)]

        for event in pygame.event.get():
            #print(event)
            if event.type == QUIT:
                # end the game and close the window
                pygame.quit()
                sys.exit()
            elif event.type == KEYDOWN:

                # general game controls  
                if event.key == K_2:
                    print("Scale UP")
                    self.scale_to(self.TileSize * 2)
                elif event.key == K_1:
                    print("Scale DOWN")
                    self.scale_to(int(self.TileSize / 2))
                elif event.key == K_3:
                    print("Grid ON/OFF")
                    self.env.toggle_view_area()
                elif event.key == K_4:
                    print("Marker ON/OFF")
                    self.env.toggle_marker()
                elif event.key == K_5:
                    print("Scaled Map ON/OFF")
                    self.env.toggle_scaled_map()
                    self.reset_screen()
                elif event.key == K_6:
                    print("Cards ON/OFF")
                    self.env.toggle_cards()
                    self.reset_screen()
                elif event.key == K_SPACE:
                    if self.MANUAL_GAME_PLAY:
                        print("NEW MAP/RESET MAP")
                        self.env.reset(self.ALWAYS_NEW_MAP)
                        #self.random_agent = not self.random_agent
                elif event.key == K_r:
                    if self.MANUAL_GAME_PLAY:
                        print("RESET MAP")
                        self.env.reset()
                elif event.key == K_TAB:
                    self.ActivePlayer += 1
                    if self.ActivePlayer >= self.NUM_AGENTS:
                        self.ActivePlayer = 0

                    self.env.set_active_agent(self.ActivePlayer)
                    # env activate player....

                # If it is a human game, allow for manual resize of map dimenisons
                if self.MANUAL_GAME_PLAY:
                    if event.key == K_7:
                        self.Grid_Width  -= 5
                        self.Grid_Height -= 5

                        if self.Grid_Width < 10:
                            self.Grid_Width = 10
                        if self.Grid_Height < 10:
                            self.Grid_Height = 10
                        self.new_map()
                    if event.key == K_8:
                        self.Grid_Width += 5
                        self.Grid_Height += 5
                        self.new_map()
                    elif event.key == K_9:
                        self.Grid_Height -= 5
                        if self.Grid_Height < 10:
                            self.Grid_Height = 10
                        self.new_map()
                    elif event.key == K_0:
                        self.Grid_Height += 5
                        self.new_map()   

                # manual control only if no random agent is acting
                if not self.random_agent:

                    # Pass the action to the active agent
                    if event.key == K_UP:
                        action_list[self.ActivePlayer] = self.ACTIONS["up"]
                        #print("MOVE FORWARD")
                    elif event.key == K_DOWN:
                        action_list[self.ActivePlayer] = self.ACTIONS["down"]
                        #print("MOVE BACKWARD")
                    elif event.key == K_LEFT:
                        action_list[self.ActivePlayer] = self.ACTIONS["left"]
                        #print("MOVE LEFT")
                    elif event.key == K_RIGHT:
                        action_list[self.ActivePlayer] = self.ACTIONS["right"]
                        #print("MOVE RIGHT")
                    elif event.key == K_COMMA:
                        if self.TURN_ACTIONS:
                            action_list[self.ActivePlayer] = self.ACTIONS["turn_left"]
                            #print("TURN LEFT")
                    elif event.key == K_PERIOD:
                        if self.TURN_ACTIONS:
                            action_list[self.ActivePlayer] = self.ACTIONS["turn_right"]
                            #print("TURN RIGHT")
                    else:
                        action_list[self.ActivePlayer] = self.ACTIONS["NOOP"]              
                
        
        self.env.update(self.screen, action_list)
        
        # While developing update display here, later automatic from _draw_frame
        if self.MANUAL_GAME_PLAY:
            pygame.display.update()
