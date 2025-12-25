import os
import random
import pygame
import json
import math

# Configuration
SCREEN_WIDTH = 432
SCREEN_HEIGHT = 768
FPS = 60

# Game physics
GRAVITY = 0.25
JUMP_STRENGTH = -6
BASE_PIPE_SPEED = 5
FLOOR_SPEED = 1
BASE_PIPE_SPAWN_RATE = 1200
PIPE_GAP = 150
PIPE_HEIGHTS = [300, 400, 500]
FLOOR_Y = 650

# Bird settings
BIRD_START_X = 100
BIRD_START_Y = 384
BIRD_FLAP_RATE = 10
MAX_BIRD_ROTATION = 30
MIN_BIRD_ROTATION = -90
ROTATION_SPEED = 5

# Audio
AUDIO_FREQUENCY = 44100
AUDIO_SIZE = -16
AUDIO_CHANNELS = 2
AUDIO_BUFFER = 512
VOLUME = 0.1

# Effects
FLASH_DURATION = 5
SHAKE_DURATION = 10
SHAKE_INTENSITY = 3
TRAIL_LENGTH = 5

# Difficulty
DIFFICULTY_SCALE = 0.5
MAX_PIPE_SPEED = 8
MIN_PIPE_SPAWN_RATE = 800

# Score
HIGH_SCORE_FILE = 'high_score.json'

class Particle:
    def __init__(self, x, y, color, size, velocity, lifetime):
        self.x = x
        self.y = y
        self.color = color
        self.size = size
        self.velocity = velocity
        self.lifetime = lifetime
        self.age = 0
        
    def update(self, dt):
        self.x += self.velocity[0] * dt
        self.y += self.velocity[1] * dt
        self.age += dt
        self.size *= 0.95
        return self.age < self.lifetime
        
    def draw(self, screen):
        if self.size > 0:
            alpha = int(255 * (1 - self.age / self.lifetime))
            particle_surf = pygame.Surface((int(self.size * 2), int(self.size * 2)), pygame.SRCALPHA)
            pygame.draw.circle(particle_surf, (*self.color, alpha), (int(self.size), int(self.size)), int(self.size))
            screen.blit(particle_surf, (int(self.x - self.size), int(self.y - self.size)))

