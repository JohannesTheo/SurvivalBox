__author__ = 'Johannes Theodoridis'

import pygame
import numpy 

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

    def __init__(self, agent_entry, map_grid_h, tile_size):

        # Calculate the total size of the card to init base class
        self.MAP_GRID_H = map_grid_h

        if tile_size < 8:
            self.margin_out = 10
            Card_h          = self.MAP_GRID_H * 8
            self.AgentView_w = agent_entry["ViewPort_Grid"][0] * 8
        else:
            self.margin_out = int(tile_size / 8) * 10
            Card_h      = self.MAP_GRID_H * tile_size
            self.AgentView_w = agent_entry["AgentView"].get_width()

        self.margin_in  = self.margin_out
        Card_w      = self.AgentView_w + 2 * self.margin_in + 2 * self.margin_out
        
        pygame.Surface.__init__(self, (Card_w, Card_h))
        
        # Surface Dimensions...
        self.AgentEntry = agent_entry
        self.ID         = agent_entry["ID"]
        self.Agent      = agent_entry["Agent"]
        self.AgentView  = agent_entry["AgentView"]
        self.ViewPort_Grid = agent_entry["ViewPort_Grid"]
        self.Active     = False

        # Dimensions we need for calculation
        self.TileSize   = tile_size
        #self.Agent_h    = self.AgentView.get_height()
        self.AgentView_y = 0
        self.Stats_y     = 0
        # self.margin_out = int(tile_size / 7) * 10
        # self.margin_in  = int(tile_size / 7) * 10
     
        # Colors
        self.TitleColor       = Card.white2
        self.TitleBg_Active   = Card.orange
        self.TitleBg_Inactive = Card.grey
        self.StatsColor       = Card.white2
        self.CardColor        = Card.dark2

        self.TitleFont = pygame.font.SysFont("monaco", 18, False, False)
        self.StatsFont = pygame.font.SysFont("monaco", 15, False, False)

        self.update_static(self.Active)

    def update(self, active):

        if self.Active != active:
            self.Active = not self.Active
            self.update_static(self.Active)

        # Draw AgentView
        self.AgentView  = self.AgentEntry["AgentView"]

        if self.TileSize < 8:
            w = self.ViewPort_Grid[0] * 8
            h = self.ViewPort_Grid[1] * 8
            #print(w)
            AgentView = pygame.transform.scale(self.AgentView, (w,h))
            self.blit( AgentView, (self.margin_in + self.margin_out, self.AgentView_y))
            self.blit( self.AgentView, (self.margin_in + self.margin_out, self.Stats_y + 50))
        else:
            self.blit( self.AgentView, (self.margin_in + self.margin_out, self.AgentView_y))

        # Draw Stats
        Stats = self.StatsFont.render("Energy: {:3.1f}".format(self.Agent.Energy), 1, self.StatsColor, self.CardColor)
        self.blit( Stats, (self.margin_in + self.margin_out, self.Stats_y))

    def scale_to(self, tile_size):
        # maybe some TileSize depending rescaling? hm...
        # Currently fixed size
        return None

    def update_static(self, active):

        # Clear the Card
        self.fill((0,0,0))
        
        # Draw the Card background
        background = (self.margin_out, 0, self.get_width() - 2 * self.margin_out, self.get_height())
        #print(background)
        pygame.draw.rect(self, self.CardColor, background)

        # Draw the Title depending on the ACTIVE status
        if active:  
            # Calculate dimensions
            TitleText = self.TitleFont.render("Agent: {}".format(self.ID), 1, self.TitleColor, self.TitleBg_Active)
            TitleBg   = (0,0, self.get_width(), TitleText.get_height() + 2 * self.margin_in)
            
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
            TitleText = self.TitleFont.render("Agent: {}".format(self.ID), 1, self.TitleColor, self.TitleBg_Inactive)
            TitleBg   = (self.margin_out, 0, self.get_width() - 2 * self.margin_out, TitleText.get_height() + 2 * self.margin_in)
            TitleBottom = TitleBg[1] + TitleBg[3]
            # Draw background and title
            pygame.draw.rect(self,self.TitleBg_Inactive, TitleBg)
            self.blit(TitleText, (self.margin_out + self.margin_in, self.margin_in))

        # Calculate y positions for the dynamically updated parts
        self.AgentView_y = TitleBottom + self.margin_in
        self.Stats_y     = self.AgentView_y + (self.AgentView.get_height() / self.TileSize * 8) + self.margin_in
      