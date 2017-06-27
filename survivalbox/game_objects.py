__author__ = 'Johannes Theodoridis'

# standard imports
import os
import copy

# third party imports
import numpy as np
import pygame
from pygame import K_UP, K_DOWN, K_LEFT, K_RIGHT, K_COMMA, K_PERIOD, K_F15

# local imports
from . import map
from . import utils

MANUAL=False
#RANDOM=False
RANDOM_NPC=False

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

# Define additional Survivor specific movement
AGENT_TURN_LEFT     = {UP: [ 0, 0,-1], DOWN: [ 0, 0,-1], LEFT: [ 0, 0,-1], RIGHT: [ 0, 0,-1]}
AGENT_TURN_RIGHT    = {UP: [ 0, 0, 1], DOWN: [ 0, 0, 1], LEFT: [ 0, 0, 1], RIGHT: [ 0, 0, 1]}

# Define additional Animal specific movement
#ANIMAL_TURN_LEFT     = {UP: [-1, 1,-1], DOWN: [ 0, 0,-1], LEFT: [ 1, 0,-1], RIGHT: [ 0,-1,-1]}
#ANIMAL_TURN_RIGHT    = {UP: [ 0, 1, 1], DOWN: [-1, 0, 1], LEFT: [ 1,-1, 1], RIGHT: [ 0, 0, 1]}
ANIMAL_TURN_LEFT     = {UP: [-1, 0,-1], DOWN: [ 0, 1,-1], LEFT: [ 0, 0,-1], RIGHT: [ 1,-1,-1]}
ANIMAL_TURN_RIGHT    = {UP: [ 0, 0, 1], DOWN: [-1, 1, 1], LEFT: [ 0,-1, 1], RIGHT: [ 1, 0, 1]}
ANIMAL_TURN_FULL     = {UP: [ 0, 0, 2], DOWN: [ 0, 0, 2], LEFT: [ 0, 0, 2], RIGHT: [ 0, 0, 2]}

# Constants for NPCs move mappings // Human Player uses the pygame constants for mapping
FORWARD = 0
TURN_L  = 1
TURN_R  = 2
TURN_F  = 3
STAY    = 4

# Preload Images
_DIR = os.path.dirname(os.path.abspath(__file__))
FIRE_ON_SMALL  = pygame.image.load(os.path.join(_DIR,'assets/fire_on_small.png' )) #.convert()
FIRE_OFF_SMALL = pygame.image.load(os.path.join(_DIR,'assets/fire_off_small.png')) #.convert()
FIRE_ON        = pygame.image.load(os.path.join(_DIR,'assets/fire_on.png' )) #.convert()
FIRE_OFF       = pygame.image.load(os.path.join(_DIR,'assets/fire_off.png')) #.convert()
SHEEP          = pygame.image.load(os.path.join(_DIR,'assets/sheep.png')) #.convert()
WOLF           = pygame.image.load(os.path.join(_DIR,'assets/wolf.png')) #.convert()

SURVIVOR_STATISTICS = {

            "basics" : {
                "steps_alive" : 0,
                "steps_water" : 0,
                "steps_land"  : 0,
                "collisions"  : 0
            },
            "specialisation" : {
                "steps_as_fireguard" : 0,
                "steps_as_shepherd"  : 0,
                "blocked_sheep"    : 0,
                "hits_from_wolf"   : 0,
                "catched_wolf"     : 0,
                "energy_from_wolf" : 0,
                "collected_food"   : 0
            },
            "rewards" : {
                "reward_from_fire"  : 0,
                "reward_from_sheep" : 0,
                "reward_from_wolf"  : 0,
                "reward_from_food"  : 0,
                "reward_total"      : 0
            }
        }

SHEEP_STATISTICS = {

            "basics" : {
                "steps_total" : 0,
                "steps_slow"  : 0,
                "steps_fast"  : 0,
                "collisions"  : 0
            },
            "specialisation" : {
                "collected_food"  : 0,
                "catched_by_wolf" : 0,
                "steps_with_shepherd"    : 0,
                "steps_without_shepherd" : 0,
                "shepherd_switches" : 0
            }
        }

