__author__ = 'Johannes Theodoridis'

# standard imports
import os

# third party imports
import numpy as np
import pygame
from pygame import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_COMMA, K_PERIOD, K_F15

# local imports
from . import map

# orientation
UP    = 0
RIGHT = 1
DOWN  = 2
LEFT  = 3
# for debugging and information
ORIENTATION_STRING_MAP = {UP:'UP', RIGHT:'RIGHT', DOWN:'DOWN', LEFT:'LEFT'}

# basic movement depending on orientation
MOVE_FORWARD  = {UP: [ 0,-1, 0], DOWN: [ 0, 1, 0], LEFT: [-1, 0, 0], RIGHT: [ 1, 0, 0]}
MOVE_BACKWARD = {UP: [ 0, 1, 0], DOWN: [ 0,-1, 0], LEFT: [ 1, 0, 0], RIGHT: [-1, 0, 0]}
MOVE_LEFT     = {UP: [-1, 0, 0], DOWN: [ 1, 0, 0], LEFT: [ 0, 1, 0], RIGHT: [ 0,-1, 0]}
MOVE_RIGHT    = {UP: [ 1, 0, 0], DOWN: [-1, 0, 0], LEFT: [ 0,-1, 0], RIGHT: [ 0, 1, 0]}
NOOP          = {UP: [ 0, 0, 0], DOWN: [ 0, 0, 0], LEFT: [ 0, 0, 0], RIGHT: [ 0, 0, 0]}

# Preload Images
_DIR = os.path.dirname(os.path.abspath(__file__))
FIRE_ON_SMALL  = pygame.image.load(os.path.join(_DIR,'assets/fire_on_small.png' )) #.convert()
FIRE_OFF_SMALL = pygame.image.load(os.path.join(_DIR,'assets/fire_off_small.png')) #.convert()
FIRE_ON        = pygame.image.load(os.path.join(_DIR,'assets/fire_on.png' )) #.convert()
FIRE_OFF       = pygame.image.load(os.path.join(_DIR,'assets/fire_off.png')) #.convert()
SHEEP          = pygame.image.load(os.path.join(_DIR,'assets/sheep.png')) #.convert()
WOLF           = pygame.image.load(os.path.join(_DIR,'assets/wolf.png')) #.convert()


def create_marker_rect(Pos, TileSize, Offset, size_x=1, size_y=1):
        '''
        This method returns the grid point infront of the given position (depending on the orientation), as a scaled rectangle.
        The returned rectangle can be used to draw an orientation marker on the map for instance.
        '''
        x = Pos[0] * TileSize + Offset
        y = Pos[1] * TileSize + Offset
        w = TileSize
        h = TileSize
 
        marker = pygame.Rect(x,y,w,h)

        if   Pos[2] == UP:
            marker.y = (Pos[1] - 1) * TileSize + Offset
        elif Pos[2] == DOWN:
            marker.y = (Pos[1] + size_y) * TileSize + Offset
        elif Pos[2] == LEFT:
            marker.x = (Pos[0] - 1) * TileSize + Offset
        elif Pos[2] == RIGHT:
            marker.x = (Pos[0] + size_y) * TileSize + Offset

        return marker

