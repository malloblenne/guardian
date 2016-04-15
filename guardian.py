# -*- coding: utf-8 -*-
"""
Created on Sun Apr 10 18:26:05 2016
Inspired by  http://programarcadegames.com/
@author: Mauro
"""

import pygame

#--- Global constants ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 500



class SpriteSheet(object):
    """ Class used to grab images out of a sprite sheet. """
 
    def __init__(self, file_name):
        """ Constructor. Pass in the file name of the sprite sheet. """
 
        # Load the sprite sheet.
        self.sprite_sheet = pygame.image.load(file_name).convert()
 
 
    def get_image(self, x, y, width, height):
        """ Grab a single image out of a larger spritesheet
            Pass in the x, y location of the sprite
            and the width and height of the sprite. """
 
        # Create a new blank image
        image = pygame.Surface([width, height]).convert()
 
        # Copy the sprite from the large sheet onto the smaller image
        image.blit(self.sprite_sheet, (0, 0), (x, y, width, height))
 
        # Assuming black works as the transparent color
        #image.set_colorkey(BLACK)
        image.set_colorkey((38,0,0))
        # Return the image
        return image

class PhysicalObject(object):
    """ Class used to represent a physical object """
    
    def __init__(self, scoreValue=0, hitPoints = 1,
                 immortal = False, damage = 0):
        """ Constructor """
        self.scoreValue = scoreValue # score to be assigned when dead
        self.hitPoints = hitPoints
        self.immortal = immortal
        self.damage = damage
        print ('created physical object')
        
        
class Player(pygame.sprite.Sprite):
    
    
    """ This class represents the player. Spaceship """
    def __init__(self):
        super().__init__()
        self.physicalObject = PhysicalObject()
        self.sprite_sheet = SpriteSheet("bitmaps/theGuardian.png")
#        self.spaceship_normal = self.sprite_sheet.get_image(5,80,25,50)
#        self.spaceship_left   = self.sprite_sheet.get_image(5+6*28,80,25,50)
#        self.spaceship_right  = pygame.transform.flip(self.spaceship_left, 
#                                                      True, False)        

        self.spaceship_normal = self.sprite_sheet.get_image(6,80,24,50)
        self.spaceship_power1 = self.spaceship_normal#self.sprite_sheet.get_image(6+2*24,80,24,50)
        self.spaceship_power2 = self.spaceship_normal#self.sprite_sheet.get_image(6+3*24,80,24,50)
        self.spaceship_left   = self.sprite_sheet.get_image(6+6*24,80,24,50)
        self.spaceship_right  = pygame.transform.flip(self.spaceship_left, 
                                                      True, False)        
        self.image = self.spaceship_normal        
        self.rect = self.image.get_rect()        
        #self.image = pygame.Surface([20, 20])
        #self.image.fill(RED)
        #self.rect = self.image.get_rect()
        self.x_speed = 0
        self.y_speed = 0
        
        self.hitPoints = 3

    def process_event(self, event):
        """ Update the player location. """

        #Move player        
        #self.x_speed = 0
        #self.y_speed = 0
        bullet = None
        
        if event.type == pygame.KEYDOWN:
            # Figure out if it was an arrow key. If so
            # adjust speed.
            if event.key == pygame.K_LEFT:
                self.x_speed =- 3
            elif event.key == pygame.K_RIGHT:
                self.x_speed = 3
            elif event.key == pygame.K_UP:
                self.y_speed =- 3
            elif event.key == pygame.K_DOWN:
                self.y_speed = 3
            elif event.key == pygame.K_SPACE:
                bullet = Bullet()
                bullet.rect.x = self.rect.x
                bullet.rect.y = self.rect.y
        # User let up on a key
        elif event.type == pygame.KEYUP:
                # If it is an arrow key, reset vector back to zero
            if event.key == pygame.K_LEFT:
                self.x_speed=0
            elif event.key == pygame.K_RIGHT:
                self.x_speed=0
            elif event.key == pygame.K_UP:
                self.y_speed=0
            elif event.key == pygame.K_DOWN:
                self.y_speed=0
        #pos = pygame.mouse.get_pos()

        #print('new pos ', self.rect.x, ' ', self.rect.y)
        return bullet
        
    def update(self):
        #Update pos spaceship
        self.rect.x = self.rect.x + self.x_speed
        self.rect.y = self.rect.y + self.y_speed

        #Check boundaries of the spaceship        
        if self.rect.y <0:
            self.rect.y = 0
        elif self.rect.y > SCREEN_HEIGHT - self.rect.height:
            self.rect.y = SCREEN_HEIGHT - self.rect.height

        if self.rect.x <0:
            self.rect.x = 0
        elif self.rect.x > SCREEN_WIDTH - self.rect.width:
            self.rect.x = SCREEN_WIDTH - self.rect.width

        #change the image accordingly
        if self.x_speed < 0 and self.image != self.spaceship_left:
            self.image = self.spaceship_left        
            #self.rect = self.image.get_rect()
        elif self.x_speed > 0 and self.image != self.spaceship_right:
            self.image = self.spaceship_right        
            #self.rect = self.image.get_rect()  
        elif self.x_speed == 0:
            if self.image == self.spaceship_normal:
                self.image = self.spaceship_power1
            elif self.image == self.spaceship_power1:
                self.image = self.spaceship_power2
            elif self.image == self.spaceship_power2:
                self.image = self.spaceship_power1
            else:
                self.image = self.spaceship_normal
            #self.rect = self.image.get_rect()  

       #check for shooting
        
        #check for collisions
        