WOLF_STATISTICS = {

            "basics" : {
                "steps_total" : 0,
                "steps_slow"  : 0,
                "steps_fast"  : 0,
                "collisions"  : 0
            },
            "specialisation" : {
                "steps_hunting" : 0,
                "catched_sheep"  : 0,
                "catched_by_survivor" : 0,
                "attacked_survivor"   : 0
            }
        }

FIRE_STATISTICS = {

            "specialisation" : {
                "steps_fire_on"   : 0,
                "steps_fire_off"  : 0,
                "fire_switches" : 0
            }
        }

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

    def __init__(self, ID, start_pos, tile_size, offset, grid_size, actions, base_image=None, view_port=None, statistics_dict={}):

        self.STATS = copy.deepcopy(statistics_dict) #.copy()
        self.Statistics = copy.deepcopy(self.STATS.copy) #()

        self.ID = ID
        self.Pos     = np.array(start_pos)
        self.OldPos  = self.Pos.copy()

        self.GRID_W = grid_size[0] # grid width  of the object in UP/DOWN position
        self.GRID_H = grid_size[1] # grid height of the object in UP/DOWN position
        self.GRID_MAX = max(self.GRID_W,self.GRID_H)
        
        self.Grid     = self.update_collision_grid()
        self.OldGrid  = self.Grid
        
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

    def get_view_grid(self):
        return self.get_view_scaled(1, 0)

    def get_marker(self):
        return create_marker_rect(self.Pos, self.TileSize, self.Offset, self.GRID_W, self.GRID_H)

    def get_marker_scaled(self, tile_size, offset):
        return create_marker_rect(self.Pos, tile_size, offset, self.GRID_W, self.GRID_H)

    def update_collision_grid(self):
        return utils.grid_from_position(self.Pos, self.GRID_W, self.GRID_H)

    def select_random_move(self, actions=[]):
            return np.random.choice(actions)

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

    def update_render_pos(self, rotate=False, tile_map=None, dead=False):
        
        if rotate:
            self.image = pygame.transform.rotate(self.IMAGE, self.Pos[2] * -90)
            self.rect = self.image.get_rect()

        self.rect.x = self.Pos[0] * self. TileSize + self.Offset
        self.rect.y = self.Pos[1] * self. TileSize + self.Offset

        dirty_sprites = []
        if tile_map is not None:
            points = []

            if dead:
                for point in self.OldGrid:
                    points.append(point)
                    dirty_sprites.append(tile_map[point])
                for point in self.Grid:
                    points.append(point)
                    dirty_sprites.append(tile_map[point])
            else:
                for point in self.OldGrid:
                    if point not in self.Grid:
                        points.append(point)
                        dirty_sprites.append(tile_map[point])
            #print("OLD: {}, NEW: {} REDRAW: {}".format(self.OldGrid, self.Grid, points))
        
        return tuple(dirty_sprites)

    def scale_to(self, new_size, new_offset):
        self.TileSize = new_size
        self.Offset   = new_offset
        self.IMAGE    = pygame.transform.scale(self.BASE_IMAGE, (self.TileSize * self.GRID_W, self.TileSize * self.GRID_H))
        self.image    = self.IMAGE
        self.rect     = self.image.get_rect()
        self.reset(self.Pos)

    def reset(self, new_pos, reset_stats=False):
        
        if reset_stats: self.Statistics = copy.deepcopy(self.STATS) #.copy()
        
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
    # cost constants (game dynamics)
    #COST_PERMANENT = 1.
    #COST_MOVE = 5.
    #COST_ROTATE = 5.
    COST_MULT_LAND = 1
    COST_MULT_WATER = 3
    
    # Action Mapping for Survivor, defines possible actions!
    BASIC_ACTIONS = { K_UP    : MOVE_FORWARD,
                      K_DOWN  : MOVE_BACKWARD,
                      K_LEFT  : MOVE_LEFT,
                      K_RIGHT : MOVE_RIGHT,
                      K_COMMA : AGENT_TURN_LEFT, 
                      K_PERIOD: AGENT_TURN_RIGHT, 
                      K_F15   : NOOP
                    }

    def __init__(self, ID, rewards, view_port, agent_start_pos, size, offset, life_points):
        
        pygame.sprite.Sprite.__init__(self)

        base_image = pygame.Surface([size, size])
        base_image.fill((255,0,0))

        GameObject.__init__(self, ID, agent_start_pos, size, offset, (1,1), Survivor.BASIC_ACTIONS, base_image, None, SURVIVOR_STATISTICS)

        self.ViewPort = view_port

        # dynamics
        self.Energy = life_points
        self._O_ENERGY = self.Energy
        self.CostMultiplier = 1
        # rewards
        self.rewards = rewards
        self.Score = 0
        self.StepsAlive = 0

    def draw_as_ally(self, Surface):
        pygame.draw.rect(Surface, (0,0,255) ,self.rect)

    def draw_as_self(self, Surface):
        Surface.blit(self.image, self.rect)

    def update(self, action_list, tile_map, living_creatures):

        # apply the basic cost
        self.Energy -= 1 * self.CostMultiplier

        # If survivor is dead return
        if self.Energy <= 0:
            self.kill()
            return self.update_render_pos(tile_map=tile_map, dead=True)

        self.StepsAlive += 1
        #print("Agent {}: steps {}".format(self.ID, self.StepsAlive))
        self.Statistics["basics"]["steps_alive"] +=1

        # Apply the action and update the position
        action = action_list[self.ID]
        self.move(action)

        # Check collisions with map and other game_objects
        dead_wolf_sprites = ()
        for point in self.Grid:

            colliding_map_tile = tile_map[point]
            
            if colliding_map_tile.TileType == map.EOW:
                self.set_back()
                self.Statistics["basics"]["collisions"] +=1
                break

            for creature in living_creatures:
                if point in creature.get_collision_grid():

                    if isinstance(creature, Survivor):
                        if self.ID != creature.ID:
                            self.set_back()
                            self.Statistics["basics"]["collisions"] +=1
                            break

                    elif isinstance(creature, Wolf):
                        #print("GOT THE WOLF!")
                        
                        # Apply the reward
                        self.Score += self.rewards["wolf"]

                        for survivor in living_creatures:
                            if isinstance(survivor, Survivor):
                                energy_from_wolf = (creature.StepsAlive * 0.25)
                                survivor.Energy += energy_from_wolf
                                self.Statistics["specialisation"]["energy_from_wolf"] += energy_from_wolf

                        #print("ENERGY FROM WOLF: {}".format(energy_from_wolf))
                        # reset wolf
                        creature.StepsAlive = 0

                        #print("WOLF  // Agent {}: +{} new score: {}".format(self.ID, self.rewards["wolf"], self.Score))
                        
                        # Save the wolfs position for redrawing later
                        dead_wolf_sprites = creature.get_collision_grid()

                        # Find a new random position for the wolf and reset
                        new_pos = utils.free_random_position( tile_map, living_creatures, forbidden_types=[map.WATER], min_space=creature.GRID_MAX)
                        creature.reset(new_pos)

                        creature.Statistics["specialisation"]["catched_by_survivor"] +=1
                        self.Statistics["specialisation"]["catched_wolf"] +=1
                        self.Statistics["rewards"]["reward_from_wolf"] += self.rewards["wolf"]
                        self.Statistics["rewards"]["reward_total"] = self.Score
                        break
                    else:
                        self.set_back()
                        self.Statistics["basics"]["collisions"] +=1
                        break

        # Now that we have the final position update the map on this position
        for point in self.Grid:
            colliding_map_tile = tile_map[point]

            if colliding_map_tile.TileType == map.WATER:
                self.CostMultiplier = Survivor.COST_MULT_WATER
                self.Statistics["basics"]["steps_water"] +=1
            else:
                self.CostMultiplier = Survivor.COST_MULT_LAND
                self.Statistics["basics"]["steps_land"] +=1

            collected_food = colliding_map_tile.update(self)
            if collected_food:
                for creature in living_creatures:
                    if isinstance(creature, Survivor):
                        creature.Energy += 0.25

        # Add the sprites points from the dead wolf to our self.OldGrid for redrawing!
        self.OldGrid += dead_wolf_sprites
        # Return all sprites that need redrawing
        return self.update_render_pos(tile_map=tile_map)

    def reset(self, new_pos, reset_stats=False):

        self.Energy = self._O_ENERGY
        self.Score = 0
        self.StepsAlive = 0
        self.CostMultiplier = 1
        super(Survivor, self).reset(new_pos, reset_stats)
 