class GameObject():

    def __init__(self, start_pos, tile_size, offset, grid_size, actions, base_image=None, view_port=None):

        self.Pos     = np.array(start_pos)
        self.OldPos  = self.Pos.copy()

        self.GRID_W = grid_size[0] # grid width  of the object in UP/DOWN position
        self.GRID_H = grid_size[1] # grid height of the object in UP/DOWN position
        
        self.Grid    = self.update_collision_grid()
        self.OldGrid = self.Grid
        
        self.TileSize = tile_size
        self.Offset   = offset

        self.ACTIONS = actions

        self.BASE_IMAGE = base_image
        if self.BASE_IMAGE is not None:
            self.IMAGE = pygame.transform.scale(self.BASE_IMAGE, (self.TileSize * self.GRID_W, self.TileSize * self.GRID_H))
            self.image = self.IMAGE
            self.rect = self.image.get_rect()
            self.update_render_pos()

        self.ViewPort = view_port
        if view_port is None:
            self.ViewPort = ViewPort(0,0,0,0)

    def get_grid_pos(self):
        return (self.Pos[0], self.Pos[1])

    def get_grid_pos_old(self):
        return (self.OldPos[0], self.OldPos[1])

    def get_collision_grid(self):
        return self.Grid

    def get_collision_grid_old(self):
        return self.OldGrid

    def get_view(self):
        return self.ViewPort.get_viewport(self.Pos, self.TileSize, self.Offset, self.GRID_W, self.GRID_H)

    def get_view_scaled(self, tile_size, offset):
        return self.ViewPort.get_viewport(self.Pos, tile_size, offset, self.GRID_W, self.GRID_H)

    def get_marker(self):
        return create_marker_rect(self.Pos, self.TileSize, self.Offset, self.GRID_W, self.GRID_H)

    def get_marker_scaled(self, tile_size, offset):
        return create_marker_rect(self.Pos, tile_size, offset, self.GRID_W, self.GRID_H)

    def update_collision_grid(self):

        collision_grid = []

        if self.Pos[2] == UP or self.Pos[2] == DOWN:
            for w in range(self.GRID_W):
                for h in range(self.GRID_H):
                    collision_grid.append((self.Pos[0]+w,self.Pos[1]+h)) 
        else:
            for w in range(self.GRID_W):
                for h in range(self.GRID_H):
                    collision_grid.append((self.Pos[0]+h,self.Pos[1]+w))

        return tuple(collision_grid)

    def move(self, action):
        self.OldPos  = self.Pos.copy()
        self.OldGrid = self.Grid

        orientation  = self.Pos[2]
        self.Pos    += self.ACTIONS[action][orientation]
        self.Pos[2] %= 4 # clip orientation to (0..3)
        self.Grid    = self.update_collision_grid()

    def set_back(self):
        self.Pos  = self.OldPos.copy()
        self.Grid = self.OldGrid

    def update_render_pos(self, rotate=False, tile_map=None):
        
        if rotate:
            self.image = pygame.transform.rotate(self.IMAGE, self.Pos[2] * -90)
            self.rect = self.image.get_rect()

        self.rect.x = self.Pos[0] * self. TileSize + self.Offset
        self.rect.y = self.Pos[1] * self. TileSize + self.Offset

        dirty_sprites = []
        if tile_map is not None:
            points = []
            for point in self.OldGrid:
                if point not in self.Grid:
                    points.append(point)
                    dirty_sprites.append(tile_map[point])
            print("OLD: {}, NEW: {} REDRAW: {}".format(self.OldGrid, self.Grid, points))
        
        return tuple(dirty_sprites)

    def scale_to(self, new_size, new_offset):
        self.TileSize = new_size
        self.Offset   = new_offset
        self.IMAGE    = pygame.transform.scale(self.BASE_IMAGE, (self.TileSize * self.GRID_W, self.TileSize * self.GRID_H))
        self.image    = self.IMAGE
        self.rect     = self.image.get_rect()
        self.reset(self.Pos)

    def reset(self, new_pos):
        self.Pos = np.array(new_pos)
        self.OldPos = self.Pos.copy()
        self.Grid = self.update_collision_grid()
        self.OldGrid = self.Grid
        self.update_render_pos(rotate=True)
    
    def update(self):
        raise NotImplementedError()


class ViewPort(pygame.Rect):

    def __init__(self, grid_points_left, 
                       grid_points_right, 
                       grid_points_front, 
                       grid_points_back):

        pygame.Rect.__init__(self, 
            0,
            0, 
            grid_points_left + grid_points_right + 1, 
            grid_points_front + grid_points_back + 1)
         
        self.grid_left  = grid_points_left
        self.grid_right = grid_points_right
        self.grid_front = grid_points_front
        self.grid_back  = grid_points_back

    def get_grid_size(self):
        return (self.grid_left, self.grid_right, self.grid_front, self.grid_back)

    def get_grid_dimensions(self):
        return( self.grid_left + self.grid_right + 1 , self.grid_front + self.grid_back + 1)

    def get_viewport(self, position, tile_size, offset, size_x=1, size_y=1):
        grid_pos_X  = position[0]
        grid_pos_Y  = position[1]
        orientation = position[2]

        # Not smart but clear
        if orientation == 0: # UP
            self.left   = (grid_pos_X - self.grid_left          ) * tile_size + offset
            self.top    = (grid_pos_Y - self.grid_front         ) * tile_size + offset
            self.width  = (self.grid_left  + self.grid_right + size_x) * tile_size
            self.height = (self.grid_front + self.grid_back  + size_y) * tile_size
        elif orientation == 2: # DOWN
            self.left   = (grid_pos_X - self.grid_left          ) * tile_size + offset
            self.top    = (grid_pos_Y - self.grid_back          ) * tile_size + offset
            self.width  = (self.grid_left  + self.grid_right + size_x) * tile_size
            self.height = (self.grid_front + self.grid_back  + size_y) * tile_size
        elif orientation == 1: # RIGHT
            self.left   = (grid_pos_X - self.grid_back          ) * tile_size + offset
            self.top    = (grid_pos_Y - self.grid_left          ) * tile_size + offset
            self.width  = (self.grid_front + self.grid_back  + size_y) * tile_size
            self.height = (self.grid_left  + self.grid_right + size_x) * tile_size
        elif orientation == 3: # LEFT
            self.left   = (grid_pos_X - self.grid_front         ) * tile_size + offset
            self.top    = (grid_pos_Y - self.grid_right         ) * tile_size + offset
            self.width  = (self.grid_front + self.grid_back  + size_y) * tile_size
            self.height = (self.grid_left  + self.grid_right + size_x) * tile_size

        return self