class Bullet(pygame.sprite.Sprite):
    """ This class represents the bullet . """
    def __init__(self):
        # Call the parent class (Sprite) constructor
        super().__init__()

        self.physicalObject = PhysicalObject(damage=1) 
        self.image = pygame.Surface([4, 10])
        self.image.fill(WHITE)
        
 
        self.rect = self.image.get_rect()
 
    def update(self):
        """ Move the bullet. """
        self.rect.y -= 3
        if self.rect.y <= 10:
            self.physicalObject.hitPoints = 0 #dead


class Game(object):
    """ This class represents an instance of the game. If we need to
        reset the game we'd just need to create a new instance of this
        class. """

    # --- Class attributes.
    # In this case, all the data we need
    # to run our game.

    # --- Class methods
    # Set up the game
    def __init__(self):
        self.score = 0
        self.game_over = False
        
        self.all_sprites_list = pygame.sprite.Group()



        # Create the player
        self.player = Player()
        self.all_sprites_list.add(self.player)

    def process_events(self):
        """ Process all of the events. Return a "True" if we need
            to close the window. """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.game_over:
                    self.__init__()
            else:
                bullet = self.player.process_event(event)
                if bullet is not None:
                    self.all_sprites_list.add(bullet)

        return False

    def run_logic(self):
        """
        This method is run each time through the frame. It
        updates positions and checks for collisions.
        """
        if not self.game_over:
            # Move all the sprites
            self.all_sprites_list.update()
            deadList = []
            
            for sprite in self.all_sprites_list:
                if sprite.physicalObject.hitPoints <=0:
                    print(sprite, ' will be removed')
                    deadList.append(sprite)
            for sprite in deadList:
                self.all_sprites_list.remove(sprite)


    def display_frame(self, screen):
        """ Display everything to the screen for the game. """
        screen.fill(BLACK)

        if self.game_over:
            #font = pygame.font.Font("Serif", 25)
            font = pygame.font.SysFont("serif", 25)
            text = font.render("Game Over, click to restart", True, BLACK)
            center_x = (SCREEN_WIDTH // 2) - (text.get_width() // 2)
            center_y = (SCREEN_HEIGHT // 2) - (text.get_height() // 2)
            screen.blit(text, [center_x, center_y])

        if not self.game_over:
            self.all_sprites_list.draw(screen)

        pygame.display.flip()


def main():
    """ Main program function. """
    # Initialize Pygame and set up the window
    pygame.init()

    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size)

    pygame.display.set_caption("My Game")
    pygame.mouse.set_visible(False)

    # Create our objects and set the data
    done = False
    clock = pygame.time.Clock()

    # Create an instance of the Game class
    game = Game()

    # Main game loop
    while not done:

        # Process events (keystrokes, mouse clicks, etc)
        done = game.process_events()

        # Update object positions, check for collisions
        game.run_logic()

        # Draw the current frame
        game.display_frame(screen)

        # Pause for the next frame
        clock.tick(60)

    # Close window and exit
    pygame.quit()

# Call the main function, start up the game
if __name__ == "__main__":
    main()
