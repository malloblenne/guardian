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
import itertools


import pygame




#--- Global constants ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)

SCREEN_WIDTH = 700
SCREEN_HEIGHT = 500

FPS = 60

display_flags = pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE

#--- Logger ---

import sys
LOGGING_LEVEL = logging.INFO
logger = logging.getLogger(__name__)
logger.setLevel(LOGGING_LEVEL)
log_hdlr = logging.StreamHandler(sys.stdout)
log_hdlr.setLevel(LOGGING_LEVEL)
logger.addHandler(log_hdlr)



class SpriteSheet(object):
    """ Class used to grab images out of a sprite sheet. """

    def __init__(self, file_name, color_key=(38, 0, 0)):
        """ Constructor. Pass in the file name of the sprite sheet. """

        # Load the sprite sheet.
        self.sprite_sheet = pygame.image.load(file_name).convert()
        self.color_key = color_key

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
        image.set_colorkey(self.color_key)
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


class Whale(pygame.sprite.Sprite):
    """ This class represents the player. Spaceship """

    images = []
    xs_circle = []
    ys_circle = []

    def __init__(self):
        """ Constructor """
        super().__init__()
        self.physical_obj = create_physical_object_dict(hit_points=50, damage=1,
                                                        score_value=200//50)

        if not Whale.images:
            #Load images
            sprite_sheet = SpriteSheet(os.path.join('bitmaps', 'bosses.png'))
            Whale.images.append(sprite_sheet.get_image(82, 359, 46, 110)) #pin left, eye right
            Whale.images.append(sprite_sheet.get_image(138, 359, 46, 110)) #pin left, eye center
            Whale.images.append(pygame.transform.flip(Whale.images[-1], True, False)) #mirror
            Whale.images.append(sprite_sheet.get_image(195, 359, 46, 110)) #pin left, eye left
            Whale.images.append(sprite_sheet.get_image(318, 359, 62, 110)) #pin right, half open mouth
            Whale.images.append(sprite_sheet.get_image(398, 358, 62, 126)) #pin left, open mouth
        if not Whale.xs_circle:
            Whale.xs_circle, Whale.ys_circle = self.circular_motion()
            Whale.xs_circle.extend(reversed(Whale.xs_circle))
            Whale.ys_circle.extend(reversed(Whale.ys_circle))

        self.rect = Whale.images[0].get_rect()
        self.max_speed = 5
        self.x_speed = 0
        self.y_speed = 0

        self.player_x = 0
        self.player_y = 0
        self.player_x_filt = 0
        self.player_y_filt = 0

        self.last_time = pygame.time.get_ticks()
        self.interval = 700 #ms
        self.last_time_change_behaviour = self.last_time
        self.interval_behaviour = 10000 #ms
        self.behaviour = 0
        self.last_time_fire = self.last_time
        self.interval_fire = 1000

        self.image_iterator = itertools.cycle(Whale.images)
        self.x_circle_iterator = itertools.cycle(Whale.xs_circle)
        self.y_circle_iterator = itertools.cycle(Whale.ys_circle)
        self.image = next(self.image_iterator)
        self.picontrol_x = PIController(kp=0.5, ki=0.05, anti_windup=100.0)
        self.picontrol_y = PIController(kp=0.5, ki=0.05, anti_windup=100.0)
        # alpha of exponential smoothing is 3/num_it for 95% constant sig
        self.alpha_exp_smoothing = 3.0/800


    def exponential_smoothing(self, alpha, val, old_filt_val):
        """ Exponential smoothing """
        return alpha * val + (1.0 - alpha) * old_filt_val

    def set_player_position(self, x_pos, y_pos):
        """ Setter for player position for smarter actions"""
        self.player_x = x_pos
        self.player_y = y_pos

        if self.player_x_filt == 0 and self.player_y_filt == 0:
            self.player_x_filt = x_pos
            self.player_y_filt = y_pos

        # exponential smoothing
        alpha = self.alpha_exp_smoothing
        self.player_x_filt = x_pos*alpha + (1.0 - alpha)*self.player_x_filt
        self.player_y_filt = y_pos*alpha + (1.0 - alpha)*self.player_y_filt


    def fire(self):
        """ Create bullet based on time interval"""
        bullets = []

        # Shoot if time
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time_fire >= self.interval_fire:
            self.last_time_fire = ticks_now

            def draw_circle_surface(radius, center, color, width):
                bullet_surf = pygame.Surface([2 * radius, 2 * radius])
                pygame.draw.circle(bullet_surf, color, center, radius, width)
                return bullet_surf
            
            def draw_circle(color, radius, width):
                center = (radius, radius)     
                return draw_circle_surface(radius, center, color, width)

            # Center
            RED_EYE = (219, 43, 0)
            bullet = Bullet(enemy=True, image=draw_circle(RED_EYE, 8, 4))
            bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
            # Left
            bullet = Bullet(enemy=True, x_speed=-3, image=draw_circle(RED_EYE, 4, 0))
            bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
            # Left
            bullet = Bullet(enemy=True, x_speed=-1, image=draw_circle(RED_EYE, 4, 0))
            bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
            # Right
            bullet = Bullet(enemy=True, x_speed=+3, image=draw_circle(RED_EYE, 4, 0))
            bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)
            # Right
            bullet = Bullet(enemy=True, x_speed=+1, image=draw_circle(RED_EYE, 4, 0))
            bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)


        return bullets



    def update_animation(self):
        """ Update animation """
        # Shoot if time
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time >= self.interval:
            self.last_time = ticks_now
            self.image = next(self.image_iterator)
        if ticks_now - self.last_time_change_behaviour >= self.interval_behaviour:
            self.last_time_change_behaviour = ticks_now
            self.behaviour = (self.behaviour + 1 ) % 2

    def circular_motion(self):
        """ Circular motion """
        r = 130#SCREEN_WIDTH/3.0
        num_steps = 100
        step = math.pi/num_steps
        angles = [x*step  for x in range(0,num_steps)]#range(0,math.pi,step)
        x_val = [r*cos_val for cos_val in [math.cos(angle) for angle in angles]]
        y_val = [r*sin_val for sin_val in [math.sin(angle) for angle in angles]]
        return x_val, y_val

    def update(self):
        """ Update whale """

        self.update_animation()

        enemy_center_x = self.rect.x + self.rect.width//2
        enemy_center_y = self.rect.y + self.rect.height//2

        x_circle = next(self.x_circle_iterator)
        y_circle = next(self.y_circle_iterator)

        if self.behaviour == 1:

            self.alpha_exp_smoothing = 3.0/300.0

            error_x = (self.player_x_filt - enemy_center_x)
            self.x_speed = self.picontrol_x.control(error_x)
            self.x_speed = min(max(self.x_speed, -self.max_speed), self.max_speed)

            y_offset = 200
            error_y = self.player_y_filt - enemy_center_y - y_offset
            self.y_speed = self.picontrol_y.control(error_y)
            self.y_speed = min(max(self.y_speed, -self.max_speed), self.max_speed)

        else:

            self.alpha_exp_smoothing = 3.0/800.0

            x_setpoint = self.player_x_filt + x_circle
            y_setpoint = self.player_y_filt - y_circle - self.rect.height

            error_x = (x_setpoint - enemy_center_x)
            self.x_speed = self.picontrol_x.control(error_x)
            self.x_speed = min(max(self.x_speed, -self.max_speed), self.max_speed)

            error_y = y_setpoint - enemy_center_y
            self.y_speed = self.picontrol_y.control(error_y)
            self.y_speed = min(max(self.y_speed, -self.max_speed), self.max_speed)

        x_pos = self.rect.x + self.x_speed
        y_pos = self.rect.y + self.y_speed

        self.rect = self.image.get_rect()

        self.rect.x = x_pos
        self.rect.y = y_pos


        #Check boundaries of the spaceship
        if self.rect.y > SCREEN_HEIGHT - self.rect.height:
            self.rect.y = SCREEN_HEIGHT - self.rect.height

        if self.rect.x < 0:
            self.rect.x = 0
        elif self.rect.x > SCREEN_WIDTH - self.rect.width:
            self.rect.x = SCREEN_WIDTH - self.rect.width


