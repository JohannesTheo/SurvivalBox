__author__ = 'Johannes Theodoridis'

# standard imports

# third party imports
import numpy as np
import pygame
from pygame import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_COMMA, K_PERIOD, K_F15

# local imports

class ViewPort(pygame.Rect):

    def __init__(self, grid_points_left =10, 
                       grid_points_right=9, 
                       grid_points_front=10, 
                       grid_points_back =9):

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


    def get_viewport(self, position, tile_size, offset):
        grid_pos_X  = position[0]
        grid_pos_Y  = position[1]
        orientation = position[2]

        # Not smart but clear
        if orientation == 0: # UP
            self.left   = (grid_pos_X - self.grid_left          ) * tile_size + offset
            self.top    = (grid_pos_Y - self.grid_front         ) * tile_size + offset
            self.width  = (self.grid_left  + self.grid_right + 1) * tile_size
            self.height = (self.grid_front + self.grid_back  + 1) * tile_size
        elif orientation == 2: # DOWN
            self.left   = (grid_pos_X - self.grid_left          ) * tile_size + offset
            self.top    = (grid_pos_Y - self.grid_back          ) * tile_size + offset
            self.width  = (self.grid_left  + self.grid_right + 1) * tile_size
            self.height = (self.grid_front + self.grid_back  + 1) * tile_size
        elif orientation == 1: # RIGHT
            self.left   = (grid_pos_X - self.grid_back          ) * tile_size + offset
            self.top    = (grid_pos_Y - self.grid_left          ) * tile_size + offset
            self.width  = (self.grid_front + self.grid_back  + 1) * tile_size
            self.height = (self.grid_left  + self.grid_right + 1) * tile_size
        elif orientation == 3: # LEFT
            self.left   = (grid_pos_X - self.grid_front         ) * tile_size + offset
            self.top    = (grid_pos_Y - self.grid_right         ) * tile_size + offset
            self.width  = (self.grid_front + self.grid_back  + 1) * tile_size
            self.height = (self.grid_left  + self.grid_right + 1) * tile_size

        return self

