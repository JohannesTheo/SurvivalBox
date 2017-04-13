__author__ = 'Johannes Theodoridis'

# standard imports
import os

# third party imports
import numpy as np
import pygame
import pickle

# local imports
from .utils import ValueNoise2D
from .game_objects import Survivor, ViewPort
from .card import Card

# constans representing the different ressources
PLAYER = -1

# TILE TYPES
EOW   = 0
WATER = 1
DIRT  = 2
GRASS = 3
MUD   = 4
GRASS_GROWING = 5
TREES_GROWING = 6

resources = {0:'EOW', 1:'WATER',2:'DIRT',3:'GRASS', 4:'MUD', 5: 'GRASS_GROWING', 6: 'TREES_GROWING'}

_DIR = os.path.dirname(os.path.abspath(__file__))
textures = {
         DIRT          : pygame.image.load(os.path.join(_DIR,'assets/dirt_light.png')),
         GRASS         : pygame.image.load(os.path.join(_DIR,'assets/grass.png')),
         GRASS_GROWING : pygame.image.load(os.path.join(_DIR,'assets/grass_growing.png')),
         TREES_GROWING : pygame.image.load(os.path.join(_DIR,'assets/trees_growing.png')),
         WATER         : pygame.image.load(os.path.join(_DIR,'assets/water.png')),
         EOW           : pygame.image.load(os.path.join(_DIR,'assets/eow.png')),
         MUD           : pygame.image.load(os.path.join(_DIR,'assets/dirt.png'))
           }

def generate_tile_map(width, height, water_percentage):

    # ! WE USE column based FORTRAN ORDER so we can get grid point column x,row y of the map by array[x,y]
    TileMap = np.zeros([height, width], dtype=int, order='F')
    START_MAP = {   "TileMap" : [],
                    "Stats"   : {
                                "water" : 0,
                                "land"  : 0,
                                "dirt"  : 0,
                                "grass" : 0,
                                "total" : 0,
                                "check" : 0
                                },
                    "Meta"    : {
                                "width" : width,
                                "height": height,
                                "water_percentage": water_percentage
                                }
                }

    # procedural generation of the map
    Vc = ValueNoise2D(width=width, height=height, octaves=8)
    Vc.calculate()
    HeightMap = Vc.get_height_map()

    # intermediate reference on STAR_MAPS["stats"] for better readability of code below:
    Stats = START_MAP["Stats"]

    # Convert HightMap into a TileMap
    for row in range(height):
        for column in range(width):
            
            # EOW - end of world border
            if row == 0 or row == (height - 1) or column == 0 or column == (width -1):
            #if row < 22 or row > (height - 21) or column < 22 or column > (width -21):
                TileMap[row,column] = EOW
                continue

            # water
            if HeightMap[row,column] <= water_percentage:
                TileMap[row,column] = WATER
                Stats["water"] += 1
                continue

            # dirt
            if HeightMap[row,column] > 0.7:
                TileMap[row,column] = DIRT
                Stats["dirt"] += 1
                continue

            # grass
            if HeightMap[row,column] > water_percentage:
                TileMap[row,column] = GRASS
                Stats["grass"] += 1
                continue
            
    # make a copy of the final TileMap
    START_MAP["TileMap"] = np.copy(TileMap)

    # compute some more stats
    Stats["land"] = Stats["dirt"] + Stats["grass"]
    Stats["total"] = Stats["land"] + Stats["water"]
    Stats["check"] = (width - 2) * (height - 2) # substract the Left/Right/Top/Down EOW border (-2)

    # print the StartMaps statistics
    print("Total: {total} (check {check}) \n Water: {water} \n Land: {land} (Dirt: {dirt}, Grass: {grass})".format(
           total=Stats["total"],
           check=Stats["check"],
           water=Stats["water"],
           land =Stats["land"],
           dirt =Stats["dirt"],
           grass=Stats["grass"]))

    return (TileMap, START_MAP)


