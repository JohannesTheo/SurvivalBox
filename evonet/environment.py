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
        self.dirty_sprites_group    = pygame.sprite.RenderUpdates()
        # Game Object related groups
        self.game_objects_group     = pygame.sprite.RenderUpdates()
        self.survivor_group         = pygame.sprite.RenderUpdates()

    def save_map(self, file_name, dir):
        if(self.START_MAP is None): raise Exception("No Map to save yet!")

        with open(dir + file_name, 'wb') as file:
            pickle.dump(self.START_MAP, file)

    def load_map(self, file_name, dir):

        with open(dir + file_name, 'rb') as file:
            loaded_map = pickle.load(file)
        
        self.MAPWIDTH  = loaded_map["Meta"]["width"]
        self.MAPHEIGHT = loaded_map["Meta"]["height"]
        self.WATER_PERCENTAGE = loaded_map["Meta"]["water_percentage"]

        ViewPort_Grid = self.ViewPort.get_grid_size()
        self.MAX_VIEW_PORT = np.max(ViewPort_Grid)
        self.ClippingBorder = (self.MAX_VIEW_PORT - 1) * self.TileSize
        
        self.MapSurface = pygame.Surface((self.MAPWIDTH  * self.TileSize  + 2 * self.ClippingBorder,
                                          self.MAPHEIGHT * self.TileSize  + 2 * self.ClippingBorder))

        self.create_new_map(loaded_map)

        # if scale doesnt fit scale to...
        if self.TileSize != self.START_MAP["TileMap_TileSize"]:
            self.scale_to(self.TileSize)

        # reset the game
        self.reset()

        return (self.MAPWIDTH, self.MAPHEIGHT, self.WATER_PERCENTAGE)
    

    def init(self, rng, num_agents=1, view_port_dimensions={}):

        # Set the rng
        self.rng = rng
        
        # Set the number of agents
        self.NumAgents = num_agents

        if not view_port_dimensions:
            raise Exception("Please provide a ViewPort dict in the form: {'grid_points_left':a, 'grid_points_right:b', 'grid_points_front':c, 'grid_points_back':d}")
        
        # Save the general ViewPort dimensions of the agents
        self.ViewPort = ViewPort(
                        view_port_dimensions["grid_points_left" ],
                        view_port_dimensions["grid_points_right"],
                        view_port_dimensions["grid_points_front"],
                        view_port_dimensions["grid_points_back" ])

        # Calculate the max amount of extra border for clipping our agent Views later
        ViewPort_Grid = self.ViewPort.get_grid_size()
        self.MAX_VIEW_PORT = np.max(ViewPort_Grid)
        self.ClippingBorder = (self.MAX_VIEW_PORT - 1) * self.TileSize
        
        # Create a drawing Surface
        self.MapSurface = pygame.Surface((self.MAPWIDTH  * self.TileSize  + 2 * self.ClippingBorder,
                                          self.MAPHEIGHT * self.TileSize  + 2 * self.ClippingBorder))

        # If no map is loaded create a new one based on the current settings
        if(self.START_MAP is None):
            self.create_new_map()

        # Create our Agents
        self.create_agents(self.NumAgents)

        # Reset the GameState
        self.reset()

        # Create cards for human friendly rendering interface
        self.create_cards()

    def create_agents(self, num_agents):
        self.AgentList = {}
        for ID in range(num_agents):

            start_pos = self.random_position()
            NewAgent = Survivor(ID, self.ViewPort, start_pos, self.TileSize, self.ClippingBorder)
            
            self.AgentList[ID] = { "ID" : ID, "Agent" : NewAgent, "ViewPort_Grid" : NewAgent.ViewPort.get_grid_dimensions(), "ViewPort" : None, "AgentView" : None}
            # add to groups
            self.everything_group.add(NewAgent)
            self.game_objects_group.add(NewAgent)
            self.survivor_group.add(NewAgent)

    def create_new_map(self, loaded_map=None):
        
        self.everything_group.empty()      
        self.bord_objects_group.empty()  
        self.eow_group.empty()
        self.map_group.empty()
        self.land_group.empty()
        self.water_group.empty()
        self.dirty_sprites_group.empty()

        if loaded_map:
            self.START_MAP = loaded_map
            self.TileMap   = self.START_MAP["TileMap"]
        else:
            self.TileMap, self.START_MAP = map.generate_tile_map(self.MAPWIDTH, 
                                                                 self.MAPHEIGHT, 
                                                                 self.WATER_PERCENTAGE, 
                                                                 self.TileSize, 
                                                                 self.ClippingBorder)

        # Sort all map sprites to their appropriate group
        for Tile in self.TileMap.flatten():

            # general groups
            self.everything_group.add(Tile)
            self.bord_objects_group.add(Tile)

            # eow group
            if (Tile.TileType == map.EOW):
                self.eow_group.add(Tile)
                continue

            # walkable map group
            self.map_group.add(Tile)

            # type specific groups
            if (Tile.TileType == map.WATER):
                self.water_group.add(Tile)
            else:
                self.land_group.add(Tile)
  
            
    def reset(self, new_map=False):

        self.score = 0
        
        # Reset TileMap to StartMap or create a new one
        if new_map:
            self.create_new_map()
        else:
            self.TileMap = self.START_MAP["TileMap"] # in case a new map was loaded AFTER init...
       
        # Reset all Tiles of the map 
        for Tile in self.TileMap.flatten():
            Tile.reset()
       
        # Reset all Agents
        for id in self.AgentList:
            agent = self.AgentList[id]["Agent"]
            agent.reset(self.random_position())
            self.everything_group.add(agent)
            self.game_objects_group.add(agent)
            self.survivor_group.add(agent)

        # make sure there is an initial view
        self.everything_group.draw(self.MapSurface)
        self.update_agent_views()

    def random_position(self, random_orientation=False):
        # Starting point must be between grid positions 1 and MAP w/h - 2, because of the border.             
        Start_X = self.rng.randint(1, self.MAPWIDTH  - 1)  # Lower Bound is inklusive
        Start_Y = self.rng.randint(1, self.MAPHEIGHT - 1)  # Upper Bound is exklusive
        
        if random_orientation:
            Start_O = self.rng.randint(0, 4)
            return (Start_X,Start_Y, Start_O)
        else:
            return (Start_X,Start_Y,0)
        

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

            myID = agent.ID
            ViewPort = agent.get_view()

            #print("VP: {}".format(ViewPort))
            #print("MS: {}".format(self.MapSurface.get_size()))

            for player in self.survivor_group.sprites():
                if myID != player.ID:
                    player.draw_as_ally(self.MapSurface)
                else:
                    player.draw_as_self(self.MapSurface)

            # Get the clipped View of the Agent
            ClippedView = self.MapSurface.subsurface(ViewPort) #.copy()
            
            # Rotate to fix UP view
            ClippedView = pygame.transform.rotate(ClippedView, agent.Pos[2] * 90)
            
            # Append to the list
            self.AgentList[myID]["ViewPort"]  = ViewPort.copy()
            self.AgentList[myID]["AgentView"] = ClippedView

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

        if self.game_over(): return

        # clear the drawing group
        self.dirty_sprites_group.empty()

        # update only living agents
        for agent in self.survivor_group.sprites():

            old_pos = agent.get_grid_pos()
            new_pos = agent.update(action_list)

            colliding_map_tile = self.TileMap[new_pos]
            
            if colliding_map_tile.TileType == map.EOW:
                agent.set_back()
                continue

            if colliding_map_tile.TileType == map.WATER:
                agent.CostMultiplier = Survivor.COST_MULT_WATER
            else:
                agent.CostMultiplier = Survivor.COST_MULT_LAND

            # update the Tile on the new pos
            self.TileMap[new_pos].update(self)

            # add the old position to render list
            dirty_tile = self.TileMap[old_pos]
            self.dirty_sprites_group.add(dirty_tile)
        
            '''
            tm_type = colliding_map_tile.TileType
            raw_type = self.START_MAP["RawMap"][new_pos]
            tm_start_type = self.START_MAP["TileMap"][new_pos].TileType

            tm_type = map.resources[tm_type]
            raw_type = map.resources[raw_type]
            tm_start_type = map.resources[tm_start_type]

            print("Agent @{}: {} - {} - {} <'TileMap, S_RawMap, S_TileMap'>".format(a_pos, tm_type, raw_type, tm_start_type))
            '''
            

        ###############################################################################
        # DRAW the important Stuff to generat the AgentViews: Needed always! training
        ###############################################################################     
        # Draw game objects AFTER bord objects so they are always visible

        # Draw the current map
        #self.bord_objects_group.draw(self.MapSurface)
        self.dirty_sprites_group.draw(self.MapSurface)

        # Draw Enemies etc.

        # Update the Agent Views
        self.update_agent_views()

        ###############################################################################
        # DRAW the "unimportant" Stuff for a Preview or Demo: Only when Display = True
        ###############################################################################

        # Redraw Agents for Map View 
        self.game_objects_group.draw(self.MapSurface)

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
                
    