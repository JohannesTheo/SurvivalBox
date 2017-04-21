__author__ = 'Johannes Theodoridis'

# standard imports
import os

# third party imports
import numpy as np
import pygame

# local imports
from .utils import ValueNoise2D

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

        # The initial Tile texture
        self.image = pygame.transform.scale(textures[self.TileType].convert(), (self.TileSize, self.TileSize))

        # Set the rendering position based on TileSize and Offset
        self.rect = self.image.get_rect()
        self.rect.x = self.Pos_x * self.TileSize + self.Offset
        self.rect.y = self.Pos_y * self.TileSize + self.Offset

    def update(self,env):

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