class Survivor(pygame.sprite.DirtySprite):
    # cost constants
    COST_PERMANENT = 1.
    COST_MOVE = 5.
    COST_ROTATE = 5.
    COST_MULT_LAND = 1
    COST_MULT_WATER = 2

    # orientation
    UP    = 0
    RIGHT = 1
    DOWN  = 2
    LEFT  = 3

    # movement depending on orientation
    MOVE_FORWARD  = {UP: [ 0,-1, 0], DOWN: [ 0, 1, 0], LEFT: [-1, 0, 0], RIGHT: [ 1, 0, 0]}
    MOVE_BACKWARD = {UP: [ 0, 1, 0], DOWN: [ 0,-1, 0], LEFT: [ 1, 0, 0], RIGHT: [-1, 0, 0]}
    MOVE_LEFT     = {UP: [-1, 0, 0], DOWN: [ 1, 0, 0], LEFT: [ 0, 1, 0], RIGHT: [ 0,-1, 0]}
    MOVE_RIGHT    = {UP: [ 1, 0, 0], DOWN: [-1, 0, 0], LEFT: [ 0,-1, 0], RIGHT: [ 0, 1, 0]}

    # movement independent of orientation
    TURN_LEFT     = {UP: [ 0, 0,-1], DOWN: [ 0, 0,-1], LEFT: [ 0, 0,-1], RIGHT: [ 0, 0,-1]}
    TURN_RIGHT    = {UP: [ 0, 0, 1], DOWN: [ 0, 0, 1], LEFT: [ 0, 0, 1], RIGHT: [ 0, 0, 1]}
    NOOP          = {UP: [ 0, 0, 0], DOWN: [ 0, 0, 0], LEFT: [ 0, 0, 0], RIGHT: [ 0, 0, 0]}
    
    # Player State is encoded as [PosX, PosY, Orientation]: PosXY TileMap Position, Orientation is: T0,R1,D2,L3
    BASIC_ACTIONS = { K_UP    : MOVE_FORWARD,
                      K_DOWN  : MOVE_BACKWARD,
                      K_LEFT  : MOVE_LEFT,
                      K_RIGHT : MOVE_RIGHT,
                      K_COMMA : TURN_LEFT, 
                      K_PERIOD: TURN_RIGHT, 
                      K_F15   : NOOP
                    }

    # for debugging
    ORIENTATION_STRING_MAP = {UP:'UP', RIGHT:'RIGHT', DOWN:'DOWN', LEFT:'LEFT'}

    def __init__(self, ID, view_port, start_x=1, start_y=1, start_o=0, size=8, offset=0):
        
        pygame.sprite.Sprite.__init__(self)

        self.ID = ID
        self.ACTIONS = Survivor.BASIC_ACTIONS
        
        self.Pos = np.array([start_x, start_y, start_o])
        self.OldPos = self.Pos.copy()
        self.ViewPort = view_port

        self.Energy = 50.
        self.CostMultiplier = Survivor.COST_MULT_LAND

        self.TileSize = size
        self.Offset = offset
        self.image = pygame.Surface([size, size])
        self.image.fill((255,0,0))
        self.rect = self.image.get_rect()
        self.update_render_pos()

    def scale_to(self, new_size, new_offset):
        self.TileSize = new_size
        self.Offset   = new_offset
        self.image    = pygame.transform.scale(self.image, (self.TileSize, self.TileSize))
        self.rect     = self.image.get_rect()
        self.update_render_pos()

    def get_view(self):
        return self.ViewPort.get_viewport(self.Pos, self.TileSize, self.Offset)

    def get_marker(self):

        marker = self.rect.copy()

        if self.Pos[2] == Survivor.UP:
            marker.y = (self.Pos[1] - 1) * self.TileSize + self.Offset
        elif self.Pos[2] == Survivor.DOWN:
            marker.y = (self.Pos[1] + 1) * self.TileSize + self.Offset
        elif self.Pos[2] == Survivor.LEFT:
            marker.x = (self.Pos[0] - 1) * self.TileSize + self.Offset
        elif self.Pos[2] == Survivor.RIGHT:
            marker.x = (self.Pos[0] + 1) * self.TileSize + self.Offset

        return marker

    def get_marker_rect(self, Pos, TileSize, Offset):

        x = Pos[0] * TileSize + Offset
        y = Pos[1] * TileSize + Offset
        w = TileSize
        h = TileSize
 
        marker = pygame.Rect(x,y,w,h)

        if   Pos[2] == Survivor.UP:
            marker.y = (Pos[1] - 1) * TileSize + Offset
        elif Pos[2] == Survivor.DOWN:
            marker.y = (Pos[1] + 1) * TileSize + Offset
        elif Pos[2] == Survivor.LEFT:
            marker.x = (Pos[0] - 1) * TileSize + Offset
        elif Pos[2] == Survivor.RIGHT:
            marker.x = (Pos[0] + 1) * TileSize + Offset

        return marker


    def get_grid_pos(self):
        return (self.Pos[0], self.Pos[1])

    def draw_as_ally(self, Surface):
        pygame.draw.rect(Surface, (0,0,255) ,self.rect)

    def update(self, dt, action_list=[]):

        # If Survivor is dead return
        if self.Energy <= 0:
            self.kill()
            return

        # Save OldPos for resetting after border collision
        self.OldPos = self.Pos.copy()

        # Get Action based on ID (index), or set to NOOP if empty list
        if not action_list:
            action = K_F15
        else:
            action = action_list[self.ID]

        # In every case reduse Energy by the permanent Life Cost
        self.Energy -= Survivor.COST_PERMANENT * dt * self.CostMultiplier
        #print("ENERGY: {}, COST_MULT: {}".format(self.Energy, self.CostMultiplier))
        
        # If the action is not NOOP apply MOVE Cost
        if action != K_F15:
            loss = Survivor.COST_MOVE * dt * 3 * self.CostMultiplier
            #print("LOSS: {}:".format(loss))
            self.Energy -= loss

        # Set the new Grid Position and Render Position based on the action
        orientation = self.Pos[2]
        self.Pos   += self.ACTIONS[action][orientation]
        self.Pos[2] = self.Pos[2] % 4 # clip orientation to (0..3)

        self.update_render_pos()

    def set_back(self):
        self.Pos = self.OldPos
        self.update_render_pos()

    def update_render_pos(self):
        # Set render position
        self.rect.x = self.Pos[0] * self. TileSize + self.Offset
        self.rect.y = self.Pos[1] * self. TileSize + self.Offset
