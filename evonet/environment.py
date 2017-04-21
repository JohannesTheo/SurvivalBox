__author__ = 'Johannes Theodoridis'

# standard imports

# third party imports
import numpy as np
import pygame
import pickle

# local imports
from . import map
from .game_objects import Survivor, ViewPort
from .card import Card


class EvoWorld():
    '''
    A class that holds the GameState in:
    TileMap, AgentList
    Applies dynamics based on agent actions and
    can render the World State as well as the Agent Views
    '''
   
    def __init__(self, map_width, map_height, water_percentage, init_tile_size):
        
        self.MAPWIDTH = map_width
        self.MAPHEIGHT = map_height
        self.WATER_PERCENTAGE = water_percentage

        # The actual world map (GameState) as a 2D array
        self.TileMap = None
        # A dict holding the inital state of the world
        self.START_MAP = None
        # The map surface to draw the maps state
        self.MapSurface = pygame.Surface((0,0))
        # The pixel of a single grid tile, used for drawing the game state
        self.TileSize = init_tile_size
        # An extra Clipping border based on the Agents max ViewPort
        self.MAX_VIEW_PORT    = 0
        self.VIEW_PORT_GRID_W = 0
        self.VIEW_PORT_GRID_H = 0
        self.ClippingBorder   = 0

        self.score = 0
        self.rewards = {
            "positive": 1.0,
            "negative": -1.0,
            "tick": 0.0,
            "loss": -5.0,
            "win": 5.0
        }

        self.NumAgents = 0
        self.AgentList = {}
        self.CardList  = {}
        self.CardBorder = 0
        self.rng = None
        self.ActivePlayer = 0
        

        # Some helpful sprite groups which we can use for drawing and collison detection
        self.everything_group       = pygame.sprite.RenderUpdates()
        # Map related groups
        self.bord_objects_group     = pygame.sprite.RenderUpdates()
        self.eow_group              = pygame.sprite.RenderUpdates()
        self.map_group              = pygame.sprite.RenderUpdates()
        self.land_group             = pygame.sprite.RenderUpdates()
        self.water_group            = pygame.sprite.RenderUpdates()
        # Game Object related groups
        self.game_objects_group     = pygame.sprite.RenderUpdates()
        self.survivor_group         = pygame.sprite.RenderUpdates()

    def save_map(self, file_name, dir):
        if(self.START_MAP is None): raise Exception("No Map to save yet!")

        with open(dir + file_name, 'wb') as file:
            pickle.dump(self.START_MAP, file)

    def load_map(self, file_name, dir):

        with open(dir + file_name, 'rb') as file:
            self.START_MAP = pickle.load(file)
        
        self.MAPWIDTH  = self.START_MAP["Meta"]["width"]
        self.MAPHEIGHT = self.START_MAP["Meta"]["height"]
        self.WATER_PERCENTAGE = self.START_MAP["Meta"]["water_percentage"]

        ViewPort_Grid = self.ViewPort.get_grid_size()
        self.MAX_VIEW_PORT = np.max(ViewPort_Grid)
        self.ClippingBorder = (self.MAX_VIEW_PORT - 1) * self.TileSize
        
        self.MapSurface = pygame.Surface((self.MAPWIDTH  * self.TileSize  + 2 * self.ClippingBorder,
                                          self.MAPHEIGHT * self.TileSize  + 2 * self.ClippingBorder))

        self.reset()
        return (self.MAPWIDTH, self.MAPHEIGHT, self.WATER_PERCENTAGE)
    

    def init(self, rng, num_agents=1, view_port_dimensions={}):

        # Set the rng
        self.rng = rng
        
        # Set the number of agents
        self.NumAgents = num_agents

        if not view_port_dimensions:
            raise Exception("Please provide a ViewPort dict in the form: {'grid_points_left':a, 'grid_points_right:b', 'grid_points_front':c, 'grid_points_back':d}")
        
        self.ViewPort = ViewPort(
                        view_port_dimensions["grid_points_left" ],
                        view_port_dimensions["grid_points_right"],
                        view_port_dimensions["grid_points_front"],
                        view_port_dimensions["grid_points_back" ])

        # Calculate the max amount of extra border for clipping our agent Views later
        ViewPort_Grid = self.ViewPort.get_grid_size()
        self.MAX_VIEW_PORT = np.max(ViewPort_Grid)
        self.ClippingBorder = (self.MAX_VIEW_PORT - 1) * self.TileSize
        
        self.MapSurface = pygame.Surface((self.MAPWIDTH  * self.TileSize  + 2 * self.ClippingBorder,
                                          self.MAPHEIGHT * self.TileSize  + 2 * self.ClippingBorder))

        # If no map exists generate one
        if(self.START_MAP is None):
            self.TileMap, self.START_MAP = map.generate_tile_map(self.MAPWIDTH, self.MAPHEIGHT, self.WATER_PERCENTAGE)
            
        # reuse the reset method to init groups and scale Sprites
        self.reset()
            

    def reset(self, new_map=False):

        self.score = 0
        
        # reset TileMap to StartMap or create a new one
        if new_map:
            self.TileMap, self.START_MAP = map.generate_tile_map(self.MAPWIDTH, self.MAPHEIGHT, self.WATER_PERCENTAGE)
        else:
            self.TileMap = self.START_MAP["TileMap"].copy()
        
        # Empty all groups, wasteful, could be done better by reuse or reset...
        self.everything_group.empty()      
        self.bord_objects_group.empty()  
        self.eow_group.empty()
        self.map_group.empty()
        self.land_group.empty()
        self.water_group.empty()
        self.game_objects_group.empty()
        self.survivor_group.empty()

        # Create all Map related Sprites
        for column in range(self.MAPWIDTH):
            for row in range(self.MAPHEIGHT):
            
                TileType = self.TileMap[column, row]
                NewTile = map.Tile(column, row, TileType, self.TileSize, self.ClippingBorder) # ! column = PosX, row = posY

                # A group with all Sprites // A group with all bord objects
                self.everything_group.add(NewTile)
                self.bord_objects_group.add(NewTile)

                # A group with the border Sprites
                if (NewTile.TileType == map.EOW):
                    self.eow_group.add(NewTile)
                    continue

                # A group with all walkable map Sprites
                self.map_group.add(NewTile)

                if (NewTile.TileType == map.WATER):
                    self.water_group.add(NewTile)
                else:
                    self.land_group.add(NewTile)

        # Create GameObjects related Sprites
        self.AgentList = {}
        for ID in range(self.NumAgents):

            # Starting point must be between grid positions 1 and MAP w/h - 2, because of the border.             
            Start_X = self.rng.randint(1, self.MAPWIDTH  - 1)  # Lower Bound is inklusive
            Start_Y = self.rng.randint(1, self.MAPHEIGHT - 1)  # Upper Bound is exklusive
            Start_O = self.rng.randint(0, 4)
            Start_O = 0

            NewAgent = Survivor(ID, self.ViewPort, Start_X, Start_Y, Start_O, self.TileSize, self.ClippingBorder)
            
            self.everything_group.add(NewAgent)
            self.game_objects_group.add(NewAgent)
            self.survivor_group.add(NewAgent)
            self.AgentList[ID] = { "ID" : ID, "Agent" : NewAgent, "ViewPort_Grid" : NewAgent.ViewPort.get_grid_dimensions(), "ViewPort" : None, "AgentView" : None}

        # Draw the initial map and create the first agent views
        self.everything_group.draw(self.MapSurface)
        self.update_agent_views()
        self.create_cards()

    def create_cards(self):
        self.CardList  = {}
        self.CardBorder = 30
        for agent in self.AgentList:
            ID = self.AgentList[agent]["ID"]
            self.CardList[ID] = Card(self.AgentList[agent],
                                     self.MAPHEIGHT, 
                                     self.TileSize)

    def get_screen_dimensions(self):
        width  = self.MapSurface.get_width()
        height = self.MapSurface.get_height()

        if(self.TileSize < 8):
            w = (self.MAPWIDTH  * 8) + (2 * (self.MAX_VIEW_PORT - 1) * 8)
            h = (self.MAPHEIGHT * 8) + (2 * (self.MAX_VIEW_PORT - 1) * 8)
            height += h
            width = w

        for card in self.CardList:
            width += self.CardList[card].get_width()
            width += self.CardBorder
            card_h = self.CardList[card].get_height()
            if card_h >= height:
                height = card_h + 2 * self.ClippingBorder



        return (width, height)

    def scale_to(self, tile_size):

        # Set the new TileSize
        self.TileSize = tile_size

        self.ClippingBorder = (self.MAX_VIEW_PORT - 1) * self.TileSize
        print("MAX ViewPort Gird: {} TileSise: {} ClippingBorder: {}".format(self.MAX_VIEW_PORT, self.TileSize, self.ClippingBorder))

        # Scale all Sprites to new Size 
        for sprite in self.everything_group.sprites():
            sprite.scale_to(self.TileSize, self.ClippingBorder)

        print("ClippingBorder: {}".format(self.ClippingBorder))
        # Create/Recreate a Surface for our map
        self.MapSurface = pygame.Surface((self.MAPWIDTH  * self.TileSize  + 2 * self.ClippingBorder,
                                          self.MAPHEIGHT * self.TileSize  + 2 * self.ClippingBorder))

        self.everything_group.draw(self.MapSurface)
        self.update_agent_views()
        self.create_cards()

    def update_agent_views(self):

        for agent in self.survivor_group.sprites():

            ID = agent.ID
            ViewPort = agent.get_view()

            #print("VP: {}".format(ViewPort))
            #print("MS: {}".format(self.MapSurface.get_size()))

            self.survivor_group.draw(self.MapSurface)
            for ally in self.survivor_group.sprites():
                if ally.ID != agent.ID:
                    ally.draw_as_ally(self.MapSurface)

            # Get the clipped View of the Agent
            ClippedView = self.MapSurface.subsurface(ViewPort) #.copy()
            
            # Rotate to fix UP view
            ClippedView = pygame.transform.rotate(ClippedView, agent.Pos[2] * 90)
            
            # Append to the list
            self.AgentList[ID]["ViewPort"]  = ViewPort.copy()
            self.AgentList[ID]["AgentView"] = ClippedView

    def get_agent_views(self):
        views = []
        for agent in self.AgentList:
            #   = self.AgentList[agent]["ID"]
            VIEW = self.AgentList[agent]["AgentView"]
            views.append( pygame.surfarray.array3d(VIEW).astype(np.uint8))
        return views
        
    def game_over(self):
        # Game Over if all Agents are Dead
        survivors = self.survivor_group.sprites()
        return not survivors

    def getScore(self):
        return self.score

    def set_active_agent(self, agent):
        self.ActivePlayer = agent

    def update(self, screen, action_list):

        # update the agents by index
        self.survivor_group.update(action_list)
            
        if self.game_over(): return

        
        # Collision can be simplified a lot by using grid positions directly instead of rects.
        
        # Apply Game Logic
        CollideEOW = pygame.sprite.groupcollide(self.survivor_group, self.eow_group, False, False)
        #print(CollideEOW)
        for agent in CollideEOW:
            agent.set_back()

        CollideFood = pygame.sprite.groupcollide(self.land_group, self.survivor_group, False, False)
        #print(CollideFood)
        for LandTile in CollideFood:
            LandTile.update(self)

        for agent in self.survivor_group.sprites():
            agent.CostMultiplier = Survivor.COST_MULT_LAND

        CollideWater = pygame.sprite.groupcollide(self.survivor_group, self.water_group, False, False)
        if CollideWater:
            for agent in CollideWater:
                agent.CostMultiplier = Survivor.COST_MULT_WATER
        
        ###############################################################################
        # DRAW the important Stuff to generat the AgentViews: Needed always! training
        ###############################################################################     
        # Draw game objects AFTER bord objects so they are always visible

        # Draw the current map
        self.bord_objects_group.draw(self.MapSurface)

        # Draw Enemies etc.

        # Update the Agent Views
        self.update_agent_views()

        # Redraw Agents for Map View 
        self.game_objects_group.draw(self.MapSurface)
     

        ###############################################################################
        # DRAW the "unimportant" Stuff for a Preview or Demo: Only when Display = True
        ###############################################################################

        # Draw the full MapSurface to our Main Game Screen
        #screen.blit(self.MapSurface,( -self.ClippingBorder, -self.ClippingBorder))

        if(self.TileSize < 8):

                #self.ClippingBorder = (self.MAX_VIEW_PORT - 1) * self.TileSize

            w = (self.MAPWIDTH  * 8) + (2 * (self.MAX_VIEW_PORT - 1) * 8)
            h = (self.MAPHEIGHT * 8) + (2 * (self.MAX_VIEW_PORT - 1) * 8)
            HugeMap = pygame.transform.scale(self.MapSurface, (w,h))
            screen.blit(HugeMap,(0,0))
            screen.blit(self.MapSurface, (((self.MAX_VIEW_PORT - 1) * 8)- self.ClippingBorder, h))
            
            # Draw a ViewPort representation
            for agent in self.AgentList:

                # Scaled

                Offset = (self.MAX_VIEW_PORT - 1) * 8
                Pos = self.AgentList[agent]["Agent"].Pos
                VP_scaled = self.AgentList[agent]["Agent"].ViewPort.get_viewport(Pos, 8, Offset)
                pygame.draw.rect(screen, (0,0,255), VP_scaled, 2)
                marker_scaled = self.AgentList[agent]["Agent"].get_marker_rect(Pos, 8, Offset)
                pygame.draw.rect(screen, (228,228,228), marker_scaled)

                # Minimap
                VP = self.AgentList[agent]["ViewPort"]
                VP.y += h 
                VP.x += ((self.MAX_VIEW_PORT - 1) * 8)- self.ClippingBorder
                marker = self.AgentList[agent]["Agent"].get_marker()
                marker.y += h
                marker.x += ((self.MAX_VIEW_PORT - 1) * 8)- self.ClippingBorder
                pygame.draw.rect(screen, (0,0,255), VP, 2)
                pygame.draw.rect(screen, (228,228,228), marker)

            # Draw per Agent Card Info
            for card in self.CardList:
                if card == self.ActivePlayer: 
                    active = True
                else:
                    active = False

                self.CardList[card].update(active)
                #screen.blit(self.CardList[card],( self.MapSurface.get_width() - self.ClippingBorder + self.CardList[card].get_width() * card + card * self.CardBorder, 0))
                screen.blit(self.CardList[card],( w + self.CardList[card].get_width() * card + card * self.CardBorder, (self.MAX_VIEW_PORT - 1) * 8))
        else:
            screen.blit(self.MapSurface,( 0, 0))
            # Draw a ViewPort representation
            for agent in self.AgentList:
                pygame.draw.rect(screen, (0,0,255), self.AgentList[agent]["ViewPort"], 2)
                pygame.draw.rect(screen, (228,228,228), self.AgentList[agent]["Agent"].get_marker())

            # Draw per Agent Card Info
            for card in self.CardList:
                if card == self.ActivePlayer: 
                    active = True
                else:
                    active = False

                self.CardList[card].update(active)
                #screen.blit(self.CardList[card],( self.MapSurface.get_width() - self.ClippingBorder + self.CardList[card].get_width() * card + card * self.CardBorder, 0))
                screen.blit(self.CardList[card],( self.MapSurface.get_width() + self.CardList[card].get_width() * card + card * self.CardBorder, self.ClippingBorder))
                
    