class Fireplace(pygame.sprite.DirtySprite, GameObject):

    def __init__(self, ID, pos, tile_size, offset=0, small=False):
        
        pygame.sprite.Sprite.__init__(self)

        if small:
            IMAGE_ON  = FIRE_ON_SMALL.conert()
            IMAGE_OFF = FIRE_OFF_SMALL.convert()
            NUM_TILES = 3
        else:
            IMAGE_ON  = FIRE_ON.convert()
            IMAGE_OFF = FIRE_OFF.convert() 
            NUM_TILES = 4

        FireArea = ViewPort(3,3,3,3)
        GameObject.__init__(self, ID, pos, tile_size, offset, (NUM_TILES, NUM_TILES), None, IMAGE_OFF, FireArea, FIRE_STATISTICS)

        # add a second Surface for the Fire ON image        
        self.BASE_IMAGE_2 = IMAGE_ON
        self.IMAGE_2 = pygame.transform.scale(self.BASE_IMAGE_2, (self.TileSize * self.GRID_W, self.TileSize * self.GRID_H))

        self.ON = False
        self.FIRE_GUARD = -1 # only one agent can be the fire guard at the same time. First come, first serve!
       # self.test = 0

    def update(self, actions, tile_map,  living_creatures):

        self.ON = False
        for creature in living_creatures:
            if isinstance(creature, Survivor):

                # Check if the survivor is inside the activation area!
                if self.get_view_grid().collidepoint(creature.get_grid_pos()):
                    #print("FIRE!, Survivor in reach: {}".format(creature.ID))
                    
                    # If no one or the current survivor is the fire guard, apply the reward and turn the fire on.
                    if (self.FIRE_GUARD == -1) or (self.FIRE_GUARD == creature.ID):
                        self.FIRE_GUARD = creature.ID
                        creature.Score += creature.rewards["fire"]
                        creature.Statistics["specialisation"]["steps_as_fireguard"] +=1
                        creature.Statistics["rewards"]["reward_from_fire"] += creature.rewards["fire"]
                        creature.Statistics["rewards"]["reward_total"] = creature.Score

                        self.ON = True
                        #print("FIRE  // Agent {}: +{} new score: {}".format(agent.ID, agent.rewards["wolf"], agent.Score))


        # Switch the Wolf and Sheep Movement Speed depending on the fire status and add Energy to the agents!
        for creature in living_creatures:
            if isinstance(creature, Survivor):
                if self.ON:
                    creature.Energy += 0.25
            if isinstance(creature, Wolf):
                if self.ON:
                    creature.MOVE_EVERY_N_STEPS = creature.SLOW
                else:
                    creature.MOVE_EVERY_N_STEPS = creature.FAST

            if isinstance(creature, Sheep):
                if self.ON:
                    creature.MOVE_EVERY_N_STEPS = creature.FAST
                else:
                    creature.MOVE_EVERY_N_STEPS = creature.SLOW

        # Switch the image based on the fire status
        if self.ON:
            self.Statistics["specialisation"]["steps_fire_on"] +=1
            self.image = self.IMAGE_2 # Fire on
        else:
            self.Statistics["specialisation"]["steps_fire_off"] +=1
            #self.Statistics["specialisation"]["fire_switches"] +=1
            self.FIRE_GUARD = -1
            self.image = self.IMAGE   # Fire off
        
        # return no dirty sprites since the fire is not moving anywhere
        return []

    def scale_to(self, tile_size, offset):
        self.IMAGE_2  = pygame.transform.scale(self.BASE_IMAGE_2, (tile_size * self.GRID_W, tile_size * self.GRID_H))
        super(Fireplace, self).scale_to(tile_size, offset)
    
    def reset(self, new_pos, reset_stats=False):
        #self.test = 0
        self.ON = False
        self.FIRE_GUARD = -1
        super(Fireplace, self).reset(new_pos, reset_stats)

