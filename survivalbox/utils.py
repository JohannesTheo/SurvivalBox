__author__ = 'Johannes Theodoridis'

# standard imports

# third party imports
import numpy as np
import scipy as sci

# local imports
from .game_objects import UP, DOWN, LEFT, RIGHT
from . import map

def grid_from_position(pos, size_x, size_y):
    '''
    Return all points of a grid, given a point and a size.
    '''
    collision_grid = []

    if pos[2] == UP or pos[2] == DOWN:
        for w in range(size_x):
            for h in range(size_y):
                collision_grid.append((pos[0]+w,pos[1]+h)) 
    else:
        for w in range(size_x):
            for h in range(size_y):
                collision_grid.append((pos[0]+h,pos[1]+w))

    return tuple(collision_grid)

def random_position(tile_map, forbidden_types=[], min_space=1, random_orientation=False, strict_type_check=True):
        '''
        Returns a random point on the given map that is min_space points away from the border and not one of the types in forbidden_types.
        If stric type checking is True, the point and an area of min_space from that point is checked to be not a forbidden type.
        '''
        # calculate bounds
        MAX_WIDTH  = tile_map.shape[0] - 1 - (min_space - 1) # map width
        MAX_HEIGHT = tile_map.shape[1] - 1 - (min_space - 1) # map height

        # generate a position candidate
        valid_pos = False
        tries = 0
        while not valid_pos:
            if tries >= 10000: raise Exception("{} {} {} {}".format(
                                              "WARNING: We tried {} times to find a valid position of size ({},{}).".format(tries, min_space, min_space),
                                              "It is either impossible or very unlikely to place the",
                                              "object according to the given restrictions {}.".format(forbidden_types),
                                              "Please consider a bigger map size than {}, or reduce the number of GameObjects!".format(tile_map.shape)))

            tries += 1

            X = np.random.randint(1, MAX_WIDTH)   # Lower Bound is inklusive
            Y = np.random.randint(1, MAX_HEIGHT)  # Upper Bound is exklusive
            valid_pos = True

            for type in forbidden_types:
                if strict_type_check:
                    for w in range(min_space):
                        for h in range(min_space):
                            tile_type = tile_map[X+w,Y+h].TileType
                            if (tile_type == type) or (tile_type == map.EOW):
                                valid_pos = False
                                break
                        if not valid_pos: break
                    if not valid_pos: break
                else:
                    if (tile_map[X,Y].TileType == type) or (tile_map[X,Y].TileType == map.EOW):
                        valid_pos = False
                        break

        # return the position with random or fixed orientation
        if random_orientation:
            O = np.random.randint(0, 4)
            return ( X, Y, O)
        else:
            return ( X, Y, 0)

def free_random_position(tile_map, objects, forbidden_types=[], min_space=1, random_orientation=False):
        '''
        This methods will return a "free" point on the given map which can be used as a GameObject position for instance.
        To be a valid candidate position, an area of min_space (starting from the candidate position) is checked. If any 
        point in that area is of a forbidden type or is blocked by another game_object, the candidate will be rejected.
        '''        
        pos_free = False
        tries = 0
        while not pos_free:
            
            if tries >= 10000: raise Exception("{} {} {} {}".format(
                                              "WARNING: We tried {} times to place an object of size ({},{}).".format(tries, min_space, min_space),
                                              "It is either impossible or very unlikely to place the",
                                              "object according to the given restrictions {}.".format(forbidden_types),
                                              "Please consider a bigger map size than {}, or reduce the number of GameObjects!".format(tile_map.shape)))

            tries += 1
            
            pos_free = True
            candidate = random_position(tile_map, forbidden_types, min_space, random_orientation)
            candidate_grid = grid_from_position(candidate, min_space, min_space)
            
            for game_object in objects:
                game_object_grid = game_object.get_collision_grid()
                
                for point in candidate_grid:
                    if point in game_object_grid:
                        pos_free = False
                        break

                if not pos_free: break
        # print("Needed {} tries to find a free place".format(tries))
        return candidate

'''
Procedural map generation
'''
def interpolate(a: float,b: float,t: float):
        T2 = (1 - sci.cos(t * sci.pi)) / 2
        return (a * (1 - T2) + b * T2)

class ValueNoise2D():

    def __init__(self, width, height, octaves=8):
        # instance variables
        self.OCTAVES = octaves
        self.WIDTH = width
        self.HEIGHT = height     
        self.START_FREQUENCY_X = 3
        self.START_FREQUENCY_Y = 3
        self._HeightMap = np.zeros(shape=(width,height),dtype=float)

    def _normalize (self):
        Min = self._HeightMap.min()
        self._HeightMap = self._HeightMap - Min
        Max = self._HeightMap.max()
        self.HeightMap = self._HeightMap / Max        
  
    def get_height_map(self):
        return self._HeightMap

    def calculate(self):
        CurrentFrequency_X = self.START_FREQUENCY_X
        CurrentFrequency_Y = self.START_FREQUENCY_Y
        CurrentAlpha = 1

        for octave in range(self.OCTAVES):

            if octave > 0:
                CurrentFrequency_X *= 2
                CurrentFrequency_Y *= 2
                CurrentAlpha /= 2
        
            DiscretePoints = np.zeros(shape=(CurrentFrequency_X + 1, CurrentFrequency_Y + 1))
            for i in range(CurrentFrequency_X + 1):
                for k in range(CurrentFrequency_Y + 1):
                    # random between 0 and 1.
                    DiscretePoints[i, k] = np.random.random() * CurrentAlpha

            
            for i in range(self.WIDTH):
                for k in range(self.HEIGHT):
                    Current_X = i / self.WIDTH  * CurrentFrequency_X
                    Current_Y = k / self.HEIGHT * CurrentFrequency_Y
 
                    Index_X = int(Current_X)
                    Index_Y = int(Current_Y)

                    w0 = interpolate(DiscretePoints[ Index_X, Index_Y],     DiscretePoints[Index_X + 1, Index_Y],     Current_X - Index_X)
                    w1 = interpolate(DiscretePoints[ Index_X, Index_Y + 1], DiscretePoints[Index_X + 1, Index_Y + 1], Current_X - Index_X)
                    w  = interpolate(w0, w1, Current_Y - Index_Y)

                    self._HeightMap[i,k] += w

        self._normalize()