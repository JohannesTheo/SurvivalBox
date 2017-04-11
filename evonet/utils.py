__author__ = 'Johannes Theodoridis'

# standard imports

# third party imports
import numpy as np
import scipy as sci

# local imports

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