class Tile(pygame.sprite.DirtySprite):

    def __init__(self, pos_x, pos_y, tile_type, tile_size, offset):
        pygame.sprite.Sprite.__init__(self)

        # The grid positon of the tile
        self.Pos_x = pos_x
        self.Pos_y = pos_y

        # The initial TileType
        self.TileType = tile_type
        self.TileSize = tile_size
        self.Offset   = offset

        # The Tile properties based on the TileType
        if self.TileType == WATER:
            self.isFeartile = True
            self.FoodValue  = 0
        elif self.TileType == GRASS:
            self.isFeartile = True
            self.FoodValue  = 100
        else:
            self.isFeartile = False
            self.FoodValue  = 0

        # The initial Tile texture
        self.image = pygame.transform.scale(textures[self.TileType].convert(), (self.TileSize, self.TileSize))

        # Set the rendering position based on TileSize and Offset
        self.rect = self.image.get_rect()
        self.rect.x = self.Pos_x * self.TileSize + self.Offset
        self.rect.y = self.Pos_y * self.TileSize + self.Offset

    def update(self,env, dt):

        #print(self.TileType)
        # update is equivalent to act
        self.FoodValue -= 100

        if self.FoodValue <= 0 and self.TileType == GRASS:
            env.score += env.rewards["positive"]
            self.FoodValue = 0
            self.TileType = MUD
            self.scale_to(self.TileSize, self.Offset)

    def scale_to(self, tile_size, offset):

        self.TileSize = tile_size
        self.Offset = offset
        self.image = pygame.transform.scale(textures[self.TileType].convert(), (self.TileSize, self.TileSize))
        self.rect = self.image.get_rect()
        self.rect.x = self.Pos_x * self.TileSize + self.Offset
        self.rect.y = self.Pos_y * self.TileSize + self.Offset
        #print(self.rect)

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
            self.ViewPort = ViewPort()
        else:
            self.ViewPort = ViewPort(
                            view_port_dimensions["grid_points_left" ],
                            view_port_dimensions["grid_points_right"],
                            view_port_dimensions["grid_points_front"],
                            view_port_dimensions["grid_points_back" ])

        ViewPort_Grid = self.ViewPort.get_grid_size()
        self.MAX_VIEW_PORT = np.max(ViewPort_Grid)
        self.ClippingBorder = (self.MAX_VIEW_PORT - 1) * self.TileSize
        
        self.MapSurface = pygame.Surface((self.MAPWIDTH  * self.TileSize  + 2 * self.ClippingBorder,
                                          self.MAPHEIGHT * self.TileSize  + 2 * self.ClippingBorder))

        # If no map exists generate one
        if(self.TileMap is None):
            self.TileMap, self.START_MAP = generate_tile_map(self.MAPWIDTH, self.MAPHEIGHT, self.WATER_PERCENTAGE)
            
        # reuse the reset method to init groups and scale Sprites
        self.reset()
            

    def reset(self, new_map=False):

        self.score = 0
        
        # reset TileMap to StartMap or create a new one
        if new_map:
            self.TileMap, self.START_MAP = generate_tile_map(self.MAPWIDTH, self.MAPHEIGHT, self.WATER_PERCENTAGE)
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
                NewTile = Tile(column, row, TileType, self.TileSize, self.ClippingBorder) # ! column = PosX, row = posY

                # A group with all Sprites // A group with all bord objects
                self.everything_group.add(NewTile)
                self.bord_objects_group.add(NewTile)

                # A group with the border Sprites
                if (NewTile.TileType == EOW):
                    self.eow_group.add(NewTile)
                    continue

                # A group with all walkable map Sprites
                self.map_group.add(NewTile)

                if (NewTile.TileType == WATER):
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
                if ally.ID != ID:
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
            ID   = self.AgentList[agent]["ID"]
            VIEW = self.AgentList[ID]["AgentView"]
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

    def update(self, screen, dt, action_list=[]):

        # Update the Agents
        self.survivor_group.update( dt, action_list)

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
            LandTile.update(self, dt)

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
                
    