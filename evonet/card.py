__author__ = 'Johannes Theodoridis'

import pygame
import numpy as np

from .game_objects import Sheep, Wolf, Fireplace

class Card(pygame.Surface):

    # Some colors
    black  = (0,0,0)
    white  = (255,255,255)
    white2 = (244,244,244)
    grey   = (130,130,130)
    grey2  = (230,230,230)
    dark   = (51,51,51)
    dark2  = (42,49,59)
    blue   = (45,162,225)
    blue2  = (35,192,234)
    cyan   = (21,163,186)
    cyan2  = (0,186,175)
    orange = (251,140,0)

    FIX_TILE_SIZE = 8 # a fixed size for the card. Every observation we be rescaled to a representation with TileSize of 8 pixels.

    def __init__(self, width, height, Title):

        # the size of the map in grid points
        # self.MAP_WIDTH  = map_size[0]
        # self.MAP_HEIGHT = map_size[1]
        # self.MAP_GRID_H = map_grid_h

        # some margins
        self.margin_out = 10
        self.margin_in  = 10

        #w = 2 * self.margin_in + 2 * self.margin_out + 100
        #h = 2 * self.margin_in + 2 * self.margin_out + self.MAP_HEIGHT * Card.FIX_TILE_SIZE
        # w = min_width
        # h = min_height
        pygame.Surface.__init__(self, (width, height))
        
        self.TitleString = Title
        self.Title_y = 0
        self.Active     = False
        #self.TileSize   = tile_size
       
        # Standard colors
        self.TitleColor       = Card.white2
        self.TitleBg_Active   = Card.orange
        self.TitleBg_Inactive = Card.grey
        self.StatsColor       = Card.white2
        self.CardColor        = Card.dark2

        # Standard font
        self.TitleFont = pygame.font.SysFont("monaco", 18, False, False)
        self.StatsFont = pygame.font.SysFont("monaco", 15, False, False)

        # self.update_static(self.Active)

    def update(self, active):

        if self.Active != active:
            self.Active = not self.Active
            self.update_static(self.Active)

    def scale_to(self, tile_size):
        # maybe some TileSize depending rescaling? hm...
        # Currently fixed size
        return None

    def update_static(self, active):

        # Clear the Card
        self.fill((0,0,0))
        
        # Draw the Card background
        background = (self.margin_out, 0, self.get_width() - 2 * self.margin_out, self.get_height())
        pygame.draw.rect(self, self.CardColor, background)

        # Draw the Card title
        self.Title_y = self.draw_title(active)
        return self.Title_y

    def empty_position(self, position):

        ending_at_x = position[0]
        ending_at_y = position[1] + self.StatsFont.get_height() #+ self.margin_in
        return (ending_at_x, ending_at_y)

    def draw_observation(self, raw_image, position):

        x = self.margin_in + self.margin_out + position[0]
        y = position[1]

        self.blit(raw_image, (x,y))

        ending_at_x = x + raw_image.get_width() 
        ending_at_y = y + raw_image.get_height() #+ self.margin_in
        return (ending_at_x, ending_at_y)

    def draw_statistic(self, text_string, position, color=None, bg_color=None):
        '''
        This method will render some text_string as statistic.
        X wise the outer and inner margin is applied by default, allowing for an extra offset through the position[0] argument.
        Y wise no margin is applied
        '''
        x = self.margin_in + self.margin_out + position[0]
        y = position[1]

        # set colors by user or default
        if color    is None: color = self.StatsColor
        if bg_color is None: bg_color = self.CardColor
        
        # draw the text to the surface
        Text = self.StatsFont.render(text_string, 1, color, bg_color)
        self.blit(Text,(x,y))

        # returns the ending x and y pixel positions inside the card. Those can be used in later calls.
        ending_at_x = x + Text.get_width()
        ending_at_y = y + Text.get_height() #+ self.margin_in
        return (ending_at_x, ending_at_y)

    def draw_line(self, thickness, color, position, full_width=False, y_margin=None):
        '''
        Draws a line. Before and after the line we apply an y_margin
        '''
        if y_margin is None: y_margin = self.margin_in
        
        if full_width:
            x = 0
            width = self.get_width()
        else:
            x = self.margin_in + self.margin_out + position[0]
            width = self.get_width() - 2 * self.margin_in - 2 * self.margin_out 
        
        y = position[1] + y_margin
        the_line = (x, y, width, thickness)

        pygame.draw.rect(self, color, the_line)

        ending_at_x = x + width 
        ending_at_y = y + thickness + y_margin
        return (ending_at_x, ending_at_y)

    def draw_title(self, active):

        # Draw a Title depending on the ACTIVE status
        if active:
            # Calculate dimensions
            TitleText = self.TitleFont.render(self.TitleString, 1, self.TitleColor, self.TitleBg_Active)
            TitleBg   = (0, 0, self.get_width(), TitleText.get_height() + 2 * self.margin_in)
            
            # Draw background and title
            pygame.draw.rect(self, self.TitleBg_Active, TitleBg)
            self.blit(TitleText, (self.margin_out + self.margin_in, self.margin_in))
           
            # Calculate and draw decoration
            TitleBottom = TitleBg[1] + TitleBg[3]
            deco_left  = [(              0, TitleBottom                       ),
                               (self.margin_out, TitleBottom                  ),
                               (self.margin_out, TitleBottom + self.margin_out)]
            
            deco_right = [(self.get_width()                  , TitleBottom                 ),
                               (self.get_width() - self.margin_out, TitleBottom                 ),
                               (self.get_width() - self.margin_out, TitleBottom + self.margin_out)]

            pygame.draw.polygon(self, self.TitleBg_Active, deco_left)
            pygame.draw.polygon(self, self.TitleBg_Active, deco_right)
      
        else:
            # Calculate dimensions
            TitleText = self.TitleFont.render(self.TitleString, 1, self.TitleColor, self.TitleBg_Inactive)
            TitleBg   = (self.margin_out, 0, self.get_width() - 2 * self.margin_out, TitleText.get_height() + 2 * self.margin_in)
            TitleBottom = TitleBg[1] + TitleBg[3]

            # Draw background and title
            pygame.draw.rect(self,self.TitleBg_Inactive, TitleBg)
            self.blit(TitleText, (self.margin_out + self.margin_in, self.margin_in))

        # return the bottom y position so it can be used to place other objects.
        ending_at_y = TitleBottom + self.margin_in
        return ending_at_y

    def reset(self, active=False):
        self.update_static(active)