class Sheep(pygame.sprite.DirtySprite, GameObject):

    # Action Mapping for Sheep, defines possible actions!
    BASIC_ACTIONS = { FORWARD : MOVE_FORWARD,
                      TURN_L  : ANIMAL_TURN_LEFT, 
                      TURN_R  : ANIMAL_TURN_RIGHT,
                      TURN_F  : ANIMAL_TURN_FULL,
                      STAY    : NOOP
                    }

    def __init__(self, ID, start_pos, tile_size=8, offset=0 ):
        
        pygame.sprite.Sprite.__init__(self)

        SheepArea = ViewPort(5,5,5,4)
        GameObject.__init__(self, ID, start_pos, tile_size, offset, (1,2), Sheep.BASIC_ACTIONS, SHEEP.convert(), SheepArea, SHEEP_STATISTICS)

        self.SLOW = 6
        self.FAST = 2
        self.MOVE_EVERY_N_STEPS = self.SLOW
        self.WorldSteps = 0
        self.SHEPHERD = -1 # only one agent can be the sheeps shepherd at the same time. First come, first serve!

    def update(self, manual_actions, tile_map,  living_creatures):

        # increment the WorldSteps
        self.WorldSteps += 1

        # select an action
        action = self.select_move(manual_actions)

        # apply the chosen action
        self.move(action)
    
        # Check collisions and set the final position
        for point in self.Grid:
            colliding_map_tile = tile_map[point]
            
            if colliding_map_tile.TileType == map.EOW:
                self.set_back()
                self.Statistics["basics"]["collisions"] +=1
                break

            if colliding_map_tile.TileType == map.WATER:
                self.set_back()
                self.move(TURN_F)
                self.Statistics["basics"]["collisions"] +=1
                break

            # The Sheep is blocked by every other creature
            for creature in living_creatures:
                if point in creature.get_collision_grid():

                    if isinstance(creature, Sheep):
                        if self.ID != creature.ID:
                            self.set_back()
                            self.Statistics["basics"]["collisions"] +=1
                            break
                    elif isinstance(creature, Survivor):
                        self.set_back()
                        self.Statistics["basics"]["collisions"] +=1
                        creature.Statistics["specialisation"]["blocked_sheep"] +=1
                        break
                    else:                   
                        self.set_back()
                        self.Statistics["basics"]["collisions"] +=1
                        break

        # Now that we have the final position update the map on this position
        for point in self.Grid:
            tile_map[point].update(self)

        # With the final position search for shepherds
        has_a_shepherd = False
        for creature in living_creatures:
            if isinstance(creature, Survivor):

                # Check if the survivor is inside the activation area!
                if self.get_view_grid().collidepoint(creature.get_grid_pos()):
                    #print("SHEPARD, Agent in reach: {}".format(agent.ID))

                    # If the sheep has no shepherd or the survivor is already its shepherd, apply the reward and set "new" shepherd
                    if (self.SHEPHERD == -1) or (self.SHEPHERD == creature.ID):
                        self.SHEPHERD = creature.ID
                        creature.Score += creature.rewards["sheep"]
                        has_a_shepherd = True

                        creature.Statistics["specialisation"]["steps_as_shepherd"] +=1
                        creature.Statistics["rewards"]["reward_from_sheep"] += creature.rewards["sheep"]
                        creature.Statistics["rewards"]["reward_total"] = creature.Score
                        self.Statistics["specialisation"]["steps_with_shepherd"] +=1
                
                        #print("SHEEP // Agent {}: +{} new score: {}".format(creature.ID, creature.rewards["sheep"], creature.Score))

        # If there was no survivor in range, reset the sheeps "ownership"
        if has_a_shepherd:
            for creature in living_creatures:
                if isinstance(creature, Survivor):
                    creature.Energy += 0.25
        elif not has_a_shepherd:
            self.SHEPHERD = -1
            self.Statistics["specialisation"]["steps_without_shepherd"] +=1
            #self.Statistics["specialisation"]["shepherd_switches"] +=1
        
        # Return all sprites that need redrawing
        return self.update_render_pos(rotate=True, tile_map=tile_map)

    def select_move(self, manual_actions=[]):

            if self.MOVE_EVERY_N_STEPS == self.SLOW:
                self.Statistics["basics"]["steps_slow"] +=1
            elif self.MOVE_EVERY_N_STEPS == self.FAST:
                self.Statistics["basics"]["steps_slow"] +=1

            # The basic movement of the Sheep. Every n world steps select a move with some probability.
            if (self.WorldSteps % self.MOVE_EVERY_N_STEPS == 0):
                self.Statistics["basics"]["steps_total"] +=1

                action_prob = np.random.random()
                if action_prob < 0.1:
                    action = TURN_L
                elif action_prob < 0.2:
                    action = TURN_R
                elif action_prob < 0.9:
                    action = FORWARD
                else:
                    action = STAY  
            else:
                action = STAY
              
            # If the Game is set to MANUAL or RANDOM mode overwrite the action
            if MANUAL:
                # Select the same action as player x for manuel play/testing
                self.ACTIONS = { K_UP    : MOVE_FORWARD,     K_DOWN  : MOVE_BACKWARD,    K_LEFT   : MOVE_LEFT, 
                                 K_RIGHT : MOVE_RIGHT,       K_COMMA : ANIMAL_TURN_LEFT, K_PERIOD : ANIMAL_TURN_RIGHT,
                                 FORWARD : MOVE_FORWARD,     TURN_L  : ANIMAL_TURN_LEFT, TURN_R   : ANIMAL_TURN_RIGHT,
                                 TURN_F  : ANIMAL_TURN_FULL, STAY    : NOOP,             K_F15    : NOOP}
                action = manual_actions[0]
            
            elif RANDOM_NPC:
                action = self.select_random_move([FORWARD, TURN_L, TURN_R, STAY])

            return action

