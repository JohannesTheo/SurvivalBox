__author__ = 'Johannes Theodoridis'

# standard imports

# third party imports
import numpy as np
import pygame
import pickle

# local imports
from . import map
from . import utils
from .game_objects import Survivor, ViewPort, Fireplace, Sheep, Wolf, create_marker_rect
from .card import Card, AgentCard, StatisticsCard

class EvoWorld():
    '''
    A class that holds the GameState in:
    TileMap, AgentList
    Applies dynamics based on agent actions and
    can render the World State as well as the Agent Views
    '''
    def __init__(self, map_width, map_height, water_percentage, init_tile_size, rewards):

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
        self.rewards = rewards

        self.NumAgents = 0
        self.NumSheeps = 0
        self.NumWolfs  = 0
        self.NumFires  = 0

        self.AgentList = {}
        self.NPC_List  = []
        self.CardList  = {}
        self.StatisticsCard = None
        self.CARD_MARGIN = 10
        self.rng = None
        self.ActivePlayer = 0

        self.DRAW_VIEW_AREAS = False
        self.DRAW_MARKER = False
        self.RENDER_CARDS       = True
        self.RENDER_SCALED_MAP  = True

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
        self.game_objects_group     = pygame.sprite.RenderUpdates() # A group with all "living" game_objects
        self.survivor_group         = pygame.sprite.RenderUpdates() # Only the living agents
        self.npc_group              = pygame.sprite.RenderUpdates() # All NPC objects like sheeps, wolfs and fires

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
    

    def init(self, rng, num_agents=1, view_port_dimensions={}, num_sheep=1, num_wolf=1, num_fire=1):

        # Set the rng
        self.rng = rng
        
        # Set the number of agents
        self.NumAgents = num_agents
        self.NumSheeps = num_sheep
        self.NumWolfs  = num_wolf
        self.NumFires  = num_fire

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

        # Create the Game Objects
        self.create_game_objects(self.NumSheeps, self.NumWolfs, self.NumFires)

        # Reset the GameState
        self.reset()

        # Create cards for human friendly rendering interface
        self.create_cards()

    def create_agents(self, num_agents):
        self.AgentList = {}
        for ID in range(num_agents):

            start_pos = utils.free_random_position(self.TileMap, self.game_objects_group.sprites())
            NewAgent = Survivor(ID, self.rewards, self.ViewPort, start_pos, self.TileSize, self.ClippingBorder)
            
            self.AgentList[ID] = { "ID" : ID, "Agent" : NewAgent, "ViewPort_Grid" : NewAgent.ViewPort.get_grid_dimensions(), "ViewPort" : None, "AgentView" : None}
            # add to groups
            self.everything_group.add(NewAgent)
            self.game_objects_group.add(NewAgent)
            self.survivor_group.add(NewAgent)

    def create_game_objects(self, num_sheep, num_wolf, num_fire):
        self.NPC_List = []

        for ID in range(num_sheep):
            start_pos = utils.free_random_position(self.TileMap, self.game_objects_group.sprites(), forbidden_types=[map.WATER], min_space=2)
            sheep = Sheep(ID, start_pos, self.TileSize, self.ClippingBorder)
            
            self.everything_group.add(sheep)
            self.game_objects_group.add(sheep)
            self.npc_group.add(sheep)
            self.NPC_List.append(sheep)

        for ID in range(num_wolf):
            start_pos = utils.free_random_position(self.TileMap, self.game_objects_group.sprites(), forbidden_types=[map.WATER], min_space=2)
            wolf = Wolf(ID, start_pos, self.TileSize, self.ClippingBorder)
            
            self.everything_group.add(wolf)
            self.game_objects_group.add(wolf)
            self.npc_group.add(wolf)
            self.NPC_List.append(wolf)

        for ID in range(num_fire):
            start_pos = utils.free_random_position(self.TileMap, self.game_objects_group.sprites(), forbidden_types=[map.WATER], min_space=4)
            fp = Fireplace(ID, start_pos, self.TileSize, self.ClippingBorder)
            
            self.everything_group.add(fp)
            self.game_objects_group.add(fp)
            self.npc_group.add(fp)
            self.NPC_List.append(fp)

    def create_cards(self):
        self.CardList = {}
        self.StatisticsCard = None

        #if self.RENDER_CARDS:
        
        for agent in self.AgentList:
            ID = self.AgentList[agent]["ID"]
            self.CardList[ID] = AgentCard(self.AgentList[agent],
                                          self.MAPHEIGHT, 
                                          self.TileSize)

        self.StatisticsCard = StatisticsCard(self.START_MAP["Stats"], self.START_MAP["Meta"], self.NPC_List, self.rewards)

    def create_new_map(self, loaded_map=None):
        
        self.everything_group.empty()      
        self.bord_objects_group.empty()  
        self.eow_group.empty()
        self.map_group.empty()
        self.land_group.empty()
        self.water_group.empty()
        self.dirty_sprites_group.empty()

        self.game_objects_group.empty()
        self.survivor_group.empty()
        self.npc_group.empty()

        if loaded_map:
            self.START_MAP = loaded_map
            self.TileMap   = self.START_MAP["TileMap"]
        else:
            self.TileMap, self.START_MAP = map.generate_tile_map(self.MAPWIDTH, 
                                                                 self.MAPHEIGHT, 
                                                                 self.WATER_PERCENTAGE, 
                                                                 self.TileSize, 
                                                                 self.ClippingBorder)

        # TODO: We should do some sanity checks to make sure every GameObject will fit on the map!
        # Something like: Map must have more valid spawn places (for the biggest object) than > total num of objects
        # There must always be at least ONE free place of that size!

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
        for ID in self.AgentList:
            agent = self.AgentList[ID]["Agent"]

            # find a position that is no blocked by another GameObject
            new_pos = utils.free_random_position(self.TileMap, self.game_objects_group.sprites())
            agent.reset(new_pos, reset_stats=True)

            self.everything_group.add(agent)
            self.game_objects_group.add(agent)
            self.survivor_group.add(agent)

        for NPC in self.NPC_List:

            # find a position that is no blocked by another GameObject
            new_pos = utils.free_random_position(self.TileMap, self.game_objects_group.sprites(), forbidden_types=[map.WATER], min_space=NPC.GRID_MAX)
            NPC.reset(new_pos, reset_stats=True)

            self.everything_group.add(NPC)
            self.game_objects_group.add(NPC)
            self.npc_group.add(NPC)


        # redraw everything to have a "clean" screen and update the agent views
        self.everything_group.draw(self.MapSurface)
        self.update_agent_views()

        self.reset_cards()

        #self.create_cards()

    def reset_cards(self):
        for card in self.CardList:
            active = (card == self.ActivePlayer)
            self.CardList[card].reset(active)
         #   self.CardList[card].update(active)

        if self.StatisticsCard is not None:
            self.StatisticsCard.reset()

    def toggle_view_area(self):
        self.DRAW_VIEW_AREAS = not self.DRAW_VIEW_AREAS

    def toggle_marker(self):
        self.DRAW_MARKER = not self.DRAW_MARKER

    def toggle_cards(self):
        self.RENDER_CARDS = not self.RENDER_CARDS

        #if self.RENDER_CARDS:
         #   self.create_cards()

    def toggle_scaled_map(self):
        self.RENDER_SCALED_MAP  = not self.RENDER_SCALED_MAP

    def get_screen_dimensions(self):

        # size of the normal map
        width  = self.MapSurface.get_width()
        height = self.MapSurface.get_height()
        ClippingBorder = self.ClippingBorder   

        if self.RENDER_SCALED_MAP:
            # size of the scaled map
            if(self.TileSize < 8):
                ClippingBorder = (self.MAX_VIEW_PORT - 1) * 8
                w = (self.MAPWIDTH  * 8)
                h = (self.MAPHEIGHT * 8)
                width = w + 2 * ClippingBorder
                height += h + 2 * ClippingBorder + (ClippingBorder - self.ClippingBorder)

        if self.RENDER_CARDS:
            # starting points of the card calculations
            card_start_w = width
            card_start_h = ClippingBorder
            agent_card_h = 0

            for card in self.CardList:

                # alawys add the width
                width += self.CardList[card].get_width()
                width += self.CARD_MARGIN

                # add height only of it is more than the current height
                agent_card_h = self.CardList[card].get_height()
                card_h =  agent_card_h + 2 * ClippingBorder
                if card_h >= height:
                    height = card_h

            if self.StatisticsCard is not None:
                card_w = card_start_w + self.StatisticsCard.get_width() + self.CARD_MARGIN
                if card_w > width:
                    width = card_w - self.StatisticsCard.margin_out

                card_h = ClippingBorder + agent_card_h + 3 * self.CARD_MARGIN + self.StatisticsCard.get_height() + ClippingBorder
                if card_h >= height:
                    height = card_h #+ 2 * self.ClippingBorder

              #  self.ClippingBorder + agent_card + selfheight + 30 + 30
            width += ClippingBorder - self.CARD_MARGIN

        return (width, height)

    def scale_to(self, tile_size):

        # reset the game before resize to have an initial game state
        self.reset()

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

        ###############################################################################
        # UPDATE the game state
        ###############################################################################   

        # update (living) agents first
        for agent in self.survivor_group.sprites():

            # get all "living" game objects
            game_objects  = self.game_objects_group.sprites()

            # update the agent and add dirty sprites to the redraw group
            dirty_sprites = agent.update(action_list, self.TileMap, game_objects)
            self.dirty_sprites_group.add(dirty_sprites)

        # update npcs second
        for npc in self.npc_group:

            # get all "living" game objects
            game_objects  = self.game_objects_group.sprites()

            # update the NPC and add dirty sprites to the redraw group
            dirty_sprites = npc.update(action_list, self.TileMap, game_objects)
            self.dirty_sprites_group.add(dirty_sprites)

        ###############################################################################
        # DRAW the important stuff that is necessary to generate the agents observation
        ###############################################################################     
        
        # Draw the dirty map sprites
        #self.bord_objects_group.draw(self.MapSurface)
        self.dirty_sprites_group.draw(self.MapSurface)

         # Draw the "living" game objects AFTER the map to ensure that they are always visible
        self.game_objects_group.draw(self.MapSurface)

        # Update the Agent Views
        self.update_agent_views()

        ###############################################################################
        # DRAW the "unimportant" Stuff for a Preview or Demo: Only when Display = True
        ###############################################################################

        # Redraw Agents for Map View 
        self.survivor_group.draw(self.MapSurface)

        # Draw the a 'human friendly' version of the game
        if(self.TileSize < 8):

            if self.RENDER_SCALED_MAP:
                huge_w, huge_h, huge_offset = self.draw_huge_map(screen)
                self.draw_normal_map(screen, huge_offset - self.ClippingBorder, huge_h)
                self.draw_cards(screen, huge_w, huge_offset)
            else:
                w, h, offset = self.draw_normal_map(screen, 0,0)
                self.draw_cards(screen, w, offset)
        else:
            w,h,offset = self.draw_normal_map(screen, 0,0)
            self.draw_cards(screen, w, offset)

    def draw_cards(self, screen, offset_x, offset_y):
            margin = self.CARD_MARGIN # margin between Cards

            card_off = 0
            margin = self.CARD_MARGIN
            for card in self.CardList:
                # limit the amount of cards:
                if card > 11: break
                # check if card is the active player
                active = (card == self.ActivePlayer)
                # update the card
                self.CardList[card].update(active)
                # calculate position
                x = offset_x + (self.CardList[card].get_width() * (card%6)) + ((card%6) * margin)
              #  print(card%6, margin)
                y = offset_y
                card_off = y + self.CardList[card].get_height() 
               # margin = self.CardList[card].margin_out

                if card > 5:
                    y += self.CardList[card].get_height() + self.CARD_MARGIN
                # draw the card
                screen.blit(self.CardList[card], (x,y))

            if self.StatisticsCard is not None:
                self.StatisticsCard.update(self.NPC_List)
                screen.blit(self.StatisticsCard, (offset_x, card_off + 3 * self.CARD_MARGIN))

    def draw_huge_map(self, screen):
        
        Offset = (self.MAX_VIEW_PORT - 1) * 8

        w = (self.MAPWIDTH  * 8) + (2 * Offset)
        h = (self.MAPHEIGHT * 8) + (2 * Offset)
        HugeMap = pygame.transform.scale(self.MapSurface, (w,h))
        screen.blit(HugeMap,(0,0))

        for game_object in self.game_objects_group.sprites():
            # if isinstance(game_object, Sheep):
            
            if self.DRAW_VIEW_AREAS:
                ViewPort_scaled = game_object.get_view_scaled(  8, Offset)
                pygame.draw.rect(screen, (255,0,0), ViewPort_scaled, 2)

            if self.DRAW_MARKER:
                Marker_scaled   = game_object.get_marker_scaled(8, Offset) 
                pygame.draw.rect(screen, (0,255,255), Marker_scaled)

        # Draw a ViewPort representation
        for id in self.AgentList:

            agent = self.AgentList[id]["Agent"]

            if self.DRAW_VIEW_AREAS:
                ViewPort_scaled = agent.get_view_scaled(  8, Offset)
                pygame.draw.rect(screen, (0,0,255), ViewPort_scaled, 2)

            if self.DRAW_MARKER:
                # Calculate ViewPort and Orientation Marker with new scale and offset
                Marker_scaled   = agent.get_marker_scaled(8, Offset) 
                # Draw the scaled ViewPort and Marker
                pygame.draw.rect(screen, (228,228,228), Marker_scaled)

        return (w, h, Offset)

    def draw_normal_map(self, screen, x, y):

        screen.blit(self.MapSurface, (x,y))

        for game_object in self.game_objects_group.sprites():
            
            if self.DRAW_VIEW_AREAS:

                ViewPort = game_object.get_view()
                ViewPort.x += x
                ViewPort.y += y
                pygame.draw.rect(screen, (255,0,0), ViewPort, 2)

            if self.DRAW_MARKER:
                Marker   = game_object.get_marker()
                # Offset by x and y
                Marker.x += x
                Marker.y += y  
                pygame.draw.rect(screen, (0,255,255), Marker)

        # Draw a ViewPort representation
        for id in self.AgentList:

            agent = self.AgentList[id]["Agent"]
            # Get the agents ViewPort

            if self.DRAW_VIEW_AREAS:
                ViewPort = self.AgentList[id]["ViewPort"]
                ViewPort.x += x
                ViewPort.y += y 
                pygame.draw.rect(screen, (0,0,255), ViewPort, 2)

            if self.DRAW_MARKER:
                Marker   = agent.get_marker()
                # Offset by x and y
                Marker.x += x
                Marker.y += y
                # Draw the real ViewPort and Marker
                pygame.draw.rect(screen, (228,228,228), Marker)

        return (self.MapSurface.get_width(), self.MapSurface.get_height(), self.ClippingBorder)