class AgentCard(Card):

    def __init__(self, agent_entry, map_dimension_y, tile_size, basic=True, detail=True, observation=True):


        self.BASIC_INFO  = basic
        self.DETAIL_INFO = detail
        self.OBSERVATION = observation

        # Calculate the total size of the card to init base class
        self.FIX_TILE_SIZE = 8
        self.MAP_H = map_dimension_y * self.FIX_TILE_SIZE


        if tile_size == self.FIX_TILE_SIZE:
            self.OBSERVATION = False
        
        self.TileSize   = tile_size

        self.AgentEntry = agent_entry
        self.ID         = agent_entry["ID"]
        self.Agent      = agent_entry["Agent"]
        self.Statistics = self.Agent.Statistics
        self.AgentView  = agent_entry["AgentView"]
        self.VIEW_W = self.AgentView.get_width() 
        self.VIEW_H = self.AgentView.get_height()
        
        self.ViewPort_GRID_W = agent_entry["ViewPort_Grid"][0]
        self.ViewPort_GRID_H = agent_entry["ViewPort_Grid"][1]
        self.Scaled_VIEW_W   = self.ViewPort_GRID_W * self.FIX_TILE_SIZE
        self.Scaled_VIEW_H   = self.ViewPort_GRID_H * self.FIX_TILE_SIZE

        self.VIEW_Y  = 0
        self.BASIC_STATS_Y = 0
        self.DETAIL_STATS_Y = 0
        self.OBSERVATION_Y = 0

        self.MIN_WIDTH  = 202
        self.MIN_HEIGHT = 0

        Card.__init__(self, 0,0, "Calculating size...")
        self.CARD_WIDTH = self.calculate_card_width()
        self.CARD_HEIGHT = self.update_static()
        Card.__init__(self, self.CARD_WIDTH, self.CARD_HEIGHT, "Agent: {}".format(self.ID))

        self.update_static(self.Active)

    def calculate_card_width(self):

        Observation_W        = (self.VIEW_W + 2 * self.margin_in + 2 * self.margin_out)
        Scaled_Observation_W = (self.Scaled_VIEW_W  + 2 * self.margin_in + 2 * self.margin_out)

        return max(self.MIN_WIDTH, Observation_W, Scaled_Observation_W)

    def update(self, active=False):
        super(AgentCard,self).update(active)

        # Reasign our Agent View because its
        self.AgentView  = self.AgentEntry["AgentView"]
        self.Statistics = self.Agent.Statistics

        next_x = 0
        next_y = self.VIEW_Y

        if self.TileSize != self.FIX_TILE_SIZE:
            ScaledView = pygame.transform.scale(self.AgentView, ( self.Scaled_VIEW_W, self.Scaled_VIEW_H ))
            next_x, next_y = self.draw_observation(ScaledView, (0, next_y))
        else:
            next_x, next_y = self.draw_observation(self.AgentView, (0, next_y))

        # Draw Stats
        if self.BASIC_INFO:
            next_y = self.BASIC_STATS_Y
            if active: color = Card.orange
            else:      color=None
            next_x, next_y = self.draw_statistic("Energy: {:3.1f}".format(self.Agent.Energy), (0,next_y), color)
            next_x, next_y = self.draw_statistic("Reward: {:3.1f}".format(self.Statistics["rewards"]["reward_total"]), (0,next_y), color)

        if self.DETAIL_INFO:
            next_y = self.DETAIL_STATS_Y

            stats = self.get_detailed_statistics()

            next_x, next_y = self.draw_statistic("Food:  {} | {}".format(stats[0][0], stats[0][0]), (0,next_y), stats[0][2])
            next_x, next_y = self.draw_statistic("Fire:  {} | {}".format(stats[1][0], stats[1][1]), (0,next_y), stats[1][2])
            next_x, next_y = self.draw_statistic("Sheep: {} | {}".format(stats[2][0], stats[2][1]), (0,next_y), stats[2][2])
            next_x, next_y = self.draw_statistic("Wolf:  {} | {}".format(stats[3][0], stats[3][1]), (0,next_y), stats[3][2])

        if self.OBSERVATION:
            self.draw_observation(self.AgentView, (0, self.OBSERVATION_Y))

    def get_detailed_statistics(self):

        food  = [self.Statistics["specialisation"]["collected_food"],     self.Statistics["rewards"]["reward_from_food"],  None]
        fire  = [self.Statistics["specialisation"]["steps_as_fireguard"], self.Statistics["rewards"]["reward_from_fire"],  None]
        sheep = [self.Statistics["specialisation"]["steps_as_shepherd"],  self.Statistics["rewards"]["reward_from_sheep"], None]
        wolf  = [self.Statistics["specialisation"]["catched_wolf"],       self.Statistics["rewards"]["reward_from_wolf"],  None]
        stats = [food, fire, sheep, wolf]

        # find the entry the currently contributes the most to the reward and set a highlight color 
        rewards = [entry[1] for entry in stats]
        max_reward = max(rewards)
        if max_reward > 0:
            index_max_reward = np.argmax(rewards)
            stats[index_max_reward][2] = Card.blue

        return stats

    def scale_to(self, tile_size):
        # maybe some TileSize depending rescaling? hm...
        # currently fixed size
        return None

    def update_static(self, active=False):
        next_y = super(AgentCard,self).update_static(active)
        self.VIEW_Y = next_y

        # draw window
        next_y += (self.Scaled_VIEW_H + self.margin_in)
        next_x, next_y = self.draw_statistic("({}x{}) pixels".format(self.AgentView.get_width(), self.AgentView.get_height()) , (0,next_y))

        if self.BASIC_INFO:
            next_x, next_y = self.draw_line(2, Card.grey,(0,next_y))
            self.BASIC_STATS_Y  = next_y
            next_x, next_y = self.empty_position((0,next_y)) # Energy
            next_x, next_y = self.empty_position((0,next_y)) # Reward

        if self.DETAIL_INFO:
            next_x, next_y = self.draw_line(2, Card.grey,(0,next_y))
            self.DETAIL_STATS_Y  = next_y
            next_x, next_y = self.empty_position((0,next_y)) # Food
            next_x, next_y = self.empty_position((0,next_y)) # Fire
            next_x, next_y = self.empty_position((0,next_y)) # Sheep
            next_x, next_y = self.empty_position((0,next_y)) # Wolf

        if self.OBSERVATION:
            # if the current y position is in close range to the map end, allign for a nicer view!
            next_y =  self.y_allign_to(self.MAP_H, next_y)
          
            next_x, next_y = self.draw_line(4, Card.black,(0,next_y), True)
            next_x, next_y = self.draw_statistic("Observation:" , (0,next_y))
            next_y += self.margin_in
            self.OBSERVATION_Y = next_y
            next_y += (self.AgentView.get_height())

        next_y = self.y_allign_to(self.MAP_H, next_y)
        return next_y + self.margin_in


    def y_allign_to(self, anchor_pos, y_pos, activation_range=150):

        if (0 < (anchor_pos - y_pos) < activation_range):
            #print("ALLGIN")
            return (anchor_pos - self.margin_in)
        else:
            return y_pos