class EnemySmallSpaceship(pygame.sprite.Sprite):
    """ This class represents a specific enemy. Spaceship """

    image_center = None
    image_left = None
    image_right = None

    def __init__(self):
        """ Constructor """
        super().__init__()
        self.physical_obj = create_physical_object_dict(hit_points=1, damage=1, score_value=2)
        if EnemySmallSpaceship.image_center is None:
            sprite_sheet = SpriteSheet(os.path.join('bitmaps', 'enemies.png'), color_key=(3, 0 ,38))
            EnemySmallSpaceship.image_center = sprite_sheet.get_image(35, 95, 16, 14)
            EnemySmallSpaceship.image_right =  sprite_sheet.get_image(58, 95,
                                                                      13, 16)
            EnemySmallSpaceship.image_left = pygame.transform.flip(
                                             EnemySmallSpaceship.image_right,
                                             True, False)

        self.image = EnemySmallSpaceship.image_center
        self.rect = self.image.get_rect()
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
        bullets = []

        # Shoot if time
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time >= self.interval:
            self.last_time = ticks_now
            bullet = Bullet(enemy=True)
            bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
            bullet.rect.y = self.rect.y + self.rect.height
            bullets.append(bullet)

        return bullets

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

        x_new = self.rect.x + self.x_speed
        y_new = self.rect.y + self.y_speed

        x_speed_int = int(self.x_speed)

        if x_speed_int > 1:
            self.image = EnemySmallSpaceship.image_right
        elif x_speed_int < -1:
            self.image = EnemySmallSpaceship.image_left
        else:
            self.image = EnemySmallSpaceship.image_center

        self.rect = self.image.get_rect()
        self.rect.x = x_new
        self.rect.y = y_new

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
        sprite_sheet = SpriteSheet(os.path.join('bitmaps',
                                                     'theGuardian.png'))

        self.spaceship_normal = sprite_sheet.get_image(7, 87, 23, 30)
        self.spaceship_power1 = sprite_sheet.get_image(65, 87, 23, 30)
        self.spaceship_power2 = sprite_sheet.get_image(95, 87, 23, 30)
        self.spaceship_left = sprite_sheet.get_image(155, 87, 23, 30)
        self.spaceship_right = pygame.transform.flip(self.spaceship_left,
                                                     True, False)
        self.iterator_spaceship_center = itertools.cycle([self.spaceship_normal,
                                                          self.spaceship_power1,
                                                          self.spaceship_power2])

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
        elif x_speed > 0 and self.image != self.spaceship_right:
            self.image = self.spaceship_right
        elif x_speed == 0:
            self.image = next(self.iterator_spaceship_center)


