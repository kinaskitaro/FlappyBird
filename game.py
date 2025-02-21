import random
import pygame

# Draw floor
def draw_floor():
    screen.blit(floor, (floor_x_pos, 650))
    screen.blit(floor, (floor_x_pos + 432, 650))

# Create pipe
def create_pipe():
    pipe_height = [300, 400, 500]
    random_pipe_pos = random.choice(pipe_height)
    bottom_pipe = pipe_surface.get_rect(midtop=(500, random_pipe_pos))
    top_pipe = pipe_surface.get_rect(midbottom=(500, random_pipe_pos - 150))
    return bottom_pipe, top_pipe
def move_pipes(pipes):
    for pipe in pipes:
        pipe.centerx -= 5
    return pipes
def draw_pipes(pipes):
    for pipe in pipes:
        if pipe.bottom >= 600:
            screen.blit(pipe_surface, pipe)
        else:
            flip_pipe = pygame.transform.flip(pipe_surface, False, True)
            screen.blit(flip_pipe, pipe)

# Check collision
def check_collision(pipes):
    for pipe in pipes:
        if bird_rect.colliderect(pipe):
            hit_sound.play()
            return False
    if bird_rect.top <= -100 or bird_rect.bottom >= 650:
        return False
    return True

# Rotate bird
def rotate_bird(bird_old):
    new_bird = pygame.transform.rotozoom(bird_old, -bird_movement * 3, 1)
    return new_bird

# Bird animation
def bird_animation():
    new_bird = bird_frames[bird_index]
    new_bird_rect = new_bird.get_rect(center=(100, bird_rect.centery))
    return new_bird, new_bird_rect

# Score display
def score_display(game_state):
    if game_state == 'main_game':
        score_surface = game_font.render(str(int(score)), True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(216, 100))
        screen.blit(score_surface, score_rect)
    if game_state == 'game_over':
        score_surface = game_font.render(f'Score: {int(score)}', True, (255, 255, 255))
        score_rect = score_surface.get_rect(center=(216, 100))
        screen.blit(score_surface, score_rect)

        high_score_surface = game_font.render(f'High Score: {int(high_score)}', True, (255, 255, 255))
        high_score_rect = high_score_surface.get_rect(center=(216, 50))
        screen.blit(high_score_surface, high_score_rect)

# Update score
def update_score(score, high_score):
    if score > high_score:
        high_score = score
    return high_score

# Initialize pygame
pygame.init()

# Create game variables
screen = pygame.display.set_mode((432, 768))
clock = pygame.time.Clock()
gravity = 0.25
bird_movement = 0
game_active = True
game_font = pygame.font.Font('04B_19.ttf', 40)
score = 0
high_score = 0

# Load game over image
game_over_surface = pygame.transform.scale2x(pygame.image.load('assets/message.png')).convert_alpha()
game_over_rect = game_over_surface.get_rect(center=(216, 384))

# Load background image
bg = pygame.image.load('assets/background-night.png').convert()
bg = pygame.transform.scale(bg, (432, 768))

# Load floor image
floor = pygame.image.load('assets/floor.png').convert()
floor = pygame.transform.scale2x(floor)
floor_x_pos = 0

# Create bird
bird_down = pygame.transform.scale2x(pygame.image.load('assets/yellowbird-downflap.png')).convert_alpha()
bird_mid = pygame.transform.scale2x(pygame.image.load('assets/yellowbird-midflap.png')).convert_alpha()
bird_up = pygame.transform.scale2x(pygame.image.load('assets/yellowbird-upflap.png')).convert_alpha()
bird_frames = [bird_down, bird_mid, bird_up]
bird_index = 0
bird = bird_frames[bird_index]
bird_rect = bird.get_rect(center=(100, 384))
bird_flap = pygame.USEREVENT + 1
pygame.time.set_timer(bird_flap, 200)

# Create pipe
pipe_surface = pygame.image.load('assets/pipe-green.png').convert()
pipe_surface = pygame.transform.scale2x(pipe_surface)
SPAWNPIPE = pygame.USEREVENT
pygame.time.set_timer(SPAWNPIPE, 1200)
pipe_list = []

# Load sounds
pygame.mixer.pre_init(frequency=44100, size=-16, channels=2, buffer=512)
pygame.mixer.init()
flap_sound = pygame.mixer.Sound('sound/sfx_wing.wav')
flap_sound.set_volume(0.1)
hit_sound = pygame.mixer.Sound('sound/sfx_hit.wav')
hit_sound.set_volume(0.1)
score_sound = pygame.mixer.Sound('sound/sfx_point.wav')
score_sound.set_volume(0.1)
score_sound_countdown = 100

while True:
    # Check for events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            exit()
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                bird_movement = 0
                bird_movement -= 6
                flap_sound.play()
            if event.key == pygame.K_SPACE and game_active == False:
                game_active = True
                pipe_list.clear()
                bird_rect.center = (100, 384)
                bird_movement = 0
                score = 0
        if event.type == SPAWNPIPE:
            pipe_list.extend(create_pipe())
        if event.type == bird_flap:
            if bird_index < 2:
                bird_index += 1
            else:
                bird_index = 0
            bird, bird_rect = bird_animation()

    # Draw background
    screen.blit(bg, (0, 0))

    if game_active:
        # Bird movement
        bird_movement += gravity
        retated_bird = rotate_bird(bird)
        bird_rect.centery += bird_movement

        #draw bird
        screen.blit(retated_bird, bird_rect)

        # Draw pipes
        pipe_list = move_pipes(pipe_list)
        draw_pipes(pipe_list)

        game_active = check_collision(pipe_list)
        score += 0.01
        score_display('main_game')
        score_sound_countdown -= 1
        if score_sound_countdown <= 0:
            score_sound.play()
            score_sound_countdown = 100
    else:
        screen.blit(game_over_surface, game_over_rect)
        high_score = update_score(score, high_score)
        score_display('game_over') 

    # Draw floor
    floor_x_pos -= 1
    draw_floor()
    if floor_x_pos <= -432:
        floor_x_pos = 0
    
    # Update display and clock
    pygame.display.update()
    clock.tick(60)