class StatisticsCard(Card):

    def __init__(self, map_statistics, map_meta, npc_list, rewards):

        self.MAP_INFO = True
        self.NPC_INFO = True

        self.map = map_statistics
        self.MAP_WIDTH  = map_meta["width"]  - 2 # minus border
        self.MAP_HEIGHT = map_meta["height"] - 2 # minus border
        self.rewards = rewards
    
        self.NPCs = npc_list
        self.NPC_Y = 0

        # Init a first time onlyfor dimension calculations
        Card.__init__(self, 0, 0, "Calculating size...")
        self.CARD_HEIGHT = self.update_static()
        self.CARD_WIDTH  = 490

        # Now init with the correct dimensions
        Card.__init__(self, self.CARD_WIDTH, self.CARD_HEIGHT, "SurvivalBox statistics")
        self.TitleBg_Active   = Card.blue
        self.TitleBg_Inactive = Card.blue

        self.CARD_HEIGHT = self.update_static()
        
    def update(self, npc_list, active=False):
        super(StatisticsCard, self).update(active)

        if self.NPC_INFO:
            # draw npc stats
            next_x = 0
            next_y = self.NPC_Y
            for NPC in npc_list:

                stats = NPC.Statistics["specialisation"]
                ID = NPC.ID

                if isinstance(NPC, Sheep):
                    FOOD = stats["collected_food"]
                    WS   = stats["steps_with_shepherd"]
                    WOS  = stats["steps_without_shepherd"]
                    DIED = stats["catched_by_wolf"]
                    next_x, next_y  = self.draw_statistic("Sheep {}: food {} | shepherd ({},{}) | died {}".format(ID, FOOD, WS, WOS, DIED),(0, next_y))
                
                elif isinstance(NPC, Wolf):

                    HUNTING = stats["steps_hunting"]
                    SHEEP  = stats["catched_sheep"]
                    CATCHED   = stats["catched_by_survivor"]
                    ATTACK = stats["attacked_survivor"]
                    next_x, next_y  = self.draw_statistic("Wolf  {}: hunting {} | sheeps {} | attacks {} | died {}".format(ID, HUNTING, SHEEP, ATTACK, CATCHED),(0, next_y))
                
                elif isinstance(NPC, Fireplace):
                    ON       = stats["steps_fire_on"]
                    OFF      = stats["steps_fire_off"]
                    SWTICHES = stats["fire_switches"]
                    next_x, next_y  = self.draw_statistic("Fire  {}: on {} | off {} | switches {}".format(ID, ON,OFF,SWTICHES),(0, next_y))
                else:
                    raise Exception("Not a valid NPC type!")

    def update_static(self, active=False):
        # update title active status
        next_y = super(StatisticsCard, self).update_static(active)

        next_x, next_y = self.draw_statistic("Rewards: Food  (+{}) / Fire (+{})".format(self.rewards["grass"], self.rewards["fire"]), (0, next_y))
        next_x, next_y = self.draw_statistic("         Sheep (+{}) / Wolf (+{})".format(self.rewards["sheep"], self.rewards["wolf"]), (0, next_y))

        if self.MAP_INFO:
            next_x, next_y = self.draw_line( 2, Card.grey, (0, next_y))
            next_x, next_y = self.draw_statistic("Map:     {} x {} ({})".format(self.MAP_WIDTH, self.MAP_HEIGHT, self.map["total"]), (0, next_y))
            next_x, next_y = self.draw_statistic("Tiles:   {} Water | {} Dirt | {} Grass".format(self.map["water"], self.map["dirt"], self.map["grass"]),(0, next_y))

        if self.NPC_INFO:
            next_x, next_y = self.draw_line( 4, Card.black, (0, next_y), True)
            next_x, next_y = self.draw_statistic("NPCs:",(0, next_y))
            self.NPC_Y = next_y + self.margin_in
            next_y = self.NPC_Y

            for npc in self.NPCs:
                next_x, next_y = self.empty_position((next_x, next_y))

        return next_y + self.margin_in
