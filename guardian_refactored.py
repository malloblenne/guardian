"""Refactored main game class using design patterns."""

import os
import logging
import random
import pygame
from pytmx.util_pygame import load_pygame
import pyscroll

from config import get_config
from entities import Player, SmallSpaceship, WhaleBoss, Bullet, PlayerBullet, StartScreen
from factories.enemy_factory import EnemyFactory
from utils import setup_logging, DISPLAY_FLAGS


class GuardianGame:
    """Main game class implementing clean architecture with design patterns."""
    
    def __init__(self):
        """Initialize the game."""
        self.logger = setup_logging(logging.INFO)
        self.config = get_config()
        
        # Game state
        self.score = 0
        self.start_screen = True
        self.game_over = False
        self.pause = False
        self.game_over_music_enabled = False
        self.fps = 0.0
        
        # Initialize pygame
        pygame.init()
        pygame.mixer.init()
        
        # Create display
        screen_width = self.config.game['screen']['width']
        screen_height = self.config.game['screen']['height']
        self.screen = pygame.display.set_mode((screen_width, screen_height), DISPLAY_FLAGS)
        pygame.display.set_caption("Guardian")
        
        # Load font
        font_config = self.config.ui['fonts']
        self.font = pygame.font.Font(
            os.path.join('fonts', font_config['main']), 
            font_config['regular_size']
        )
        
        # Create sprite groups
        self.all_sprites_list = pygame.sprite.Group()
        self.player_object_list = pygame.sprite.Group()
        self.enemy_object_list = pygame.sprite.Group()
        self.enemy_list = pygame.sprite.Group()
        
        # Set up sprite containers
        Player.containers = self.all_sprites_list, self.player_object_list
        SmallSpaceship.containers = self.all_sprites_list, self.enemy_object_list, self.enemy_list
        WhaleBoss.containers = self.all_sprites_list, self.enemy_object_list, self.enemy_list
        Bullet.containers = self.all_sprites_list, self.enemy_object_list
        PlayerBullet.containers = self.all_sprites_list, self.player_object_list
        
        # Enemy spawning
        self.last_time_enemy_killed = pygame.time.get_ticks()
        self.milliseconds_per_kill = 1500
        self.interval_spawn_enemy = 1500
        self.last_time_spawn_enemy = pygame.time.get_ticks()
        
        # Create player
        self.player = Player()
        
        # Create start screen
        self.start_screen_obj = StartScreen()
        self.max_score = 0
        
        # Initialize map system
        self._setup_map()
        
        # Game clock
        self.clock = pygame.time.Clock()
        
        # Factory for creating enemies
        self.enemy_factory = EnemyFactory()
    
    def _setup_map(self):
        """Set up the scrolling map system."""
        # Load TMX data
        tmx_data = load_pygame(os.path.join('maps', 'mapcorridor.tmx'))
        
        # Make data source for the map
        map_data = pyscroll.data.TiledMapData(tmx_data)
        
        # Set up the scrolling map layer
        screen_width = self.config.game['screen']['width']
        screen_height = self.config.game['screen']['height']
        self.map_layer = pyscroll.BufferedRenderer(
            map_data, (screen_width, screen_height), clamp_camera=False
        )
        
        # Center map initially
        self.center_map = [self.map_layer.map_rect.width // 2, self.map_layer.map_rect.height - 50]
        self.map_layer.center(self.center_map)
    
    def spawn_enemy(self):
        """Spawn new enemy based on time interval."""
        ticks_now = pygame.time.get_ticks()
        max_interval = max(self.milliseconds_per_kill * 0.80,
                          self.interval_spawn_enemy / 2.0)
        max_interval = min(max_interval, self.interval_spawn_enemy * 1.5)
        
        if ticks_now - self.last_time_spawn_enemy >= max_interval:
            self.last_time_spawn_enemy = ticks_now
            
            # Create enemy using factory
            enemy = self.enemy_factory.create_random_enemy(self.player.score)
            
            # If it's a whale boss, slow down spawning
            if isinstance(enemy, WhaleBoss):
                slow_down_time = 60 * 1000  # 1 min
                self.last_time_spawn_enemy = ticks_now + slow_down_time
    
    def process_events(self):
        """Process all game events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return False
                elif event.key == pygame.K_RETURN and self.start_screen:
                    self.start_screen = False
                    self.start_screen_obj.stop_music()
                    # Start corridor music
                    if pygame.mixer:
                        try:
                            music_file = self.config.audio['music']['corridor']
                            pygame.mixer.music.load(music_file)
                            pygame.mixer.music.play(-1)
                        except pygame.error:
                            pass
                elif event.key == pygame.K_p and not self.start_screen:
                    self.pause = not self.pause
            
            # Forward events to player
            if not self.start_screen and not self.pause and not self.game_over:
                self.player.process_event(event)
        
        return True
    
    def run_logic(self):
        """Run main game logic."""
        if self.start_screen or self.pause or self.game_over:
            return
        
        # Scroll the map
        scroll_speed = self.config.game['physics']['scroll_speed']
        half_height = self.config.game['screen']['height'] // 2
        
        self.center_map[1] -= scroll_speed
        
        # Wrap map vertically
        if self.center_map[1] < half_height:
            self.center_map[1] = (self.map_layer.map_rect.height - 
                                  half_height - scroll_speed)
        
        self.map_layer.center(self.center_map)
        
        # Spawn new enemies
        self.spawn_enemy()
        
        # Update enemy AI with player position
        player_x = self.player.rect.x + self.player.rect.width // 2
        player_y = self.player.rect.y + self.player.rect.height // 2
        
        for enemy in self.enemy_list:
            enemy.set_player_position(player_x, player_y)
        
        # Update all sprites
        self.all_sprites_list.update()
        
        # Check collisions
        self._check_collisions()
        
        # Check game over
        if self.player.physical_obj['hit_points'] <= 0:
            self.game_over = True
            if not self.game_over_music_enabled:
                if pygame.mixer:
                    try:
                        music_file = self.config.audio['music']['game_over']
                        pygame.mixer.music.load(music_file)
                        pygame.mixer.music.play()
                        self.game_over_music_enabled = True
                    except pygame.error:
                        pass
    
    def _check_collisions(self):
        """Check all collision types."""
        player_hp_old = self.player.physical_obj['hit_points']
        
        # Player vs Enemy collisions
        for ally_obj in self.player_object_list:
            enemy_hit_list = pygame.sprite.spritecollide(
                ally_obj, self.enemy_object_list, False
            )
            
            for enemy in enemy_hit_list:
                # Damage enemy
                enemy.physical_obj['hit_points'] -= ally_obj.physical_obj['damage']
                
                # Damage player object
                if not ally_obj.physical_obj['immortal']:
                    ally_obj.physical_obj['hit_points'] -= enemy.physical_obj['damage']
                
                # Remove enemy if destroyed
                if enemy.physical_obj['hit_points'] <= 0:
                    self.player.score += enemy.physical_obj['score_value']
                    enemy.kill()
                    self.last_time_enemy_killed = pygame.time.get_ticks()
                
                # Remove ally object if destroyed (except player)
                if (ally_obj.physical_obj['hit_points'] <= 0 and 
                    ally_obj != self.player):
                    ally_obj.kill()
        
        # Play collision sound if player was hit
        if (player_hp_old > self.player.physical_obj['hit_points'] and 
            hasattr(self.player, 'collision_sound')):
            self.player.collision_sound.play()
        
        # Update score tracking
        self.max_score = max(self.max_score, self.player.score)
        
        # Adjust enemy spawn rate based on performance
        ticks_now = pygame.time.get_ticks()
        self.milliseconds_per_kill = ticks_now - self.last_time_enemy_killed
    
    def display_frame(self):
        """Render the current frame."""
        if self.start_screen:
            self.screen.fill((0, 0, 0))
            self.screen.blit(self.start_screen_obj.image, (0, 0))
            
            # Draw instructions
            text = self.font.render("PRESS ENTER TO START", True, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.centerx = self.screen.get_rect().centerx
            text_rect.y = 150
            self.screen.blit(text, text_rect)
            
        elif self.game_over:
            self.screen.fill((0, 0, 0))
            
            # Game over text
            text = self.font.render("GAME OVER", True, (255, 0, 0))
            text_rect = text.get_rect()
            text_rect.center = self.screen.get_rect().center
            self.screen.blit(text, text_rect)
            
            # Score text
            score_text = self.font.render(f"FINAL SCORE: {self.player.score}", True, (255, 255, 255))
            score_rect = score_text.get_rect()
            score_rect.centerx = self.screen.get_rect().centerx
            score_rect.y = text_rect.bottom + 20
            self.screen.blit(score_text, score_rect)
            
        else:
            # Draw map
            self.map_layer.draw(self.screen, self.screen.get_rect())
            
            # Draw all sprites
            self.all_sprites_list.draw(self.screen)
            
            # Draw UI
            self._draw_ui()
        
        # Update display
        pygame.display.flip()
    
    def _draw_ui(self):
        """Draw game UI elements."""
        # Score
        score_text = self.font.render(f"SCORE: {self.player.score}", True, (255, 255, 255))
        self.screen.blit(score_text, (10, 10))
        
        # HP
        hp_text = self.font.render(f"HP: {self.player.physical_obj['hit_points']}", True, (255, 255, 255))
        self.screen.blit(hp_text, (10, 25))
        
        # FPS (optional)
        if hasattr(self, 'fps'):
            fps_text = self.font.render(f"FPS: {int(self.fps)}", True, (255, 255, 255))
            self.screen.blit(fps_text, (200, 10))
    
    def run(self):
        """Main game loop."""
        self.start_screen_obj.play_music()
        running = True
        
        while running:
            # Process events
            running = self.process_events()
            
            # Run game logic
            self.run_logic()
            
            # Render frame
            self.display_frame()
            
            # Control frame rate
            self.fps = self.clock.tick(60)
        
        pygame.quit()


def main():
    """Main entry point."""
    game = GuardianGame()
    game.run()


if __name__ == "__main__":
    main()