class FlappyBirdGame:
    def __init__(self):
        pygame.mixer.pre_init(frequency=AUDIO_FREQUENCY, size=AUDIO_SIZE, 
                             channels=AUDIO_CHANNELS, buffer=AUDIO_BUFFER)
        pygame.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.game_font = pygame.font.Font('04B_19.TTF', 40)
        self.small_font = pygame.font.Font('04B_19.TTF', 20)
        
        # Initialize timers before reset_game
        self.SPAWNPIPE = pygame.USEREVENT
        
        # Difficulty variables
        self.current_pipe_speed = BASE_PIPE_SPEED
        self.current_spawn_rate = BASE_PIPE_SPAWN_RATE
        pygame.time.set_timer(self.SPAWNPIPE, self.current_spawn_rate)
        
        # Bird animation timer
        self.bird_flap_timer = 0
        
        # Effect variables
        self.particles = []
        self.trail = []
        self.flash_count = 0
        self.shake_count = 0
        self.shake_offset = [0, 0]
        self.flash_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.flash_surface.set_alpha(100)
        
        self.game_active = False
        self.paused = False
        self.sound_enabled = True
        
        self.load_assets()
        self.load_high_score()
        self.reset_game()
        
        self.game_state = 'menu'
        
    def load_assets(self):
        try:
            self.game_over_surface = pygame.transform.scale2x(
                pygame.image.load('assets/message.png').convert_alpha()
            )
            self.game_over_rect = self.game_over_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            
            self.bg = pygame.image.load('assets/background-night.png').convert()
            self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            self.bg_x = 0
            
            self.floor = pygame.image.load('assets/floor.png').convert()
            self.floor = pygame.transform.scale2x(self.floor)
            self.floor_x_pos = 0
            
            bird_down = pygame.transform.scale2x(pygame.image.load('assets/yellowbird-downflap.png').convert_alpha())
            bird_mid = pygame.transform.scale2x(pygame.image.load('assets/yellowbird-midflap.png').convert_alpha())
            bird_up = pygame.transform.scale2x(pygame.image.load('assets/yellowbird-upflap.png').convert_alpha())
            self.bird_frames = [bird_down, bird_mid, bird_up]
            
            self.pipe_surface = pygame.image.load('assets/pipe-green.png').convert()
            self.pipe_surface = pygame.transform.scale2x(self.pipe_surface)
            
            pygame.mixer.init()
            self.flap_sound = pygame.mixer.Sound('sound/sfx_wing.wav')
            self.flap_sound.set_volume(VOLUME)
            self.hit_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
            self.hit_sound.set_volume(VOLUME)
            self.score_sound = pygame.mixer.Sound('sound/sfx_point.wav')
            self.score_sound.set_volume(VOLUME)
            
        except FileNotFoundError as e:
            print(f"Error loading assets: {e}")
            pygame.quit()
            exit()
            
    def load_high_score(self):
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, 'r') as f:
                    data = json.load(f)
                    self.high_score = data.get('high_score', 0)
            else:
                self.high_score = 0
        except:
            self.high_score = 0
            
    def save_high_score(self):
        try:
            with open(HIGH_SCORE_FILE, 'w') as f:
                json.dump({'high_score': self.high_score}, f)
        except:
            pass
            
    def reset_game(self):
        self.bird_index = 0
        self.bird = self.bird_frames[self.bird_index]
        self.bird_rect = self.bird.get_rect(center=(BIRD_START_X, BIRD_START_Y))
        self.bird_movement = 0
        self.bird_rotation = 0
        self.bird_flap_timer = 0
        self.pipe_list = []
        self.score = 0
        self.passed_pipes = set()
        self.particles = []
        self.trail = []
        self.current_pipe_speed = BASE_PIPE_SPEED
        self.current_spawn_rate = BASE_PIPE_SPAWN_RATE
        pygame.time.set_timer(self.SPAWNPIPE, self.current_spawn_rate)
        
    def create_jump_particles(self):
        for _ in range(5):
            angle = random.uniform(math.pi * 0.7, math.pi * 0.9)
            speed = random.uniform(2, 4)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            particle = Particle(
                self.bird_rect.centerx - 10,
                self.bird_rect.centery + 10,
                (255, 255, 255),
                random.uniform(3, 6),
                velocity,
                random.uniform(10, 20)
            )
            self.particles.append(particle)
            
    def create_score_particles(self):
        for _ in range(8):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(2, 5)
            velocity = (math.cos(angle) * speed, math.sin(angle) * speed)
            particle = Particle(
                self.bird_rect.centerx,
                self.bird_rect.centery,
                (255, 215, 0),
                random.uniform(4, 7),
                velocity,
                random.uniform(15, 25)
            )
            self.particles.append(particle)
            
    def update_trail(self):
        self.trail.append({
            'rect': self.bird_rect.copy(),
            'alpha': 200
        })
        if len(self.trail) > TRAIL_LENGTH:
            self.trail.pop(0)
        for t in self.trail:
            t['alpha'] = max(0, t['alpha'] - 15)
            
    def draw_trail(self):
        for t in self.trail:
            if t['alpha'] > 0:
                trail_surf = self.bird.copy()
                trail_surf.set_alpha(t['alpha'])
                self.screen.blit(trail_surf, t['rect'])
                
    def update_difficulty(self):
        new_speed = min(MAX_PIPE_SPEED, BASE_PIPE_SPEED + self.score * DIFFICULTY_SCALE)
        new_spawn_rate = max(MIN_PIPE_SPAWN_RATE, BASE_PIPE_SPAWN_RATE - self.score * 30)
        
        if abs(new_speed - self.current_pipe_speed) > 0.01:
            self.current_pipe_speed = new_speed
        if abs(new_spawn_rate - self.current_spawn_rate) > 1:
            self.current_spawn_rate = int(new_spawn_rate)
            pygame.time.set_timer(self.SPAWNPIPE, self.current_spawn_rate)
            
    def draw_floor(self):
        self.screen.blit(self.floor, (self.floor_x_pos, FLOOR_Y))
        self.screen.blit(self.floor, (self.floor_x_pos + SCREEN_WIDTH, FLOOR_Y))
        
    def create_pipe(self):
        random_pipe_pos = random.choice(PIPE_HEIGHTS)
        bottom_pipe = self.pipe_surface.get_rect(midtop=(SCREEN_WIDTH + 50, random_pipe_pos))
        top_pipe = self.pipe_surface.get_rect(midbottom=(SCREEN_WIDTH + 50, random_pipe_pos - PIPE_GAP))
        return bottom_pipe, top_pipe
        
    def move_pipes(self, pipes):
        for pipe in pipes:
            pipe.centerx -= self.current_pipe_speed
        return pipes
        
    def draw_pipes(self, pipes):
        for pipe in pipes:
            if pipe.bottom >= 600:
                self.screen.blit(self.pipe_surface, pipe)
            else:
                flip_pipe = pygame.transform.flip(self.pipe_surface, False, True)
                self.screen.blit(flip_pipe, pipe)
                
    def check_collision(self, pipes):
        for pipe in pipes:
            if self.bird_rect.colliderect(pipe):
                if self.sound_enabled:
                    self.hit_sound.play()
                self.shake_count = SHAKE_DURATION
                return False
        if self.bird_rect.top <= -100 or self.bird_rect.bottom >= FLOOR_Y:
            self.shake_count = SHAKE_DURATION
            return False
        return True
        
    def rotate_bird(self):
        # Target rotation based on movement
        if self.bird_movement < 0:
            target_rotation = MAX_BIRD_ROTATION
        else:
            target_rotation = MIN_BIRD_ROTATION
        
        # Smoothly interpolate towards target
        if self.bird_rotation < target_rotation:
            self.bird_rotation += ROTATION_SPEED
            if self.bird_rotation > target_rotation:
                self.bird_rotation = target_rotation
        elif self.bird_rotation > target_rotation:
            self.bird_rotation -= ROTATION_SPEED
            if self.bird_rotation < target_rotation:
                self.bird_rotation = target_rotation
        
        rotated_bird = pygame.transform.rotozoom(self.bird, self.bird_rotation, 1)
        rotated_rect = rotated_bird.get_rect(center=self.bird_rect.center)
        return rotated_bird, rotated_rect
        
    def bird_animation(self):
        new_bird = self.bird_frames[self.bird_index]
        new_bird_rect = new_bird.get_rect(center=self.bird_rect.center)
        return new_bird, new_bird_rect
        
    def check_score(self):
        for pipe in self.pipe_list:
            pipe_id = id(pipe)
            if pipe.centerx < self.bird_rect.centerx and pipe_id not in self.passed_pipes:
                self.score += 1
                self.passed_pipes.add(pipe_id)
                if self.sound_enabled:
                    self.score_sound.play()
                self.flash_count = FLASH_DURATION
                self.create_score_particles()
                self.update_difficulty()
                
    def score_display(self, game_state):
        if game_state == 'main_game':
            score_surface = self.game_font.render(str(int(self.score)), True, (255, 255, 255))
            score_rect = score_surface.get_rect(center=(SCREEN_WIDTH//2, 100))
            
            score_shadow = self.game_font.render(str(int(self.score)), True, (0, 0, 0))
            score_shadow_rect = score_shadow.get_rect(center=(SCREEN_WIDTH//2 + 2, 102))
            
            self.screen.blit(score_shadow, score_shadow_rect)
            self.screen.blit(score_surface, score_rect)
        elif game_state == 'game_over':
            score_surface = self.game_font.render(f'Score: {int(self.score)}', True, (255, 255, 255))
            score_rect = score_surface.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(score_surface, score_rect)
            
            high_score_surface = self.game_font.render(f'High Score: {int(self.high_score)}', True, (255, 215, 0))
            high_score_rect = high_score_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
            self.screen.blit(high_score_surface, high_score_rect)
            
            if self.score >= self.high_score and self.score > 0:
                new_record_text = self.small_font.render('NEW RECORD!', True, (255, 100, 100))
                new_record_rect = new_record_text.get_rect(center=(SCREEN_WIDTH//2, 130))
                self.screen.blit(new_record_text, new_record_rect)
                
    def menu_display(self):
        self.screen.blit(self.game_over_surface, self.game_over_rect)
        
        if self.high_score > 0:
            high_score_surface = self.game_font.render(f'High Score: {int(self.high_score)}', True, (255, 215, 0))
            high_score_rect = high_score_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
            self.screen.blit(high_score_surface, high_score_rect)
            
        # Create semi-transparent background for text
        text_bg = pygame.Surface((SCREEN_WIDTH - 40, 160), pygame.SRCALPHA)
        text_bg.fill((0, 0, 0, 150))
        text_bg_rect = text_bg.get_rect(center=(SCREEN_WIDTH//2, 480))
        self.screen.blit(text_bg, text_bg_rect)
        
        # Split text into two lines
        start_line1 = self.game_font.render('Press SPACE', True, (255, 255, 255))
        start_line1_rect = start_line1.get_rect(center=(SCREEN_WIDTH//2, 440))
        
        for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            start_line1_outline = self.game_font.render('Press SPACE', True, (0, 0, 0))
            start_line1_outline_rect = start_line1_outline.get_rect(center=(SCREEN_WIDTH//2 + offset_x, 440 + offset_y))
            self.screen.blit(start_line1_outline, start_line1_outline_rect)
        self.screen.blit(start_line1, start_line1_rect)
        
        start_line2 = self.game_font.render('or Click to Start', True, (255, 255, 255))
        start_line2_rect = start_line2.get_rect(center=(SCREEN_WIDTH//2, 475))
        
        for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            start_line2_outline = self.game_font.render('or Click to Start', True, (0, 0, 0))
            start_line2_outline_rect = start_line2_outline.get_rect(center=(SCREEN_WIDTH//2 + offset_x, 475 + offset_y))
            self.screen.blit(start_line2_outline, start_line2_outline_rect)
        self.screen.blit(start_line2, start_line2_rect)
        
        controls_text = self.small_font.render('SPACE: Jump | P: Pause | M: Toggle Sound', True, (255, 255, 200))
        controls_rect = controls_text.get_rect(center=(SCREEN_WIDTH//2, 520))
        
        for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
            controls_outline = self.small_font.render('SPACE: Jump | P: Pause | M: Toggle Sound', True, (0, 0, 0))
            controls_outline_rect = controls_outline.get_rect(center=(SCREEN_WIDTH//2 + offset_x, 520 + offset_y))
            self.screen.blit(controls_outline, controls_outline_rect)
        self.screen.blit(controls_text, controls_rect)
        
    def pause_display(self):
        pause_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        pause_surface.fill((0, 0, 0, 128))
        self.screen.blit(pause_surface, (0, 0))
        
        pause_text = self.game_font.render('PAUSED', True, (255, 255, 255))
        pause_rect = pause_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
        self.screen.blit(pause_text, pause_rect)
        
        resume_text = self.small_font.render('Press P or SPACE to Resume', True, (200, 200, 200))
        resume_rect = resume_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2 + 50))
        self.screen.blit(resume_text, resume_rect)
        
    def handle_jump(self):
        if self.paused:
            self.paused = False
        elif not self.game_active:
            self.game_active = True
            self.game_state = 'game'
            self.reset_game()
        elif self.game_active:
            self.bird_movement = JUMP_STRENGTH
            if self.sound_enabled:
                self.flap_sound.play()
            self.create_jump_particles()
            
    def toggle_sound(self):
        self.sound_enabled = not self.sound_enabled
        vol = VOLUME if self.sound_enabled else 0
        self.flap_sound.set_volume(vol)
        self.hit_sound.set_volume(vol)
        self.score_sound.set_volume(vol)
            
    def update_effects(self, dt):
        self.particles = [p for p in self.particles if p.update(dt)]
        
        if self.flash_count > 0:
            self.flash_count -= 1
            
        if self.shake_count > 0:
            self.shake_offset = [
                random.uniform(-SHAKE_INTENSITY, SHAKE_INTENSITY),
                random.uniform(-SHAKE_INTENSITY, SHAKE_INTENSITY)
            ]
            self.shake_count -= 1
        else:
            self.shake_offset = [0, 0]
            
    def draw_effects(self):
        for particle in self.particles:
            particle.draw(self.screen)
            
        if self.flash_count > 0:
            self.screen.blit(self.flash_surface, (0, 0))
            
    def run(self):
        while True:
            dt = self.clock.tick(FPS) / 1000.0 * 60
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_high_score()
                    pygame.quit()
                    exit()
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        self.handle_jump()
                    elif event.key == pygame.K_p:
                        if self.game_active:
                            self.paused = not self.paused
                    elif event.key == pygame.K_m:
                        self.toggle_sound()
                    elif event.key == pygame.K_ESCAPE:
                        if self.paused:
                            self.paused = False
                        
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.handle_jump()
                    
                if event.type == self.SPAWNPIPE and self.game_active and not self.paused:
                    self.pipe_list.extend(self.create_pipe())
                    
            self.screen.blit(self.bg, (0, 0))
            
            if self.game_state == 'menu':
                self.menu_display()
                
            elif self.game_state == 'game':
                # Update bird animation
                self.bird_flap_timer += dt
                if self.bird_flap_timer >= BIRD_FLAP_RATE:
                    self.bird_index = (self.bird_index + 1) % len(self.bird_frames)
                    self.bird, self.bird_rect = self.bird_animation()
                    self.bird_flap_timer = 0
                    
                if self.game_active and not self.paused:
                    self.bird_movement += GRAVITY
                    self.bird_rect.centery = int(self.bird_rect.centery + self.bird_movement)
                    
                    rotated_bird, rotated_rect = self.rotate_bird()
                    self.update_trail()
                    
                    self.pipe_list = self.move_pipes(self.pipe_list)
                    self.draw_pipes(self.pipe_list)
                    
                    self.draw_trail()
                    self.screen.blit(rotated_bird, rotated_rect)
                    
                    self.game_active = self.check_collision(self.pipe_list)
                    self.check_score()
                    self.score_display('main_game')
                    self.update_effects(dt)
                    self.draw_effects()
                    
                    if not self.game_active:
                        if self.score > self.high_score:
                            self.high_score = int(self.score)
                            self.save_high_score()
                        self.game_state = 'game_over'
                elif self.paused:
                    self.pipe_list = self.move_pipes(self.pipe_list)
                    self.draw_pipes(self.pipe_list)
                    self.screen.blit(self.bird, self.bird_rect)
                    self.score_display('main_game')
                    self.pause_display()
                else:
                    self.screen.blit(self.game_over_surface, self.game_over_rect)
                    self.score_display('game_over')
                    
                    # Create semi-transparent background for text
                    text_bg = pygame.Surface((SCREEN_WIDTH - 40, 100), pygame.SRCALPHA)
                    text_bg.fill((0, 0, 0, 150))
                    text_bg_rect = text_bg.get_rect(center=(SCREEN_WIDTH//2, 520))
                    self.screen.blit(text_bg, text_bg_rect)
                    
                    # Split text into two lines
                    restart_line1 = self.game_font.render('Press SPACE', True, (255, 255, 255))
                    restart_line1_rect = restart_line1.get_rect(center=(SCREEN_WIDTH//2, 500))
                    
                    for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                        restart_line1_outline = self.game_font.render('Press SPACE', True, (0, 0, 0))
                        restart_line1_outline_rect = restart_line1_outline.get_rect(center=(SCREEN_WIDTH//2 + offset_x, 500 + offset_y))
                        self.screen.blit(restart_line1_outline, restart_line1_outline_rect)
                    self.screen.blit(restart_line1, restart_line1_rect)
                    
                    restart_line2 = self.game_font.render('or Click to Restart', True, (255, 255, 255))
                    restart_line2_rect = restart_line2.get_rect(center=(SCREEN_WIDTH//2, 535))
                    
                    for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                        restart_line2_outline = self.game_font.render('or Click to Restart', True, (0, 0, 0))
                        restart_line2_outline_rect = restart_line2_outline.get_rect(center=(SCREEN_WIDTH//2 + offset_x, 535 + offset_y))
                        self.screen.blit(restart_line2_outline, restart_line2_outline_rect)
                    self.screen.blit(restart_line2, restart_line2_rect)
                    
            elif self.game_state == 'game_over':
                self.screen.blit(self.game_over_surface, self.game_over_rect)
                self.score_display('game_over')
                
                # Create semi-transparent background for text
                text_bg = pygame.Surface((SCREEN_WIDTH - 40, 100), pygame.SRCALPHA)
                text_bg.fill((0, 0, 0, 150))
                text_bg_rect = text_bg.get_rect(center=(SCREEN_WIDTH//2, 520))
                self.screen.blit(text_bg, text_bg_rect)
                
                # Split text into two lines
                restart_line1 = self.game_font.render('Press SPACE', True, (255, 255, 255))
                restart_line1_rect = restart_line1.get_rect(center=(SCREEN_WIDTH//2, 500))
                
                for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    restart_line1_outline = self.game_font.render('Press SPACE', True, (0, 0, 0))
                    restart_line1_outline_rect = restart_line1_outline.get_rect(center=(SCREEN_WIDTH//2 + offset_x, 500 + offset_y))
                    self.screen.blit(restart_line1_outline, restart_line1_outline_rect)
                self.screen.blit(restart_line1, restart_line1_rect)
                
                restart_line2 = self.game_font.render('or Click to Restart', True, (255, 255, 255))
                restart_line2_rect = restart_line2.get_rect(center=(SCREEN_WIDTH//2, 535))
                
                for offset_x, offset_y in [(-2, -2), (-2, 2), (2, -2), (2, 2)]:
                    restart_line2_outline = self.game_font.render('or Click to Restart', True, (0, 0, 0))
                    restart_line2_outline_rect = restart_line2_outline.get_rect(center=(SCREEN_WIDTH//2 + offset_x, 535 + offset_y))
                    self.screen.blit(restart_line2_outline, restart_line2_outline_rect)
                self.screen.blit(restart_line2, restart_line2_rect)
                
            self.floor_x_pos -= FLOOR_SPEED
            self.draw_floor()
            if self.floor_x_pos <= -SCREEN_WIDTH:
                self.floor_x_pos = 0
                
            if self.shake_count > 0:
                shake_surf = self.screen.copy()
                self.screen.blit(shake_surf, (int(self.shake_offset[0]), int(self.shake_offset[1])))
                
            pygame.display.update()

if __name__ == '__main__':
    game = FlappyBirdGame()
    game.run()
