import os
import random
import pygame
import json

# Configuration
SCREEN_WIDTH = 432
SCREEN_HEIGHT = 768
FPS = 60

# Game physics
GRAVITY = 0.25
JUMP_STRENGTH = -6
PIPE_SPEED = 5
FLOOR_SPEED = 1
PIPE_SPAWN_RATE = 1200
PIPE_GAP = 150
PIPE_HEIGHTS = [300, 400, 500]
FLOOR_Y = 650

# Bird settings
BIRD_START_X = 100
BIRD_START_Y = 384
BIRD_FLAP_RATE = 200
BIRD_ROTATION_FACTOR = 3

# Audio
AUDIO_FREQUENCY = 44100
AUDIO_SIZE = -16
AUDIO_CHANNELS = 2
AUDIO_BUFFER = 512
VOLUME = 0.1

# Score
HIGH_SCORE_FILE = 'high_score.json'

class FlappyBirdGame:
    def __init__(self):
        pygame.mixer.pre_init(frequency=AUDIO_FREQUENCY, size=AUDIO_SIZE, 
                             channels=AUDIO_CHANNELS, buffer=AUDIO_BUFFER)
        pygame.init()
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.clock = pygame.time.Clock()
        self.game_font = pygame.font.Font('04B_19.TTF', 40)
        
        self.load_assets()
        self.load_high_score()
        self.reset_game()
        
        self.SPAWNPIPE = pygame.USEREVENT
        pygame.time.set_timer(self.SPAWNPIPE, PIPE_SPAWN_RATE)
        
        self.bird_flap = pygame.USEREVENT + 1
        pygame.time.set_timer(self.bird_flap, BIRD_FLAP_RATE)
        
        self.game_state = 'menu'
        
    def load_assets(self):
        try:
            self.game_over_surface = pygame.transform.scale2x(
                pygame.image.load('assets/message.png').convert_alpha()
            )
            self.game_over_rect = self.game_over_surface.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))
            
            self.bg = pygame.image.load('assets/background-night.png').convert()
            self.bg = pygame.transform.scale(self.bg, (SCREEN_WIDTH, SCREEN_HEIGHT))
            
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
        self.pipe_list = []
        self.score = 0
        self.passed_pipes = set()
        self.game_active = False
        
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
            pipe.centerx -= PIPE_SPEED
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
                self.hit_sound.play()
                return False
        if self.bird_rect.top <= -100 or self.bird_rect.bottom >= FLOOR_Y:
            return False
        return True
        
    def rotate_bird(self, bird_old):
        new_bird = pygame.transform.rotozoom(bird_old, -self.bird_movement * BIRD_ROTATION_FACTOR, 1)
        return new_bird
        
    def bird_animation(self):
        new_bird = self.bird_frames[self.bird_index]
        new_bird_rect = new_bird.get_rect(center=(BIRD_START_X, self.bird_rect.centery))
        return new_bird, new_bird_rect
        
    def check_score(self):
        for pipe in self.pipe_list:
            if pipe.centerx == self.bird_rect.centerx and pipe not in self.passed_pipes:
                self.score += 1
                self.passed_pipes.add(pipe)
                self.score_sound.play()
                
    def score_display(self, game_state):
        if game_state == 'main_game':
            score_surface = self.game_font.render(str(int(self.score)), True, (255, 255, 255))
            score_rect = score_surface.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(score_surface, score_rect)
        elif game_state == 'game_over':
            score_surface = self.game_font.render(f'Score: {int(self.score)}', True, (255, 255, 255))
            score_rect = score_surface.get_rect(center=(SCREEN_WIDTH//2, 100))
            self.screen.blit(score_surface, score_rect)
            
            high_score_surface = self.game_font.render(f'High Score: {int(self.high_score)}', True, (255, 255, 255))
            high_score_rect = high_score_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
            self.screen.blit(high_score_surface, high_score_rect)
            
    def menu_display(self):
        self.screen.blit(self.game_over_surface, self.game_over_rect)
        
        if self.high_score > 0:
            high_score_surface = self.game_font.render(f'High Score: {int(self.high_score)}', True, (255, 255, 255))
            high_score_rect = high_score_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
            self.screen.blit(high_score_surface, high_score_rect)
            
        start_text = self.game_font.render('Press SPACE or Click to Start', True, (255, 255, 255))
        start_rect = start_text.get_rect(center=(SCREEN_WIDTH//2, 550))
        self.screen.blit(start_text, start_rect)
        
    def handle_jump(self):
        if not self.game_active:
            self.game_active = True
            self.reset_game()
        else:
            self.bird_movement = JUMP_STRENGTH
            self.flap_sound.play()
            
    def run(self):
        while True:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_high_score()
                    pygame.quit()
                    exit()
                    
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_SPACE:
                        if self.game_state == 'menu':
                            self.game_state = 'game'
                        self.handle_jump()
                        
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if self.game_state == 'menu':
                        self.game_state = 'game'
                    self.handle_jump()
                    
                if event.type == self.SPAWNPIPE and self.game_active:
                    self.pipe_list.extend(self.create_pipe())
                    
                if event.type == self.bird_flap:
                    self.bird_index = (self.bird_index + 1) % len(self.bird_frames)
                    self.bird, self.bird_rect = self.bird_animation()
                    
            self.screen.blit(self.bg, (0, 0))
            
            if self.game_state == 'menu':
                self.menu_display()
                
            elif self.game_state == 'game':
                if self.game_active:
                    self.bird_movement += GRAVITY
                    rotated_bird = self.rotate_bird(self.bird)
                    self.bird_rect.centery = int(self.bird_rect.centery + self.bird_movement)
                    self.screen.blit(rotated_bird, self.bird_rect)
                    
                    self.pipe_list = self.move_pipes(self.pipe_list)
                    self.draw_pipes(self.pipe_list)
                    
                    self.game_active = self.check_collision(self.pipe_list)
                    self.check_score()
                    self.score_display('main_game')
                    
                    if not self.game_active:
                        if self.score > self.high_score:
                            self.high_score = int(self.score)
                            self.save_high_score()
                        self.game_state = 'game_over'
                else:
                    self.screen.blit(self.game_over_surface, self.game_over_rect)
                    high_score_surface = self.game_font.render(f'High Score: {int(self.high_score)}', True, (255, 255, 255))
                    high_score_rect = high_score_surface.get_rect(center=(SCREEN_WIDTH//2, 50))
                    self.screen.blit(high_score_surface, high_score_rect)
                    
                    restart_text = self.game_font.render('Press SPACE or Click to Restart', True, (255, 255, 255))
                    restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, 550))
                    self.screen.blit(restart_text, restart_rect)
                    
            elif self.game_state == 'game_over':
                self.screen.blit(self.game_over_surface, self.game_over_rect)
                self.score_display('game_over')
                
                restart_text = self.game_font.render('Press SPACE or Click to Restart', True, (255, 255, 255))
                restart_rect = restart_text.get_rect(center=(SCREEN_WIDTH//2, 550))
                self.screen.blit(restart_text, restart_rect)
                
            self.floor_x_pos -= FLOOR_SPEED
            self.draw_floor()
            if self.floor_x_pos <= -SCREEN_WIDTH:
                self.floor_x_pos = 0
                
            pygame.display.update()
            self.clock.tick(FPS)

if __name__ == '__main__':
    game = FlappyBirdGame()
    game.run()