class Survivor(pygame.sprite.DirtySprite, GameObject):
    # cost constants
    COST_PERMANENT = 1.
    COST_MOVE = 5.
    COST_ROTATE = 5.
    COST_MULT_LAND = 1
    COST_MULT_WATER = 3

    # Define additional Survivor specific movement
    TURN_LEFT     = {UP: [ 0, 0,-1], DOWN: [ 0, 0,-1], LEFT: [ 0, 0,-1], RIGHT: [ 0, 0,-1]}
    TURN_RIGHT    = {UP: [ 0, 0, 1], DOWN: [ 0, 0, 1], LEFT: [ 0, 0, 1], RIGHT: [ 0, 0, 1]}
    
    # Player State is encoded as [PosX, PosY, Orientation]: PosXY TileMap Position, Orientation is: T0,R1,D2,L3
    BASIC_ACTIONS = { K_UP    : MOVE_FORWARD,
                      K_DOWN  : MOVE_BACKWARD,
                      K_LEFT  : MOVE_LEFT,
                      K_RIGHT : MOVE_RIGHT,
                      K_COMMA : TURN_LEFT, 
                      K_PERIOD: TURN_RIGHT, 
                      K_F15   : NOOP
                    }

    def __init__(self, ID, view_port, agent_start_pos=(1,1,0), size=8, offset=0):
        
        pygame.sprite.Sprite.__init__(self)

        base_image = pygame.Surface([size, size])
        base_image.fill((255,0,0))
        GameObject.__init__(self, agent_start_pos, size, offset, (1,1), Survivor.BASIC_ACTIONS, base_image)

        self.ID = ID
        self.ViewPort = view_port

        # dynamics
        self.Energy = 3000.
        self._O_ENERGY = self.Energy
        self.CostMultiplier = 1
        # reward
        self.Score = 0

    def draw_as_ally(self, Surface):
        pygame.draw.rect(Surface, (0,0,255) ,self.rect)

    def draw_as_self(self, Surface):
        Surface.blit(self.image, self.rect)

    def update(self, action_list, tile_map, rewards, game_objects):

        # apply the basic cost
        self.Energy -= 1 * self.CostMultiplier

        # If survivor is dead return
        if self.Energy <= 0:
            self.kill()
            return self.update_render_pos()

        # Apply the action and update the position
        action = action_list[self.ID]
        self.move(action)

        # Check collisions with map and other game_objects
        for point in self.Grid:
            colliding_map_tile = tile_map[point]
            
            if colliding_map_tile.TileType == map.EOW:
                self.set_back()
                break

            for game_object in game_objects:
                if point in game_object.get_collision_grid():
                    self.set_back()
                    break

            if colliding_map_tile.TileType == map.WATER:
                self.CostMultiplier = Survivor.COST_MULT_WATER
            else:
                self.CostMultiplier = Survivor.COST_MULT_LAND

            # update the Map on the correct pos
            colliding_map_tile.update(self, rewards)

        return self.update_render_pos(tile_map=tile_map)

    def reset(self, new_pos):

        self.Energy = self._O_ENERGY
        self.Score = 0
        self.CostMultiplier = 1
        super(Survivor, self).reset(new_pos)
 
class Fireplace(pygame.sprite.DirtySprite, GameObject):

    def __init__(self, pos, tile_size, offset=0, small=False):
        
        pygame.sprite.Sprite.__init__(self)
        if small:
            IMAGE_ON  = FIRE_ON_SMALL.conert()
            IMAGE_OFF = FIRE_OFF_SMALL.convert()
            NUM_TILES = 3
        else:
            IMAGE_ON  = FIRE_ON.convert()
            IMAGE_OFF = FIRE_OFF.convert() 
            NUM_TILES = 4

        GameObject.__init__(self, pos, tile_size, offset, (NUM_TILES, NUM_TILES), None, IMAGE_OFF)

        # add a second Surface for the Fire ON image        
        self.BASE_IMAGE_2 = IMAGE_ON
        self.IMAGE_2 = pygame.transform.scale(self.BASE_IMAGE_2, (self.TileSize * self.GRID_W, self.TileSize * self.GRID_H))

        self.ON = False
        self.test = 0

    def update(self, actions, tile_map):

        self.test += 1
        if self.test > 50:
            self.ON = True
            self.image = self.IMAGE_2 # Fire on
        if self.test > 150:
            self.ON = False
            self.image = self.IMAGE   # Fire off
        return []

    def scale_to(self, tile_size, offset):
        self.IMAGE_2  = pygame.transform.scale(self.BASE_IMAGE_2, (tile_size * self.GRID_W, tile_size * self.GRID_H))
        super(Fireplace, self).scale_to(tile_size, offset)
    
    def reset(self, new_pos):
        self.test = 0
        self.ON = False
        super(Fireplace, self).reset(new_pos)