class Bullet(pygame.sprite.Sprite):
    """ This class represents the bullet . """
    def __init__(self,  x_speed=0, y_speed=3, enemy=False, image=None):
        # Call the parent class (Sprite) constructor
        super().__init__()

        self.physical_obj = create_physical_object_dict(damage=1)
        self.x_speed = x_speed
        self.y_speed = y_speed
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
            self.rect.y += self.y_speed
            if self.rect.y >= SCREEN_HEIGHT:
                self.physical_obj['hit_points'] = 0 #dead
        else:
            self.rect.y -= self.y_speed
            if self.rect.y <= self.rect.height:
                self.physical_obj['hit_points'] = 0 #dead

        self.rect.x += self.x_speed
        if self.rect.x <= self.rect.width or self.rect.x >= SCREEN_WIDTH:
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
        self.pause = False
        self.game_over_music_enabled = False
        self.fps = 0.0
        self.font = pygame.font.Font(os.path.join('fonts','PressStart2P.ttf'), 12)

        self.all_sprites_list = pygame.sprite.Group()
        self.player_object_list = pygame.sprite.Group()
        #it contains all enemy sprites including bullets
        self.enemy_object_list = pygame.sprite.Group()
        #it contains only ships and monsters
        self.enemy_list = pygame.sprite.Group()
        
        self.last_time_enemy_killed = 0
        self.milliseconds_per_kill = 1500



        # Create the player
        self.player = Player()
        self.all_sprites_list.add(self.player)
        self.player_object_list.add(self.player)

        self.interval_spawn_enemy = 1500
        self.last_time_spawn_enemy = pygame.time.get_ticks()
        
        # Test boss
        #self.add_whale()

        if pygame.mixer:
            # http://www.khinsider.com/midi/nes/guardian-legend
            pygame.mixer.music.load(os.path.join('sounds', 'corridor-0.mid'))
            pygame.mixer.music.play(-1)

    def add_enemy(self):
        """ Create an instance of an enemy. """
        enemy = EnemySmallSpaceship()
        enemy.rect.x = random.randint(0, SCREEN_WIDTH-enemy.rect.width)
        self.all_sprites_list.add(enemy)
        self.enemy_object_list.add(enemy)
        self.enemy_list.add(enemy)

    def add_whale(self):
        """ Create an instance of an enemy. """
        enemy = Whale()
        enemy.rect.x = random.randint(0, SCREEN_WIDTH-enemy.rect.width)
        self.all_sprites_list.add(enemy)
        self.enemy_object_list.add(enemy)
        self.enemy_list.add(enemy)


    def spawn_enemy(self):
        """ Spawn new enemy based on time interval. """
        ticks_now = pygame.time.get_ticks()
        if ticks_now - self.last_time_spawn_enemy >= (self.milliseconds_per_kill * 0.80):#self.interval_spawn_enemy:
            self.last_time_spawn_enemy = ticks_now
            # The boss can be spawn only when score is high
            if self.player.score < 50:
                self.add_enemy()
            elif random.random() < 0.95:
                self.add_enemy()
            else:
                self.add_whale()
                # Slow down spawn of monster for some time
                slow_down_time = 60*1000 # 1 min
                self.last_time_spawn_enemy = ticks_now + slow_down_time

    def set_fps(self, fps):
        """ Setter fps """
        self.fps = fps

    def process_events(self, screen):
        """ Process all of the events. Return a "True" if we need
            to close the window. """

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return True
            elif event.type==pygame.VIDEORESIZE:
                size_screen = event.dict['size']
                screen=pygame.display.set_mode(size_screen, display_flags)
                return False
            if (self.game_over and (event.type == pygame.MOUSEBUTTONDOWN or
               (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN))):
                self.__init__()
                return False
            elif (event.type == pygame.KEYDOWN and event.key == pygame.K_p):
                self.pause = not self.pause
                if self.pause:
                   pygame.mixer.music.set_volume(0.0)
                   pygame.mixer.music.pause() # midi does not stop
                else:
                   pygame.mixer.music.set_volume(1.0)
                   pygame.mixer.music.unpause()					  

            if not self.game_over and not self.pause:
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
                pygame.mixer.music.play(1)
                self.game_over_music_enabled = True
        
        elif self.pause:
             pass # Do nothing for now	
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
                bullets = enemy.fire()
                if bullets:
                    self.all_sprites_list.add(bullets)
                    self.enemy_object_list.add(bullets)

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
            num_killed_enemy_now = 0

            for sprite in self.all_sprites_list:
                if sprite.physical_obj['hit_points'] <= 0:
                    logger.debug(str(sprite) + '  will be removed')
                    dead_list.append(sprite)
                    if not isinstance(sprite, Bullet):
                        num_killed_enemy_now+= 1
                    
            for sprite in dead_list:
                self.all_sprites_list.remove(sprite)
                self.player_object_list.remove(sprite)
                self.enemy_object_list.remove(sprite)
                self.enemy_list.remove(sprite)

            if num_killed_enemy_now > 0:
                ticks_now = pygame.time.get_ticks()
                interval_kills = (ticks_now - self.last_time_enemy_killed) / num_killed_enemy_now
                self.last_time_enemy_killed = ticks_now                
                alpha = 0.90
                self.milliseconds_per_kill = alpha * self.milliseconds_per_kill + (1.0 - alpha) * interval_kills 
                logger.debug('%10.2f ms/kills %10.2f kills/s',
                             self.milliseconds_per_kill,
                             1000.0/(self.milliseconds_per_kill))

    def display_frame(self, surface_fixed_size, true_screen):
        """ Display everything to the screen for the game. """
        surface_fixed_size.fill(BLACK)

        # Score
        text_score = self.font.render("Score {0}".format(self.player.score)
                                          , True, WHITE)
        surface_fixed_size.blit(text_score, [5, 40])

        if self.game_over:
            #font = pygame.font.Font("Serif", 25)
            #font = pygame.font.SysFont("serif", 25)
            text = self.font.render(
                "Game Over, click the mouse or press enter to restart",
                True, WHITE)
            center_x = (SCREEN_WIDTH // 2) - (text.get_width() // 2)
            center_y = (SCREEN_HEIGHT // 2) - (text.get_height() // 2)
            surface_fixed_size.blit(text, [center_x, center_y])

        if not self.game_over:
            self.all_sprites_list.draw(surface_fixed_size)

            #Display fps in bottom left side
            text_fps = self.font.render("FPS {0}".format(round(self.fps, 1)),
                                            True, WHITE)
            surface_fixed_size.blit(text_fps, [SCREEN_WIDTH -95, SCREEN_HEIGHT -40])

            # Hit points
            text_hp = self.font.render("HP {0}".format(
                self.player.physical_obj['hit_points']), True, WHITE)
            surface_fixed_size.blit(text_hp, [SCREEN_WIDTH -95, 40])
			
			# Kill / s
            text_kill_s = self.font.render("Kill/s {0:.2f}".format(
                1000.0/(self.milliseconds_per_kill)), True, WHITE)
            surface_fixed_size.blit(text_kill_s, [0, SCREEN_HEIGHT -40])			

        true_screen.blit(pygame.transform.scale(surface_fixed_size, true_screen.get_size()), (0, 0))
        pygame.display.flip()


def main():
    """ Main program function. """
    # Initialize logger
    #logging.getLogger().setLevel(logging.INFO)
    # Initialize Pygame and set up the window
    pygame.init()

    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size, display_flags)

    # Everything will be drawn on a fixed surface and then scaled
    surface_fixed_size = screen.copy()

    pygame.display.set_caption("Guardian")
    pygame.mouse.set_visible(False)

	# Set Icon of the window
    sprite_sheet = SpriteSheet(os.path.join('bitmaps', 'bosses.png'))
    icon = sprite_sheet.get_image(99, 312, 32, 32)
    pygame.display.set_icon(icon)
	
    # Create our objects and set the data
    done = False
    clock = pygame.time.Clock()

    # Create an instance of the Game class
    game = Game()

    # Main game loop
    while not done:

        # Process events (keystrokes, mouse clicks, etc)
        done = game.process_events(screen)

        # Update object positions, check for collisions
        game.run_logic()

        #set fps to be printed
        game.set_fps(clock.get_fps())

        # Draw the current frame
        game.display_frame(surface_fixed_size, screen)

        # Pause for the next frame
        clock.tick(FPS)

    # Close window and exit
    pygame.quit()



# Main function
if __name__ == "__main__":
    main()
