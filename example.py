from evonet import EvoNet
from PIL import Image
import matplotlib.pyplot as plt

import cProfile

def run():
    game = EvoNet( grid_width=52, grid_height=52, tile_size=8, water_percentage=0.5, num_agents=4)

    game._setup()
    game.init()

    for x in range(3000):
    #while True: 
        if game.game_over():
           
            #break
            game.reset()
        #time.sleep(0.05)
        #dt = game.clock.tick_busy_loop(30)
        dt = game.clock.tick(30) 
        #dt = 10
        game.step(dt)
        print(game.getScore())

        if x == 10001:
            observations = game.getScreenRGB()
            print(observations)
            #img = Image.fromarray(observations[0], 'RGB')
           # img = Image.fromarray(observations, 'RGB')
            #img.save('my.png')
          #  img.show()

            imgplot = plt.imshow(observations)
            plt.show()
           
        #print(game.step(dt))
        #print(game.getScreenRGB())
        #pygame.display.update()

run()
#cProfile.run('run()', 'evo_sm.profile')