class Sheep(pygame.sprite.DirtySprite, GameObject):

    # Define additional Sheep specific movement
    #TURN_LEFT     = {UP: [-1, 1,-1], DOWN: [ 0, 0,-1], LEFT: [ 1, 0,-1], RIGHT: [ 0,-1,-1]}
    #TURN_RIGHT    = {UP: [ 0, 1, 1], DOWN: [-1, 0, 1], LEFT: [ 1,-1, 1], RIGHT: [ 0, 0, 1]}
    TURN_LEFT     = {UP: [-1, 0,-1], DOWN: [ 0, 1,-1], LEFT: [ 0, 0,-1], RIGHT: [ 1,-1,-1]}
    TURN_RIGHT    = {UP: [ 0, 0, 1], DOWN: [-1, 1, 1], LEFT: [ 0,-1, 1], RIGHT: [ 1, 0, 1]}

    FORWARD = 0
    TURN_L  = 1
    TURN_R  = 2

    BASIC_ACTIONS = { K_UP    : MOVE_FORWARD,
                      K_DOWN  : MOVE_BACKWARD,
                      K_LEFT  : MOVE_LEFT,
                      K_RIGHT : MOVE_RIGHT,
                      K_COMMA : TURN_LEFT, 
                      K_PERIOD: TURN_RIGHT, 
                      K_F15   : NOOP
                    }

    def __init__(self, start_pos, tile_size=8, offset=0 ):
        
        pygame.sprite.Sprite.__init__(self)
        GameObject.__init__(self, start_pos, tile_size, offset, (1,2), Sheep.BASIC_ACTIONS, SHEEP.convert())
        self.ViewPort = ViewPort(5,5,5,4)

       #UP    = ViewPort(5,6,5,5)
       # DOWN  = ViewPort(6,5,5,5)
       # LEFT  = ViewPort(5,5,5,6)
       # RIGHT = ViewPort(5,5,6,5)

    def update(self, actions, tile_map):

        action = actions[0]
        self.move(action)

        for point in self.Grid:
            colliding_map_tile = tile_map[point]
            
            if colliding_map_tile.TileType == map.EOW:
                self.set_back()
                break

            # update the Map on the correct pos
            colliding_map_tile.update()
        
        return self.update_render_pos(rotate=True, tile_map=tile_map)

class Wolf(pygame.sprite.DirtySprite, GameObject):

    # Define additional Wolf specific movement
    #TURN_LEFT     = {UP: [-1, 1,-1], DOWN: [ 0, 0,-1], LEFT: [ 1, 0,-1], RIGHT: [ 0,-1,-1]}
    #TURN_RIGHT    = {UP: [ 0, 1, 1], DOWN: [-1, 0, 1], LEFT: [ 1,-1, 1], RIGHT: [ 0, 0, 1]}
    TURN_LEFT     = {UP: [-1, 0,-1], DOWN: [ 0, 1,-1], LEFT: [ 0, 0,-1], RIGHT: [ 1,-1,-1]}
    TURN_RIGHT    = {UP: [ 0, 0, 1], DOWN: [-1, 1, 1], LEFT: [ 0,-1, 1], RIGHT: [ 1, 0, 1]}

    FORWARD = 0
    TURN_L  = 1
    TURN_R  = 2

    BASIC_ACTIONS = { K_UP    : MOVE_FORWARD,
                      K_DOWN  : MOVE_BACKWARD,
                      K_LEFT  : MOVE_LEFT,
                      K_RIGHT : MOVE_RIGHT,
                      K_COMMA : TURN_LEFT, 
                      K_PERIOD: TURN_RIGHT, 
                      K_F15   : NOOP
                    }

    def __init__(self, start_pos, tile_size=8, offset=0 ):
        
        pygame.sprite.Sprite.__init__(self)
        GameObject.__init__(self, start_pos, tile_size, offset, (1,2), Wolf.BASIC_ACTIONS, WOLF.convert())

    def update(self, actions, tile_map):

        action = actions[0]
        #self.move(action)

        for point in self.Grid:
            colliding_map_tile = tile_map[point]
            
            if colliding_map_tile.TileType == map.EOW:
                self.set_back()
                break

            # update the Map on the correct pos
            colliding_map_tile.update()
        
        return self.update_render_pos(rotate=True, tile_map=tile_map)