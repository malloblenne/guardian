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
import sys


import pygame
from pytmx.util_pygame import load_pygame
import pyscroll



#--- Global constants ---
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
PURPLE = (128, 0, 128)
RED_EYE = (219, 43, 0)

SCREEN_WIDTH = 256
SCREEN_HEIGHT = 220

FPS = 60

PLAYER_HP = 3
PLAYER_IMMORTAL = False

DISPLAY_FLAGS = pygame.HWSURFACE|pygame.DOUBLEBUF|pygame.RESIZABLE

#--- Logger ---

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

    def __repr__(self):
        """ Representation of the object """
        return "PIController(kp={0}, ki={1}, anti_windup={2})".format(self.kp_gain,
                             self.ki_gain, self.anti_windup)


def exponential_smoothing(alpha, val, old_filt_val):
    """ Exponential smoothing """
    return alpha * val + (1.0 - alpha) * old_filt_val


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
                """ Create a surface with a circle in the middle"""
                bullet_surf = pygame.Surface([2 * radius, 2 * radius])
                pygame.draw.circle(bullet_surf, color, center, radius, width)
                bullet_surf.set_colorkey(BLACK)
                return bullet_surf

            def draw_circle(color, radius, width):
                """ Create a surface with a circle in the middle. Shortcut"""
                center = (radius, radius)
                return draw_circle_surface(radius, center, color, width)

            # Center
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
            self.behaviour = (self.behaviour + 1) % 2

    def circular_motion(self):
        """ Circular motion """
        r = 130#SCREEN_WIDTH/3.0
        num_steps = 100
        step = math.pi/num_steps
        angles = [x*step  for x in range(0, num_steps)]#range(0,math.pi,step)
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
        self.physical_obj = create_physical_object_dict(hit_points=1,
                                                        damage=1,
                                                        score_value=2)

        if EnemySmallSpaceship.image_center is None:
            sprite_sheet = SpriteSheet(os.path.join('bitmaps', 'enemies.png'),
                                       color_key=(3, 0, 38))
            EnemySmallSpaceship.image_center = sprite_sheet.get_image(35, 95,
                                                                      16, 14)
            EnemySmallSpaceship.image_right = sprite_sheet.get_image(58, 95,
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


def on_keyboard_event_user1(event):
    """ Convert keys to game event """

    event_result = {'type': 'None', 'value': 'None'}

    if event.type == pygame.KEYDOWN:
        event_result['type'] = 'pressed'
    elif event.type == pygame.KEYUP:
        event_result['type'] = 'released'

    if event_result['type'] != 'None':
        if event.key == pygame.K_LEFT:
            event_result['value'] = 'left'
        elif event.key == pygame.K_RIGHT:
            event_result['value'] = 'right'
        elif event.key == pygame.K_UP:
            event_result['value'] = 'up'
        elif event.key == pygame.K_DOWN:
            event_result['value'] = 'down'
        elif event.key == pygame.K_SPACE:
            event_result['value'] = 'fire'

    return event_result

def send_event_pause():
    """ Send event pause/start """

    ev_dict = {'type': 'pause'}
    user_event = pygame.event.Event(pygame.USEREVENT, ev_dict)
    pygame.event.post(user_event)

    logger.debug('Pause event')


class JoypadControl(object):
    """ This class that handles the joypad inputs """

    def __init__(self):

        # Initialize the joysticks
        pygame.joystick.init()

        # Get count of joysticks
        joystick_count = pygame.joystick.get_count()

        logger.debug('Number joypads connected: %d', joystick_count)

        self.joystick = None

        if joystick_count:
            self.joystick = pygame.joystick.Joystick(0) #first one
            self.joystick.init()
            self.numaxes = self.joystick.get_numaxes()
            self.numbuttons = self.joystick.get_numbuttons()
            self.axis_lr_pressed_old = 'left'
            self.axis_ud_pressed_old = 'up'

    def on_joypad_event(self, event):
        """ Convert joypad to game event """
        event_result = {'type': 'None', 'value': 'None'}

        if not self.joystick or self.numaxes < 2 or self.numbuttons < 10:
            return event_result

        # Possible joystick actions: JOYAXISMOTION JOYBALLMOTION JOYBUTTONDOWN
        # JOYBUTTONUP JOYHATMOTION
        if event.type == pygame.JOYBUTTONDOWN:
            event_result['type'] = 'pressed'
            event_result['value'] = 'fire'
#            for i in range(buttons):
#                button = joystick.get_button(i)
#                if button:
#                    event_result['value'] = 'fire'
#                    break
            if self.joystick.get_button(8) or self.joystick.get_button(9):
                send_event_pause()

        elif event.type == pygame.JOYBUTTONUP:
            event_result['type'] = 'released'
            event_result['value'] = 'fire'

        elif event.type == pygame.JOYAXISMOTION:
            if event.dict['axis'] == 0:
                if abs(event.dict['value']) < 0.5:
                    event_result['type'] = 'released'
                    event_result['value'] = self.axis_lr_pressed_old
                else:
                    event_result['type'] = 'pressed'
                    if event.dict['value'] < 0.0:
                        event_result['value'] = 'left'
                    else:
                        event_result['value'] = 'right'
                    self.axis_lr_pressed_old = event_result['value']

            if event.dict['axis'] == 1:
                if abs(event.dict['value']) < 0.5:
                    event_result['type'] = 'released'
                    event_result['value'] = self.axis_ud_pressed_old
                else:
                    event_result['type'] = 'pressed'
                    if event.dict['value'] < 0.0:
                        event_result['value'] = 'up'
                    else:
                        event_result['value'] = 'down'
                    self.axis_ud_pressed_old = event_result['value']

        return event_result


class Player(pygame.sprite.Sprite):


    """ This class represents the player. Spaceship """
    def __init__(self):
        super().__init__()
        self.physical_obj = create_physical_object_dict(hit_points=PLAYER_HP,
                                                        immortal=PLAYER_IMMORTAL,
                                                        damage=1)
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

        reverse_spaceship = sprite_sheet.get_image(391, 46, 25, 28) #49
        reverse_spaceship_tilt1 = sprite_sheet.get_image(366, 46, 18, 28)
        reverse_spaceship_tilt2 = sprite_sheet.get_image(345, 47, 14, 27)
        reverse_spaceship_tilt1_flip = pygame.transform.flip(reverse_spaceship_tilt1,
                                                             True, False)
        reverse_spaceship_tilt2_flip = pygame.transform.flip(reverse_spaceship_tilt2,
                                                             True, False)

        self.iterator_spaceship_reverse = itertools.cycle([reverse_spaceship_tilt2,
                                                           reverse_spaceship_tilt1,
                                                           reverse_spaceship,
                                                           reverse_spaceship_tilt2_flip,
                                                           reverse_spaceship_tilt1_flip,
                                                           self.spaceship_normal])

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
            self.collision_sound = pygame.mixer.Sound(os.path.join('sounds',
                                                              '27826_erdie_sword01_short.ogg'))
        self.score = 0
        self.last_hit_points = self.physical_obj['hit_points']
        self.last_time_immortal = pygame.time.get_ticks()
        self.immortality_interval = 800
        self.immortality_always = PLAYER_IMMORTAL
        self.iteration = 0

        self.bullet = None

        self.joypad = JoypadControl()

    def create_bullet(self):
        """ Generate a bullet. """
        bullet = Bullet(image=self.bullet_image)

        bullet.rect.x = self.rect.x + self.rect.width//2 - bullet.rect.width//2
        bullet.rect.y = self.rect.y

        return bullet

    def fire(self):
        """ Return bullet if it was prepared for. """

        if self.bullet:

            ret_bullet = self.bullet
            self.bullet = None

            if pygame.mixer:
                self.fire_sound.play()

            return ret_bullet
        else:
            return None

    def process_event(self, event):
        """ Update the player location. """

        #Select player action to apply in next update step

        game_event = on_keyboard_event_user1(event)

        if game_event['type'] == 'None' or game_event['value'] == 'None':
            game_event = self.joypad.on_joypad_event(event)
            if game_event['type'] == 'None' or game_event['value'] == 'None':
                return None

        if game_event['type'] == 'pressed':
            # Figure out if it was an arrow key. If so
            # adjust speed.
            if game_event['value'] == 'left':
                self.x_speed_left = -3
            elif game_event['value'] == 'right':
                self.x_speed_right = 3
            elif game_event['value'] == 'up':
                self.y_speed_up = -3
            elif game_event['value'] == 'down':
                self.y_speed_down = 3
            elif game_event['value'] == 'fire':
                self.bullet = self.create_bullet()
        # User let up on a key
        elif game_event['type'] == 'released':
                # If it is an arrow key, reset vector back to zero
            if game_event['value'] == 'left':
                self.x_speed_left = 0
            elif game_event['value'] == 'right':
                self.x_speed_right = 0
            elif game_event['value'] == 'up':
                self.y_speed_up = 0
            elif game_event['value'] == 'down':
                self.y_speed_down = 0
        #pos = pygame.mouse.get_pos()

        #logging.debug('new pos ', self.rect.x, ' ', self.rect.y)
        return None

    def set_temporary_immortality(self):
        """ Make immortal after one damage is received """

        self.physical_obj['immortal'] = True
        self.physical_obj['damage'] = 0.0
        self.last_time_immortal = pygame.time.get_ticks()


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

        # remove immortality if time expired
        if self.physical_obj['immortal'] and not self.immortality_always:
            ticks_now = pygame.time.get_ticks()
            if ticks_now - self.last_time_immortal >= self.immortality_interval:
                self.physical_obj['immortal'] = False

        #check if damage received, if so make it immortal for a period of time
        if self.last_hit_points > self.physical_obj['hit_points']:
            self.set_temporary_immortality()

        self.last_hit_points = self.physical_obj['hit_points']


        #change the image accordingly
        if self.physical_obj['immortal'] and not self.immortality_always:
            if self.iteration % 5 == 0:
                self.image = next(self.iterator_spaceship_reverse)
        else:
            if x_speed < 0 and self.image != self.spaceship_left:
                self.image = self.spaceship_left
            elif x_speed > 0 and self.image != self.spaceship_right:
                self.image = self.spaceship_right
            elif x_speed == 0 and self.iteration % 3 == 0:
                self.image = next(self.iterator_spaceship_center)

        self.iteration += 1

class Bullet(pygame.sprite.Sprite):
    """ This class represents the bullet . """

    image_default = None

    def __init__(self, x_speed=0, y_speed=3, enemy=False, image=None):
        # Call the parent class (Sprite) constructor
        super().__init__()

        self.physical_obj = create_physical_object_dict(damage=1)
        self.x_speed = x_speed
        self.y_speed = y_speed
        self.enemy = enemy #is an enemy of is coming from an ally
        if not Bullet.image_default:
            Bullet.image_default = pygame.Surface([4, 10])
            Bullet.image_default.fill(WHITE)

        if image:
            self.image = image
        else:
            self.image = Bullet.image_default

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


def print_text_on_surface(font, str_list, surface, center, offset_line):
    """ Show multi line text on surface """

    for idx, str_display in enumerate(str_list):
        text = font.render(str_display, True, WHITE)
        center_x = center[0] - (text.get_width() // 2)
        center_y = center[1] - (text.get_height() // 2)
        surface.blit(text, [center_x, center_y + idx * offset_line])


class StartScreen(object):
    """ This class encapsulates the start screen menu """

    image_eye = None

    def __init__(self):
        sprite_sheet = SpriteSheet(os.path.join('bitmaps', 'originalStartup.png'),
                                   color_key=BLACK)
        StartScreen.image_eye = sprite_sheet.get_image(80, 0, 96, 88)

        self.font_title = pygame.font.Font(os.path.join('fonts', 'PressStart2P.ttf'),
                                           12)

        self.font = pygame.font.Font(os.path.join('fonts', 'PressStart2P.ttf'),
                                     8)

    def play_music(self):
        """ Start start screen theme """
        if pygame.mixer:
        # http://www.khinsider.com/midi/nes/guardian-legend
            pygame.mixer.music.load(os.path.join('sounds', 'title.mid'))
            pygame.mixer.music.play(-1)


    def draw(self, surface):
        """ Draw startup screen on surface """

        surface.blit(StartScreen.image_eye, (80, 0))

        center = ((SCREEN_WIDTH // 2), (SCREEN_HEIGHT // 2))
        print_text_on_surface(self.font_title, ['-= Guardian =-', 'a tribute'],
                              surface, center, 14)

        text_pos = (center[0], center[1] + 50)
        print_text_on_surface(self.font, ['press to start'],
                              surface, text_pos, 14)

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
        self.start_screen = True
        self.start_screen_obj = StartScreen()
        self.game_over = False
        self.pause = False
        self.game_over_music_enabled = False
        self.fps = 0.0
        self.font = pygame.font.Font(os.path.join('fonts', 'PressStart2P.ttf'),
                                     8)

        self.all_sprites_list = pygame.sprite.Group()
        self.player_object_list = pygame.sprite.Group()
        #it contains all enemy sprites including bullets
        self.enemy_object_list = pygame.sprite.Group()
        #it contains only ships and monsters
        self.enemy_list = pygame.sprite.Group()

        self.last_time_enemy_killed = pygame.time.get_ticks()
        self.milliseconds_per_kill = 1500



        # Create the player
        self.player = Player()
        self.all_sprites_list.add(self.player)
        self.player_object_list.add(self.player)

        self.interval_spawn_enemy = 1500
        self.last_time_spawn_enemy = pygame.time.get_ticks()

        self.max_score = 0

        # Test boss
        #self.add_whale()

        self.start_screen_obj.play_music()

        # Load TMX data
        tmx_data = load_pygame(os.path.join('maps', 'mapcorridor.tmx'))

        # Make data source for the map
        map_data = pyscroll.TiledMapData(tmx_data)

        # Make layer
        self.map_layer = pyscroll.BufferedRenderer(map_data,
                                                   (SCREEN_WIDTH,
                                                    SCREEN_HEIGHT))
        self.center_map = [self.map_layer.map_rect.width//2,
                           self.map_layer.map_rect.height - SCREEN_HEIGHT//2]

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
        max_interval = max(self.milliseconds_per_kill * 0.80,
                           self.interval_spawn_enemy / 2.0)
        max_interval = min(max_interval, self.interval_spawn_enemy * 1.5)

        if ticks_now - self.last_time_spawn_enemy >= max_interval:
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

            # Generic game events
            if self.start_screen:
                if (event.type == pygame.KEYDOWN or
                event.type == pygame.JOYBUTTONDOWN):
                    self.start_screen = False

                    if pygame.mixer:
                        # http://www.khinsider.com/midi/nes/guardian-legend
                        pygame.mixer.music.load(os.path.join('sounds', 'corridor-0.mid'))
                        pygame.mixer.music.play(-1)


            if event.type == pygame.QUIT:
                return True, screen
            elif event.type == pygame.VIDEORESIZE:
                size_screen = event.dict['size']
                screen = pygame.display.set_mode(size_screen, DISPLAY_FLAGS)
                return False, screen
            if (self.game_over and
                (event.type == pygame.MOUSEBUTTONDOWN or
                (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN) or
                (event.type == pygame.USEREVENT and event.dict['type'] == 'pause'))):
                self.__init__()
                return False, screen
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_1:
                ev_dict = {'size': [SCREEN_WIDTH, SCREEN_HEIGHT]}
                resize_event = pygame.event.Event(pygame.VIDEORESIZE, ev_dict)
                pygame.event.post(resize_event)
                return False, screen
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_2:
                ev_dict = {'size': [SCREEN_WIDTH * 2, SCREEN_HEIGHT * 2]}
                resize_event = pygame.event.Event(pygame.VIDEORESIZE, ev_dict)
                pygame.event.post(resize_event)
                return False, screen
            elif event.type == pygame.KEYDOWN and event.key == pygame.K_p:
                send_event_pause()

            if event.type == pygame.USEREVENT and event.dict['type'] == 'pause':
                self.pause = not self.pause
                if self.pause:
                    pygame.mixer.music.set_volume(0.0)
                    pygame.mixer.music.pause() # midi does not stop
                else:
                    pygame.mixer.music.set_volume(1.0)
                    pygame.mixer.music.unpause()

            #Player events

            self.player.process_event(event)

        return False, screen

    def run_logic(self):
        """
        This method is run each time through the frame. It
        updates positions and checks for collisions.
        """
        self.game_over = self.player.physical_obj['hit_points'] <= 0


        if self.start_screen:
            pass
        elif self.game_over:
            if not self.game_over_music_enabled and pygame.mixer:
                pygame.mixer.music.stop()
                pygame.mixer.music.load(os.path.join('sounds', 'game-over.mid'))
                pygame.mixer.music.play(1)
                self.game_over_music_enabled = True

                if self.player.score > self.max_score:
                    self.max_score = self.player.score

        elif self.pause:
            pass # Do nothing for now
        else:

            # Scroll map

            scroll_speed = 4

            half_height = SCREEN_HEIGHT // 2

            self.center_map[1] = self.center_map[1] - scroll_speed

            if self.center_map[1] < half_height:
                self.center_map[1] = (self.map_layer.map_rect.height -
                                      half_height - scroll_speed)

            self.map_layer.center(self.center_map)

            # Spawn new enemy if time

            self.spawn_enemy()

            # Move all the sprites
            player_x = self.player.rect.x + self.player.rect.width // 2
            player_y = self.player.rect.y + self.player.rect.height // 2

            for enemy in self.enemy_list:
                enemy.set_player_position(player_x, player_y)

            self.all_sprites_list.update()

            # Add new bullet for player
            bullet = self.player.fire()
            if bullet:
                self.all_sprites_list.add(bullet)
                self.player_object_list.add(bullet)

            # Add new bullet for enemies
            for enemy in self.enemy_list:
                bullets = enemy.fire()
                if bullets:
                    self.all_sprites_list.add(bullets)
                    self.enemy_object_list.add(bullets)

            # Check collisions
            player_hp_old = self.player.physical_obj['hit_points']

            for ally_obj in  self.player_object_list:
                enemy_hit_list = pygame.sprite.spritecollide(ally_obj,
                                                             self.enemy_object_list,
                                                             False)

                # When player is immortal to not check collision with him
                if ally_obj == self.player and self.player.physical_obj['immortal']:
                    continue

                for enemy_obj in enemy_hit_list:
                    if not isinstance(ally_obj, Bullet) or not isinstance(enemy_obj, Bullet):
                        if ally_obj.physical_obj['immortal'] is False:
                            ally_obj.physical_obj['hit_points'] -= enemy_obj.physical_obj['damage']
                        if not enemy_obj.physical_obj['immortal']:
                            enemy_obj.physical_obj['hit_points'] -= ally_obj.physical_obj['damage']
                            self.player.score += enemy_obj.physical_obj['score_value']

            # Make sound if player gets damage
            if (pygame.mixer and
                    player_hp_old - self.player.physical_obj['hit_points'] > 0):
                self.player.collision_sound.play()

            # Check for dead objects to be removed
            dead_list = []
            num_killed_enemy_now = 0

            for sprite in self.all_sprites_list:
                if sprite.physical_obj['hit_points'] <= 0:
                    logger.debug(str(sprite) + '  will be removed')
                    dead_list.append(sprite)
                    if not isinstance(sprite, Bullet):
                        num_killed_enemy_now += 1

            for sprite in dead_list:
                self.all_sprites_list.remove(sprite)
                self.player_object_list.remove(sprite)
                self.enemy_object_list.remove(sprite)
                self.enemy_list.remove(sprite)

            if num_killed_enemy_now > 0:
                ticks_now = pygame.time.get_ticks()
                interval_kills = (ticks_now - self.last_time_enemy_killed) / num_killed_enemy_now
                self.last_time_enemy_killed = ticks_now
                alpha = 0.50
                self.milliseconds_per_kill = exponential_smoothing(alpha,
                                                                   interval_kills,
                                                                   self.milliseconds_per_kill)
                #self.milliseconds_per_kill = alpha * self.milliseconds_per_kill + (1.0 - alpha) * interval_kills
                logger.debug('%10.2f ms/kills %10.2f kills/s',
                             self.milliseconds_per_kill,
                             1000.0/(self.milliseconds_per_kill))

    def display_frame(self, surface_fixed_size, true_screen):
        """ Display everything to the screen for the game. """
        surface_fixed_size.fill(BLACK)

        if self.start_screen:
            self.start_screen_obj.draw(surface_fixed_size)

        elif self.game_over:
            offset_y = 14
            str_list = ['Game Over, click the mouse', 'or press enter to restart',
                        '', '', '',
                        'Score {0} - Max {1}'.format(self.player.score, self.max_score)]
            print_text_on_surface(self.font, str_list, surface_fixed_size,
                                  (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2), offset_y)

        else:

            self.map_layer.draw(surface_fixed_size, surface_fixed_size.get_rect())

            self.all_sprites_list.draw(surface_fixed_size)

            # Score
            text_score = self.font.render("Score {0}".format(self.player.score)
                                          , True, WHITE)
            surface_fixed_size.blit(text_score, [5, 20])

            #Display fps in bottom left side
            text_fps = self.font.render("FPS {0}".format(round(self.fps, 1)),
                                        True, WHITE)
            surface_fixed_size.blit(text_fps, [SCREEN_WIDTH -95, SCREEN_HEIGHT -20])

            # Hit points
            text_hp = self.font.render("HP {0}".format(
                self.player.physical_obj['hit_points']), True, WHITE)
            surface_fixed_size.blit(text_hp, [SCREEN_WIDTH -60, 20])

            # Kill / s
            text_kill_s = self.font.render("Kill/s {0:.2f}".format(
                1000.0/(self.milliseconds_per_kill)), True, WHITE)
            surface_fixed_size.blit(text_kill_s, [0, SCREEN_HEIGHT -20])

            #test Map coordinate
            #text_map = self.font.render("Map 1 {0}".format(
            #    self.center_map[1]), True, WHITE)
            #surface_fixed_size.blit(text_map, [SCREEN_WIDTH//2, SCREEN_HEIGHT -80])

            if self.pause:
                #Display fps in bottom left side
                text_pause = self.font.render("PAUSED", True, WHITE)
                center_x = (SCREEN_WIDTH // 2) - (text_pause.get_width() // 2)
                center_y = (SCREEN_HEIGHT // 2) - (text_pause.get_height() // 2)
                surface_fixed_size.blit(text_pause, [center_x, center_y])


        true_screen.blit(pygame.transform.scale(surface_fixed_size, true_screen.get_size()), (0, 0))
        pygame.display.flip()


def main():
    """ Main program function. """
    # Initialize logger
    #logging.getLogger().setLevel(logging.INFO)
    # Initialize Pygame and set up the window
    pygame.init()

    size = [SCREEN_WIDTH, SCREEN_HEIGHT]
    screen = pygame.display.set_mode(size, DISPLAY_FLAGS)

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
        done, screen = game.process_events(screen)

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
