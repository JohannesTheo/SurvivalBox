__author__ = 'Johannes Theodoridis'

# standard imports
import os

# third party imports
import numpy as np
import pygame

# local imports
from .utils import ValueNoise2D
from .game_objects import Survivor, Sheep

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


resources = {EOW:'EOW', WATER:'WATER', DIRT:'DIRT', GRASS:'GRASS', MUD:'MUD', GRASS_GROWING: 'GRASS_GROWING', TREES_GROWING: 'TREES_GROWING'}

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

def parse_height_map(width, height, water_percentage, height_map):
    '''
    Converts a value noise height map in a meaningful environment.
    This is the place to define or change the map characteristics.
    '''
    #print(height_map, height_map.shape)
    RawMap  = np.zeros([width, height], dtype=int, order='F')
    statistics = {"water" : 0, "land"  : 0, "dirt"  : 0, "grass" : 0, "total" : 0, "check" : 0}

    #Convert HightMap into a TileMap
    for row in range(width):
        for column in range(height):
            
            # EOW - end of world border
            if row == 0 or row == (width - 1) or column == 0 or column == (height -1):
            #if row < 22 or row > (height - 21) or column < 22 or column > (width -21):
                RawMap[row,column] = EOW
                continue

            # water
            if height_map[row,column] <= water_percentage:
                RawMap[row,column] = WATER
                statistics["water"] += 1
                continue

            # dirt
            if height_map[row,column] > 0.7:
                RawMap[row,column] = DIRT
                statistics["dirt"] += 1
                continue

            # grass
            if height_map[row,column] > water_percentage:
                RawMap[row,column] = GRASS
                statistics["grass"] += 1
                continue

    # compute some more stats
    statistics["land"]  = statistics["dirt"] + statistics["grass"]
    statistics["total"] = statistics["land"] + statistics["water"]
    statistics["check"] = (width - 2) * (height - 2) # substract the Left/Right/Top/Down EOW border (-2)

    return RawMap, statistics

def convert_raw_map(width, height, raw_map, tile_size, clipping_border):
    '''
    Converts a the raw terrain information of the raw map into pygame sprite objects with appropriate scale and position
    '''
    TileMap = np.zeros([width, height], dtype=object, order='F')
    for row in range(width):
        for column in range(height):
        
            TileType = raw_map[row, column]
            NewTile = Tile(row, column, TileType, tile_size, clipping_border)
            TileMap[row, column] = NewTile

    return TileMap

def generate_tile_map(width, height, water_percentage, tile_size, clipping_border):

    # ! WE USE column based FORTRAN ORDER so we can get grid point column x,row y of the map by array[x,y]
    #RawMap  = np.zeros([height, width], dtype=int, order='F')
    #TileMap = np.zeros([height, width], dtype=int, order='F')

    START_MAP = {   "TileMap"   : [],
                    "TileMap_TileSize" : tile_size,
                    "HeigthMap" : [],
                    "RawMap"    : [],
                    "Description" : resources,
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

    # parse the hight map and create terrain
    RawMap, Stats = parse_height_map(width, height, water_percentage, HeightMap)
    START_MAP["Stats"] = Stats
    
    # convert the raw information of the map into a pygame friendly format
    TileMap = convert_raw_map(width, height, RawMap, tile_size, clipping_border)

    # make a copy of the final TileMap
    START_MAP["HeightMap"] = np.copy(HeightMap)
    START_MAP["RawMap"]    = np.copy(RawMap)
    START_MAP["TileMap"]   = np.copy(TileMap)

    # print the StartMaps statistics
    print("Total: {total} (check {check}) \n Water: {water} \n Land: {land} (Dirt: {dirt}, Grass: {grass})".format(
           total=Stats["total"],
           check=Stats["check"],
           water=Stats["water"],
           land =Stats["land"],
           dirt =Stats["dirt"],
           grass=Stats["grass"]))

    #if Stats["water"] / Stats["total"] < 0.2:
     #   print("MAP NOT COOL :/")
      #  return generate_tile_map(width, height, water_percentage, tile_size, clipping_border)
    #else:
    return (TileMap, START_MAP)


class Tile(pygame.sprite.DirtySprite):
    '''
    One Tile represents one grid point in the world
    '''
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

        # save original values for reset
        self._O_TILE_TYPE  = self.TileType
        self._O_FOOD_VALUE = self.FoodValue
        self._O_FEARTILE   = self.isFeartile

        # The initial Tile texture
        self.image = pygame.transform.scale(textures[self.TileType].convert(), (self.TileSize, self.TileSize))

        # Set the rendering position based on TileSize and Offset
        self.rect = self.image.get_rect()
        self.rect.x = self.Pos_x * self.TileSize + self.Offset
        self.rect.y = self.Pos_y * self.TileSize + self.Offset

    def update(self, creature=None):

        # update is equivalent to act
        self.FoodValue -= 100

        if self.FoodValue <= 0 and self.TileType == GRASS:
            self.FoodValue = 0
            self.TileType = MUD
            self.scale_to(self.TileSize, self.Offset)

            if creature is not None:

                if isinstance(creature, Survivor):
                    creature.Score += creature.rewards["grass"]
                    creature.Statistics["specialisation"]["collected_food"] +=1
                    creature.Statistics["rewards"]["reward_from_food"] += creature.rewards["grass"]
                    creature.Statistics["rewards"]["reward_total"] = creature.Score
                    # print("GRASS // Agent {}: +{} new score: {}".format(agent.ID, agent.rewards["grass"], agent.Score))
                elif isinstance(creature, Sheep):
                    creature.Statistics["specialisation"]["collected_food"] +=1
                    
                return True

        return False

            

    def scale_to(self, tile_size, offset):

        self.TileSize = tile_size
        self.Offset = offset
        self.image = pygame.transform.scale(textures[self.TileType].convert(), (self.TileSize, self.TileSize))
        self.rect = self.image.get_rect()
        self.rect.x = self.Pos_x * self.TileSize + self.Offset
        self.rect.y = self.Pos_y * self.TileSize + self.Offset
        #print(self.rect)

    def get_grid_pos(self):
        return (self.Pos_x, self.Pos_y)

    def reset(self):

        self.TileType   = self._O_TILE_TYPE
        self.FoodVlaue  = self._O_FOOD_VALUE
        self.isFeartile = self._O_FEARTILE
        self.scale_to(self.TileSize, self.Offset)
