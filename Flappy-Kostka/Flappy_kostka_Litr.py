import pygame
import sys
import random
import math

pygame.init()

# Nastavení zobrazení
WIDTH, HEIGHT = pygame.display.get_desktop_sizes()[0]
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Flappy Kostka")

# Barvy
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GREEN = (0, 255, 0)
RED = (255, 0, 0)
SKY_BLUE = (135, 206, 235)
BLUE = (0, 0, 255)
YELLOW = (255, 255, 0)
PURPLE = (128, 0, 128)
ORANGE = (255, 165, 0)

clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 36)
large_font = pygame.font.SysFont("consolas", 72)

# Vlastnosti kostky
cube_size = 50
cube_x = WIDTH // 4
cube_y = HEIGHT // 2
cube_velocity = 0
gravity = 0.5
jump_strength = -10

# Sloupy
pillar_width = 100
pillar_gap = 320
pillar_velocity = 7
pillars = []
available_pillar_colors = [GREEN, RED, BLUE, YELLOW, PURPLE, ORANGE]
current_pillar_color = GREEN

score = 0
high_score = 0

state = "START" # START, HRANÍ, KONEC HRY

# Mraky
clouds = []
for _ in range(6):
    clouds.append({
        "x": random.randint(0, WIDTH),
        "y": random.randint(50, HEIGHT // 2),
        "speed": random.uniform(0.5, 1.5),
        "size": random.randint(50, 100)
    })

def draw_clouds():
    for cloud in clouds:
        cx = int(cloud["x"])
        cy = int(cloud["y"])
        cs = cloud["size"]
        pygame.draw.circle(screen, WHITE, (cx, cy), cs // 2)
        pygame.draw.circle(screen, WHITE, (cx + int(cs / 1.5), cy - int(cs / 3)), int(cs / 1.5))
        pygame.draw.circle(screen, WHITE, (cx + int(cs * 1.3), cy), cs // 2)
        
        # Posun mraku
        cloud["x"] -= cloud["speed"]
        if cloud["x"] + cs * 2 < 0:
            cloud["x"] = WIDTH + cs
            cloud["y"] = random.randint(50, HEIGHT // 2)
            cloud["speed"] = random.uniform(0.5, 1.5)
            cloud["size"] = random.randint(50, 100)

def add_pillar():
    # Zajištění dostatku místa pro mezeru
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

def draw_cube_with_line(draw_x=None, draw_y=None):
    if draw_x is None:
        draw_x = cube_x
    if draw_y is None:
        draw_y = cube_y

    angle = math.degrees(math.atan2(-cube_velocity, pillar_velocity))
    
    # Zvětšení plochy tak, aby se na ni vešla přečnívající čára, s udržením kostky přesně uprostřed
    pad = 20
    surf_size = cube_size + pad * 2
    cube_surface = pygame.Surface((surf_size, surf_size), pygame.SRCALPHA)
    
    # Střed plochy
    scx = surf_size / 2
    scy = surf_size / 2
    
    # Vykreslení červené kostky uprostřed
    cube_rect = pygame.Rect(scx - cube_size / 2, scy - cube_size / 2, cube_size, cube_size)
    pygame.draw.rect(cube_surface, RED, cube_rect)
    
    # Vykreslení bílé čáry přečnívající ze středu pravé strany červené kostky
    start_pos = (scx, scy) 
    end_pos = (scx + cube_size / 2 + pad, scy)
    pygame.draw.line(cube_surface, WHITE, start_pos, end_pos, 4)
    
    # Otočení celé plochy
    rotated_cube = pygame.transform.rotate(cube_surface, angle)
    
    # Souřadnice středu kostky na obrazovce
    cx = draw_x + cube_size / 2
    cy = draw_y + cube_size / 2
    
    # Vykreslení otočené kostky na střed
    rot_rect = rotated_cube.get_rect(center=(cx, cy))
    screen.blit(rotated_cube, rot_rect.topleft)

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        # Ukončení pomocí ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False
            
        # Skok kliknutím myši
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if state == "START":
                play_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 200, 200, 80)
                settings_button_rect = pygame.Rect(WIDTH - 180, 20, 160, 50)
                if play_button_rect.collidepoint(event.pos):
                    reset_game()
                elif settings_button_rect.collidepoint(event.pos):
                    state = "SETTINGS"
            elif state == "SETTINGS":
                back_button_rect = pygame.Rect(20, 20, 130, 50)
                if back_button_rect.collidepoint(event.pos):
                    state = "START"
                num_colors = len(available_pillar_colors)
                for i, col in enumerate(available_pillar_colors):
                    rect = pygame.Rect(WIDTH//2 - (num_colors*80)//2 + i*80, HEIGHT//2 - 30, 60, 60)
                    if rect.collidepoint(event.pos):
                        current_pillar_color = col
            elif state == "GAMEOVER":
                reset_game()
            elif state == "PLAYING":
                cube_velocity = jump_strength
                
        # Skok mezerníkem
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                if state == "GAMEOVER":
                    reset_game()
                elif state == "PLAYING":
                    cube_velocity = jump_strength

    if state == "PLAYING":
        # Aktualizace kostky
        cube_velocity += gravity
        cube_y += cube_velocity

        # Aktualizace sloupů
        for pillar in pillars:
            pillar["x"] -= pillar_velocity

            # Kontrola průletu sloupem pro skóre
            if not pillar["passed"] and pillar["x"] + pillar_width < cube_x:
                pillar["passed"] = True
                score += 1
                if score > high_score:
                    high_score = score

        # Odstranění sloupů mimo obrazovku
        if len(pillars) > 0 and pillars[0]["x"] + pillar_width < 0:
            pillars.pop(0)

        # Přidání nových sloupů
        # Objeví se nový sloup, když se poslední sloup dostatečně posune na obrazovku
        if len(pillars) == 0 or pillars[-1]["x"] < WIDTH - 650:
            add_pillar()

        # Kolize
        cube_rect = pygame.Rect(cube_x, cube_y, cube_size, cube_size)

        # Kolize s podlahou / stropem
        if cube_y < 0 or cube_y + cube_size > HEIGHT:
            state = "GAMEOVER"

        # Kolize se sloupem
        for pillar in pillars:
            top_rect = pygame.Rect(pillar["x"], 0, pillar_width, pillar["top_height"])
            bottom_rect = pygame.Rect(pillar["x"], pillar["bottom_y"], pillar_width, HEIGHT - pillar["bottom_y"])

            if cube_rect.colliderect(top_rect) or cube_rect.colliderect(bottom_rect):
                state = "GAMEOVER"

    # Vykreslování
    screen.fill(SKY_BLUE)
    draw_clouds()

    if state == "START":
        # Vykreslení kostky uprostřed obrazovky
        draw_cube_with_line(WIDTH // 2 - cube_size // 2, HEIGHT // 2 - cube_size // 2)

        text = large_font.render("FLAPPY KOSTKA", True, BLACK)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//4))

        # Vykreslení tlačítka PLAY
        play_button_rect = pygame.Rect(WIDTH//2 - 100, HEIGHT - 200, 200, 80)
        pygame.draw.rect(screen, GREEN, play_button_rect)
        pygame.draw.rect(screen, BLACK, play_button_rect, 4) # border
        
        play_text = font.render("PLAY", True, BLACK)
        screen.blit(play_text, (play_button_rect.centerx - play_text.get_width()//2, play_button_rect.centery - play_text.get_height()//2))

        # Vykreslení tlačítka SETTINGS
        settings_button_rect = pygame.Rect(WIDTH - 180, 20, 160, 50)
        pygame.draw.rect(screen, WHITE, settings_button_rect)
        pygame.draw.rect(screen, BLACK, settings_button_rect, 4)
        set_text = font.render("SETTINGS", True, BLACK)
        screen.blit(set_text, (settings_button_rect.centerx - set_text.get_width()//2, settings_button_rect.centery - set_text.get_height()//2))

        text3 = font.render("Press ESC to Quit", True, BLACK)
        screen.blit(text3, (WIDTH//2 - text3.get_width()//2, HEIGHT - 100))
        
    elif state == "SETTINGS":
        text = large_font.render("CHOOSE PILLAR COLOR", True, BLACK)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//4))
        
        back_button_rect = pygame.Rect(20, 20, 130, 50)
        pygame.draw.rect(screen, WHITE, back_button_rect)
        pygame.draw.rect(screen, BLACK, back_button_rect, 4)
        back_text = font.render("BACK", True, BLACK)
        screen.blit(back_text, (back_button_rect.centerx - back_text.get_width()//2, back_button_rect.centery - back_text.get_height()//2))

        num_colors = len(available_pillar_colors)
        for i, col in enumerate(available_pillar_colors):
            rect = pygame.Rect(WIDTH//2 - (num_colors*80)//2 + i*80, HEIGHT//2 - 30, 60, 60)
            pygame.draw.rect(screen, col, rect)
            if col == current_pillar_color:
                pygame.draw.rect(screen, BLACK, rect, 4) # highlight selected
            else:
                pygame.draw.rect(screen, BLACK, rect, 1)

    elif state == "PLAYING":
        # Vykreslení sloupů
        for pillar in pillars:
            pygame.draw.rect(screen, current_pillar_color, (pillar["x"], 0, pillar_width, pillar["top_height"]))
            pygame.draw.rect(screen, current_pillar_color, (pillar["x"], pillar["bottom_y"], pillar_width, HEIGHT - pillar["bottom_y"]))

        # Vykreslení kostky
        draw_cube_with_line()

        # Vykreslení skóre
        score_text = large_font.render(str(score), True, BLACK)
        screen.blit(score_text, (WIDTH//2 - score_text.get_width()//2, 50))
        
    elif state == "GAMEOVER":
        # Vykreslení sloupů
        for pillar in pillars:
            pygame.draw.rect(screen, current_pillar_color, (pillar["x"], 0, pillar_width, pillar["top_height"]))
            pygame.draw.rect(screen, current_pillar_color, (pillar["x"], pillar["bottom_y"], pillar_width, HEIGHT - pillar["bottom_y"]))

        # Vykreslení kostky
        draw_cube_with_line()

        # Uživatelské rozhraní konce hry
        text = large_font.render("GAME OVER", True, RED)
        screen.blit(text, (WIDTH//2 - text.get_width()//2, HEIGHT//3))
        
        text2 = font.render(f"Score: {score}  High Score: {high_score}", True, BLACK)
        screen.blit(text2, (WIDTH//2 - text2.get_width()//2, HEIGHT//2))
        
        text3 = font.render("Click or press Space to Restart", True, BLACK)
        screen.blit(text3, (WIDTH//2 - text3.get_width()//2, HEIGHT//2 + 50))
        
        text4 = font.render("Press ESC to Quit", True, BLACK)
        screen.blit(text4, (WIDTH//2 - text4.get_width()//2, HEIGHT//2 + 100))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