class Wolf(pygame.sprite.DirtySprite, GameObject):

    # Action Mapping for Wolf, defines possible actions!
    BASIC_ACTIONS = { FORWARD : MOVE_FORWARD,
                      TURN_L  : ANIMAL_TURN_LEFT, 
                      TURN_R  : ANIMAL_TURN_RIGHT,
                      TURN_F  : ANIMAL_TURN_FULL,
                      STAY    : NOOP
                    }

    def __init__(self, ID, start_pos, tile_size=8, offset=0 ):
        
        pygame.sprite.Sprite.__init__(self)

        WolfArea = ViewPort(8,8,8,8)
        GameObject.__init__(self, ID, start_pos, tile_size, offset, (1,2), Wolf.BASIC_ACTIONS, WOLF.convert(), WolfArea, WOLF_STATISTICS)
        self.DMG = 50
        self.SLOW = 4
        self.FAST = 1
        self.MOVE_EVERY_N_STEPS = self.FAST
        self.WorldSteps = 0
        self.StepsAlive = 0

    def update(self, manual_actions, tile_map,  living_creatures):

        # increment the WorldSteps
        self.WorldSteps += 1
        self.StepsAlive += 1
        #print("Wolf is {} Steps alive.".format(self.StepsAlive))

        # Check if a sheep is in the hunting range
        HUNTING, SheepPos = self.snoop(living_creatures)

        # select an action
        action = self.select_move(HUNTING, SheepPos, manual_actions)

        # apply the chosen action
        self.move(action)

        # check collisions with map and game objects
        dead_sheep_sprites = ()
        for point in self.Grid:

            colliding_map_tile = tile_map[point]
            
            if colliding_map_tile.TileType == map.EOW:
                self.set_back()
                self.Statistics["basics"]["collisions"] +=1
                break

            if colliding_map_tile.TileType == map.WATER:
                self.set_back()
                self.move(TURN_F)
                self.Statistics["basics"]["collisions"] +=1

                if HUNTING:
                    # attempt another move to better escape from "trapped" situatios
                    self.move(self.select_random_move([FORWARD, TURN_L, TURN_R]))
                    
                    # check collisions with mao again.
                    for new_point in self.Grid:
                        
                        new_map_tile = tile_map[new_point]

                        if new_map_tile.TileType == map.WATER or new_map_tile.TileType == map.EOW:
                            self.set_back()
                            self.Statistics["basics"]["collisions"] +=1
                            break
                        
                        sheep = self.check_object_collisions(new_point, tile_map, living_creatures)
                        if sheep: dead_sheep_sprites = sheep
                break

            sheep = self.check_object_collisions(point, tile_map, living_creatures)
            if sheep: dead_sheep_sprites = sheep

        # Add the sprites points from the dead sheep to our self.OldGrid for redrawing!
        self.OldGrid += dead_sheep_sprites
        # Return all sprites that need redrawing
        return self.update_render_pos(rotate=True, tile_map=tile_map)

    def check_object_collisions(self, point, tile_map, living_creatures):
        
        dead_sheep_sprites = ()
        for creature in living_creatures:
            if point in creature.get_collision_grid():

                if isinstance(creature, Wolf):
                    if self.ID != creature.ID:
                        self.set_back()
                        self.Statistics["basics"]["collisions"] +=1
                        break

                elif isinstance(creature, Sheep):
                        #print("WOLF KILLS THE SHEEP!")

                        # Save the sheeps position for redrawing later
                        dead_sheep_sprites = creature.get_collision_grid()

                        # Find a new random position for the sheep and reset
                        new_pos = utils.free_random_position( tile_map, living_creatures, forbidden_types=[map.WATER], min_space=creature.GRID_MAX)
                        creature.reset(new_pos)

                        self.Statistics["specialisation"]["catched_sheep"] +=1
                        creature.Statistics["specialisation"]["catched_by_wolf"] +=1

                        #creature.kill()
                        break

                elif isinstance(creature, Survivor):

                    # Apply the attack damage of the wolf to the survivor, reset position
                    creature.Energy -= self.DMG
                    self.set_back()
                    self.Statistics["specialisation"]["attacked_survivor"] +=1
                    creature.Statistics["specialisation"]["hits_from_wolf"] +=1

                    print("WOLF attacks Agent {} -{} dmg, new energy: {}!".format(creature.ID, self.DMG, creature.Energy))
                    break
                else:
                    # Every other game object is just unwalkable for the wolf
                    self.set_back()
                    break

        return dead_sheep_sprites

    def select_random_move(self, with_stay=True):
        if with_stay:
            return np.random.choice([FORWARD, TURN_R, TURN_L, STAY])
        else:
            return np.random.choice([FORWARD, TURN_R, TURN_L])

    def snoop(self, living_creatures):
        '''
        This method checks if a sheep is in the hunting area
        '''
        HUNTING = False
        SheepPos = ()

        for creature in living_creatures:
            if isinstance(creature, Sheep):
                
                hunting_area = self.get_view_grid()
                the_sheep = creature.get_collision_grid()

                for point in the_sheep:
                    if hunting_area.collidepoint(point):
                        HUNTING = True
                        SheepPos = creature.get_grid_pos()
                        #print("WOLF spottet a sheep, hmmm.....")
                        break

        return HUNTING, SheepPos

    def select_move(self, hunting, victim_pos, manual_actions=[]):


        if self.MOVE_EVERY_N_STEPS == self.SLOW:
            self.Statistics["basics"]["steps_slow"] +=1
        elif self.MOVE_EVERY_N_STEPS == self.FAST:
            self.Statistics["basics"]["steps_slow"] +=1

        action = STAY
        # The basic movement of the Wolf. Every n world steps select a move with some probability.
        if (self.WorldSteps % self.MOVE_EVERY_N_STEPS == 0):
            self.Statistics["basics"]["steps_total"] +=1

            # If the wolf is in hunting mode, select a special move, else one of the basic moves.
            if hunting:
                wolf  = self.get_grid_pos()
                sheep = victim_pos
                action   = self.select_hunt_move(hunter_pos=wolf, victim_pos=sheep)
                self.Statistics["specialisation"]["steps_hunting"] +=1
            else:
                
                    action_prob = np.random.random()
                    if action_prob < 0.1:
                        action = TURN_L
                    elif action_prob < 0.2:
                        action = TURN_R
                    elif action_prob < 0.9:
                        action = FORWARD
                    else:
                        action = STAY

        # If the Game is set to MANUAL or RANDOM mode overwrite the action
        if MANUAL:
            # Select the same action as player x for manuel play/testing
            self.ACTIONS = { K_UP    : MOVE_FORWARD,     K_DOWN  : MOVE_BACKWARD,    K_LEFT   : MOVE_LEFT, 
                             K_RIGHT : MOVE_RIGHT,       K_COMMA : ANIMAL_TURN_LEFT, K_PERIOD : ANIMAL_TURN_RIGHT,
                             FORWARD : MOVE_FORWARD,     TURN_L  : ANIMAL_TURN_LEFT, TURN_R   : ANIMAL_TURN_RIGHT,
                             TURN_F  : ANIMAL_TURN_FULL, STAY    : NOOP,             K_F15    : NOOP}
            action = manual_actions[1]
        
        elif RANDOM_NPC:
            action = self.select_random_move([FORWARD, TURN_L, TURN_R, STAY])

        return action

    def select_hunt_move(self, hunter_pos, victim_pos):

        diff_x = hunter_pos[0] - victim_pos[0]
        diff_y = hunter_pos[1] - victim_pos[1]

        reduce = diff_x if abs(diff_x) >= abs(diff_y) else diff_y
        #print("Wolf: {}, Sheep: {}, Diff: ({},{}, Reduce {})".format(hunter_pos, victim_pos, diff_x, diff_y, reduce))

        if reduce == diff_x:
            # again not smart but clear
            if diff_x > 0:
                if self.Pos[2]   == UP:    return TURN_L                    
                elif self.Pos[2] == DOWN:  return TURN_R                  
                elif self.Pos[2] == RIGHT: return TURN_F                    
                elif self.Pos[2] == LEFT:  return FORWARD
                else: return Wolf.STAY
            else:
                if self.Pos[2]   == UP:    return TURN_R                   
                elif self.Pos[2] == DOWN:  return TURN_L                  
                elif self.Pos[2] == RIGHT: return FORWARD                    
                elif self.Pos[2] == LEFT:  return TURN_F
                else: return Wolf.STAY
        else:
            if diff_y > 0:
                if self.Pos[2]   == UP:    return FORWARD                   
                elif self.Pos[2] == DOWN:  return TURN_F                 
                elif self.Pos[2] == RIGHT: return TURN_L                  
                elif self.Pos[2] == LEFT:  return TURN_R
                else: return Wolf.STAY
            else:
                if self.Pos[2]   == UP:    return TURN_F           
                elif self.Pos[2] == DOWN:  return FORWARD                 
                elif self.Pos[2] == RIGHT: return TURN_R                  
                elif self.Pos[2] == LEFT:  return TURN_L
                else: return Wolf.STAY

    def reset(self, new_pos, reset_stats=False):
        self.WorldSteps = 0
        self.StepsAlive = 0
        super(Wolf, self).reset(new_pos, reset_stats)
        