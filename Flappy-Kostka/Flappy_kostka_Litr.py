import pygame
import sys
import random

pygame.init()

# Setup display
WIDTH, HEIGHT = pygame.display.get_desktop_sizes()[0]
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Flappy Kostka")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)

clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 36)
large_font = pygame.font.SysFont("consolas", 72)

# Cube properties
cube_size = 50
cube_x = WIDTH // 4
cube_y = HEIGHT // 2
cube_velocity = 0
gravity = 0.5
jump_strength = -10

# Pillars
pillar_width = 100
pillar_gap = 250
pillar_velocity = 7
pillars = []

score = 0
high_score = 0

state = "START" # START, PLAYING, GAMEOVER

def add_pillar():
    # Ensure there is enough space for the gap
    gap_y = random.randint(150, HEIGHT - 150 - pillar_gap)
    pillars.append({
        "x": WIDTH, 
        "top_height": gap_y, 
        "bottom_y": gap_y + pillar_gap, 
        "passed": False
    })

def reset_game():
    global cube_y, cube_velocity, pillars, score, state
    cube_y = HEIGHT // 2
    cube_velocity = 0
    pillars = []
    score = 0
    add_pillar()
    state = "PLAYING"

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Quit on ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
            
        # Jump on Mouse Click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == "START" or state == "GAMEOVER":
                reset_game()
            elif state == "PLAYING":
                cube_velocity = jump_strength
                
        # Jump on Spacebar
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if state == "START" or state == "GAMEOVER":
                    reset_game()
                elif state == "PLAYING":
                    cube_velocity = jump_strength

    if state == "PLAYING":
        # Update cube
        cube_velocity += gravity
        cube_y += cube_velocity

        # Update pillars
        for pillar in pillars:
            pillar["x"] -= pillar_velocity

            # Check if passed pillar for score
            if not pillar["passed"] and pillar["x"] + pillar_width < cube_x:
                pillar["passed"] = True
                score += 1
                if score > high_score:
                    high_score = score

        # Remove off-screen pillars
        if len(pillars) > 0 and pillars[0]["x"] + pillar_width < 0:
            pillars.pop(0)

        # Add new pillars
        # Spawns a new pillar when the last pillar moves far enough onto the screen
        if len(pillars) == 0 or pillars[-1]["x"] < WIDTH - 450:
            add_pillar()

        # Collisions
        cube_rect = pygame.Rect(cube_x, cube_y, cube_size, cube_size)

        # Floor / Ceiling Collision
        if cube_y < 0 or cube_y + cube_size > HEIGHT:
            state = "GAMEOVER"

        # Pillar Collision
        for pillar in pillars:
            top_rect = pygame.Rect(pillar["x"], 0, pillar_width, pillar["top_height"])
            bottom_rect = pygame.Rect(pillar["x"], pillar["bottom_y"], pillar_width, HEIGHT - pillar["bottom_y"])

            if cube_rect.colliderect(top_rect) or cube_rect.colliderect(bottom_rect):
                state = "GAMEOVER"

    # Draw
    screen.fill(BLACK)

    if state == "START":
        text = large_font.render("FLAPPY KOSTKA", True, WHITE)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//3))
        text2 = font.render("Click or press Space to Start", True, WHITE)
        screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2))
        text3 = font.render("Press ESC to Quit", True, WHITE)
        screen.blit(text3, (WIDTH//2 - text3.get_width()//2, HEIGHT//2 + 50))
        
    elif state == "PLAYING":
        # Draw pillars
        for pillar in pillars:
            pygame.draw.rect(screen, GREEN, (pillar["x"], 0, pillar_width, pillar["top_height"]))
            pygame.draw.rect(screen, GREEN, (pillar["x"], pillar["bottom_y"], pillar_width, HEIGHT - pillar["bottom_y"]))

        # Draw cube
        pygame.draw.rect(screen, RED, (cube_x, cube_y, cube_size, cube_size))

        # Draw score
        score_text = large_font.render(str(score), True, WHITE)
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 50))
        
    elif state == "GAMEOVER":
        # Draw pillars
        for pillar in pillars:
            pygame.draw.rect(screen, GREEN, (pillar["x"], 0, pillar_width, pillar["top_height"]))
            pygame.draw.rect(screen, GREEN, (pillar["x"], pillar["bottom_y"], pillar_width, HEIGHT - pillar["bottom_y"]))

        # Draw cube
        pygame.draw.rect(screen, RED, (cube_x, cube_y, cube_size, cube_size))

        # Game over UI
        text = large_font.render("GAME OVER", True, RED)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//3))
        
        text2 = font.render(f"Score: {score}  High Score: {high_score}", True, WHITE)
        screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2))
        
        text3 = font.render("Click or press Space to Restart", True, WHITE)
        screen.blit(text3, (WIDTH//2 - text3.get_width()//2, HEIGHT//2 + 50))
        
        text4 = font.render("Press ESC to Quit", True, WHITE)
        screen.blit(text4, (WIDTH//2 - text4.get_width()//2, HEIGHT//2 + 100))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
