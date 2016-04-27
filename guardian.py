#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 10 18:26:05 2016
Inspired by the tutorials: http://programarcadegames.com/

@author: Mauro Brenna
"""

import logging
import math
import random
import os


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

    def get_image(self, x_pos, y_pos, width, height):
        """ Grab a single image out of a larger spritesheet
            Pass in the x_pos, y_pos location of the sprite
            and the width and height of the sprite. """

        # Create a new blank image
        image = pygame.Surface([width, height]).convert()

        # Copy the sprite from the large sheet onto the smaller image
        image.blit(self.sprite_sheet, (0, 0), (x_pos, y_pos, width, height))

        # Assuming black works as the transparent color
        #image.set_colorkey(BLACK)
        image.set_colorkey((38, 0, 0))
        # Return the image
        return image

class PIController(object):
    """ Class repesenting a PI controller """

    def __init__(self, kp=0.01, ki=0.001, anti_windup=10.0):
        """ Constructor. Pass the gains proportional and integral """
        self.kp_gain = kp
        self.ki_gain = ki
        self.cum_sum = 0.0
        self.anti_windup = abs(anti_windup)

    def control(self, error):
        """ Control function getting as input error
        and returning the setpoint based on PI controller"""
        control_value = self.kp_gain * error + self.ki_gain * self.cum_sum
        self.cum_sum = self.cum_sum + error
        #anti windup
        self.cum_sum = max(min(self.cum_sum, self.anti_windup),
                           -self.anti_windup)
        return control_value


def create_physical_object_dict(score_value=0, hit_points=1,
                                immortal=False, damage=0):
    """ Create a dictionary with filled value for physical object
    attributes """
    phy_obj = {}
    phy_obj['score_value'] = score_value # score to be assigned when dead
    phy_obj['hit_points'] = hit_points
    phy_obj['immortal'] = immortal
    phy_obj['damage'] = damage
    return phy_obj


class Enemy1(pygame.sprite.Sprite):
    """ This class represents the player. Spaceship """

    image = None

    def __init__(self):
        """ Constructor """
        super().__init__()
        self.physical_obj = create_physical_object_dict(hit_points=1, damage=1, score_value=2)
        if Enemy1.image is None:
            sprite_sheet = SpriteSheet("bitmaps/enemies.png")
            Enemy1.image = sprite_sheet.get_image(35, 95, 16, 14)
        self.rect = Enemy1.image.get_rect()
        self.x_speed = 0
        self.y_speed = 0
        self.max_speed = 10.0

        self.player_x = 0
        self.player_y = 0
        self.last_time = pygame.time.get_ticks()
        self.interval = 700 #ms

        self.rect.y = self.rect.height + 1

        self.picontrol_x = PIController(kp=0.01, ki=0.01, anti_windup=100.0)
        self.picontrol_y = PIController(kp=0.01, ki=0.01, anti_windup=100.0)
        self.times_update_func_called = 0

    def set_player_position(self, x_pos, y_pos):
        """ Setter for player position for smarter actions"""
        self.player_x = x_pos
        self.player_y = y_pos


    def fire(self):
        """ Create bullet based on time interval"""
        bullet = None

        # Shoot if time
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time >= self.interval:
            self.last_time = ticks_now
            bullet = Bullet(enemy=True)
            bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
            bullet.rect.y = self.rect.y + self.rect.height

        return bullet

    def update(self):
        """ Update enemy ship"""
        # Move enemy spaceship
        enemy_center_x = self.rect.x + self.rect.width//2
        enemy_center_y = self.rect.y + self.rect.height//2
        error_x = (self.player_x - enemy_center_x)

        self.x_speed = self.picontrol_x.control(error_x)
        self.x_speed = min(max(self.x_speed, -self.max_speed), self.max_speed)


        error_y = self.player_y - enemy_center_y
        offset_max = 3.0
        freq = 1.0/240.0
        sin_value = math.sin(2.0 * math.pi * freq * self.times_update_func_called)
        offset_y = offset_max * sin_value  - offset_max/2.0 -1.0

        self.y_speed = self.picontrol_y.control(error_y) + offset_y
        self.y_speed = min(max(self.y_speed, -self.max_speed), self.max_speed)

        self.times_update_func_called = self.times_update_func_called + 1.0
        self.rect.x = self.rect.x + int(self.x_speed)
        self.rect.y = self.rect.y + self.y_speed


        #Check boundaries of the spaceship
        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.y > SCREEN_HEIGHT - self.rect.height:
            self.rect.y = SCREEN_HEIGHT - self.rect.height

        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > SCREEN_WIDTH - self.rect.width:
            self.rect.x = SCREEN_WIDTH - self.rect.width


class Player(pygame.sprite.Sprite):


    """ This class represents the player. Spaceship """
    def __init__(self):
        super().__init__()
        self.physical_obj = create_physical_object_dict(hit_points=3, damage=1)
        self.sprite_sheet = SpriteSheet(os.path.join('bitmaps',
                                                     'theGuardian.png'))

        self.spaceship_normal = self.sprite_sheet.get_image(7, 87, 23, 30)
        self.spaceship_power1 = self.sprite_sheet.get_image(65, 87, 23, 30)
        self.spaceship_power2 = self.sprite_sheet.get_image(95, 87, 23, 30)
        self.spaceship_left = self.sprite_sheet.get_image(155, 87, 23, 30)
        self.spaceship_right = pygame.transform.flip(self.spaceship_left,
                                                     True, False)

        bullet_sprite_sheet = SpriteSheet(os.path.join('bitmaps',
                                                       'bullet.png'))
        self.bullet_image = bullet_sprite_sheet.get_image(8, 4, 7, 21)
        self.image = self.spaceship_normal
        self.rect = self.image.get_rect()
        self.rect.x = SCREEN_WIDTH//2 - self.rect.width//2
        self.rect.y = SCREEN_HEIGHT - self.rect.height//2
        self.x_speed_left = 0
        self.x_speed_right = 0
        self.y_speed_up = 0
        self.y_speed_down = 0

        #http://programarcadegames.com/index.php?
        #chapter=bitmapped_graphics_and_sound
        if pygame.mixer:
            self.fire_sound = pygame.mixer.Sound(os.path.join('sounds',
                                                          'laser5.ogg'))
        self.score = 0

    def create_bullet(self):
        """ Generate a bullet. """
        bullet = Bullet(image=self.bullet_image)

        bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
        bullet.rect.y = self.rect.y

        return bullet

    def process_event(self, event):
        """ Update the player location. """

        #Move player
        bullet = None

        if event.type == pygame.KEYDOWN:
            # Figure out if it was an arrow key. If so
            # adjust speed.
            if event.key == pygame.K_LEFT:
                self.x_speed_left = -3
            elif event.key == pygame.K_RIGHT:
                self.x_speed_right = 3
            elif event.key == pygame.K_UP:
                self.y_speed_up = -3
            elif event.key == pygame.K_DOWN:
                self.y_speed_down = 3
            elif event.key == pygame.K_SPACE:
                bullet = self.create_bullet()
                if pygame.mixer:
                    self.fire_sound.play()
        # User let up on a key
        elif event.type == pygame.KEYUP:
                # If it is an arrow key, reset vector back to zero
            if event.key == pygame.K_LEFT:
                self.x_speed_left = 0
            elif event.key == pygame.K_RIGHT:
                self.x_speed_right = 0
            elif event.key == pygame.K_UP:
                self.y_speed_up = 0
            elif event.key == pygame.K_DOWN:
                self.y_speed_down = 0
        #pos = pygame.mouse.get_pos()

        #logging.debug('new pos ', self.rect.x, ' ', self.rect.y)
        return bullet

    def update(self):
        """ Update player spaceship """

        #Update pos spaceship
        x_speed = self.x_speed_left + self.x_speed_right
        y_speed = self.y_speed_up + self.y_speed_down
        self.rect.x = self.rect.x + x_speed
        self.rect.y = self.rect.y + y_speed

        #Check boundaries of the spaceship
        if self.rect.y < 0:
            self.rect.y = 0
        elif self.rect.y > SCREEN_HEIGHT - self.rect.height:
            self.rect.y = SCREEN_HEIGHT - self.rect.height

        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > SCREEN_WIDTH - self.rect.width:
            self.rect.x = SCREEN_WIDTH - self.rect.width

        #change the image accordingly
        if x_speed < 0 and self.image != self.spaceship_left:
            self.image = self.spaceship_left
            #self.rect = self.image.get_rect()
        elif x_speed > 0 and self.image != self.spaceship_right:
            self.image = self.spaceship_right
            #self.rect = self.image.get_rect()
        elif x_speed == 0:
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
    def __init__(self, speed=3, enemy=False, image=None):
        # Call the parent class (Sprite) constructor
        super().__init__()

        self.physical_obj = create_physical_object_dict(damage=1)
        self.speed = speed
        self.enemy = enemy #is an enemy of is coming from an ally
        if image:
            self.image = image
        else:
            self.image = pygame.Surface([4, 10])
            self.image.fill(WHITE)

        self.rect = self.image.get_rect()

        self.damage = 1

    def update(self):
        """ Move the bullet. """
        if self.enemy is True:
            self.rect.y += self.speed
            if self.rect.y >= SCREEN_HEIGHT:
                self.physical_obj['hit_points'] = 0 #dead
        else:
            self.rect.y -= self.speed
            if self.rect.y <= 10:
                self.physical_obj['hit_points'] = 0 #dead



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
        self.game_over_music_enabled = False
        self.fps = 0.0
        self.fps_font = pygame.font.SysFont("serif", 25)

        self.all_sprites_list = pygame.sprite.Group()
        self.player_object_list = pygame.sprite.Group()
        #it contains all enemy sprites including bullets
        self.enemy_object_list = pygame.sprite.Group()
        #it contains only ships and monsters
        self.enemy_list = pygame.sprite.Group()



        # Create the player
        self.player = Player()
        self.all_sprites_list.add(self.player)
        self.player_object_list.add(self.player)

        self.interval_spawn_enemy = 1500
        self.last_time_spawn_enemy = pygame.time.get_ticks()

        if pygame.mixer:
            # http://www.khinsider.com/midi/nes/guardian-legend
            pygame.mixer.music.load(os.path.join('sounds', 'corridor-0.mid'))
            pygame.mixer.music.play(-1)

    def add_enemy(self):
        """ Create an instance of an enemy. """
        enemy = Enemy1()
        enemy.rect.x = random.randint(0, SCREEN_WIDTH-enemy.rect.width)
        self.all_sprites_list.add(enemy)
        self.enemy_object_list.add(enemy)
        self.enemy_list.add(enemy)

    def spawn_enemy(self):
        """ Spawn new enemy based on time interval. """
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time_spawn_enemy >= self.interval_spawn_enemy:
            self.last_time_spawn_enemy = ticks_now
            self.add_enemy()

    def set_fps(self, fps):
        """ Setter fps """
        self.fps = fps

    def process_events(self):
        """ Process all of the events. Return a "True" if we need
            to close the window. """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            if (event.type == pygame.MOUSEBUTTONDOWN or
               (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN)):
                if self.game_over:
                    self.__init__()
            elif not self.game_over:
                bullet = self.player.process_event(event)
                if bullet is not None:
                    self.all_sprites_list.add(bullet)
                    self.player_object_list.add(bullet)
        return False

    def run_logic(self):
        """
        This method is run each time through the frame. It
        updates positions and checks for collisions.
        """
        self.game_over = self.player.physical_obj['hit_points'] <= 0
        if self.game_over:
            if not self.game_over_music_enabled and pygame.mixer:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(os.path.join('sounds', 'game-over.mid'))
                pygame.mixer.music.play(-1)
                self.game_over_music_enabled = True
        else:

            self.spawn_enemy()

            # Move all the sprites
            player_x = self.player.rect.x + self.player.rect.width//2
            player_y = self.player.rect.y + self.player.rect.height//2

            for enemy in self.enemy_list:
                enemy.set_player_position(player_x, player_y)

            self.all_sprites_list.update()

            # Add new bullet
            for enemy in self.enemy_list:
                bullet = enemy.fire()
                if bullet is not None:
                    self.all_sprites_list.add(bullet)
                    self.enemy_object_list.add(bullet)

            # Check collisions
            for ally_obj in  self.player_object_list:
                enemy_hit_list = pygame.sprite.spritecollide(ally_obj,
                                                             self.enemy_object_list,
                                                             False)
                for enemy_obj in enemy_hit_list:
                    if not isinstance(ally_obj, Bullet) or not isinstance(enemy_obj, Bullet):
                        if ally_obj.physical_obj['immortal'] is False:
                            ally_obj.physical_obj['hit_points'] -= enemy_obj.physical_obj['damage']
                        if enemy_obj.physical_obj['immortal'] is False:
                            enemy_obj.physical_obj['hit_points'] -= ally_obj.physical_obj['damage']
                            self.player.score += enemy_obj.physical_obj['score_value']


            # Check for dead objects to be removed
            dead_list = []

            for sprite in self.all_sprites_list:
                if sprite.physical_obj['hit_points'] <= 0:
                    logging.debug(sprite, ' will be removed')
                    dead_list.append(sprite)
            for sprite in dead_list:
                self.all_sprites_list.remove(sprite)
                self.player_object_list.remove(sprite)
                self.enemy_object_list.remove(sprite)
                self.enemy_list.remove(sprite)


    def display_frame(self, screen):
        """ Display everything to the screen for the game. """
        screen.fill(BLACK)

        # Score
        text_score = self.fps_font.render("Score {0}".format(self.player.score)
                                          , True, WHITE)
        screen.blit(text_score, [5, 40])

        if self.game_over:
            #font = pygame.font.Font("Serif", 25)
            font = pygame.font.SysFont("serif", 25)
            text = font.render(
                "Game Over, click the mouse or press enter to restart",
                True, WHITE)
            center_x = (SCREEN_WIDTH // 2) - (text.get_width() // 2)
            center_y = (SCREEN_HEIGHT // 2) - (text.get_height() // 2)
            screen.blit(text, [center_x, center_y])

        if not self.game_over:
            self.all_sprites_list.draw(screen)

            #Display fps in bottom left side
            text_fps = self.fps_font.render("FPS {0}".format(round(self.fps, 1)),
                                            True, WHITE)
            screen.blit(text_fps, [SCREEN_WIDTH -95, SCREEN_HEIGHT -40])

            # Hit points
            text_hp = self.fps_font.render("HP {0}".format(
                self.player.physical_obj['hit_points']), True, WHITE)
            screen.blit(text_hp, [SCREEN_WIDTH -95, 40])



        pygame.display.flip()


def main():
    """ Main program function. """
    # Initialize logger
    #logging.getLogger().setLevel(logging.INFO)
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

        #set fps to be printed
        game.set_fps(clock.get_fps())

        # Draw the current frame
        game.display_frame(screen)

        # Pause for the next frame
        clock.tick(60)

    # Close window and exit
    pygame.quit()



# Main function
if __name__ == "__main__":
    main()
