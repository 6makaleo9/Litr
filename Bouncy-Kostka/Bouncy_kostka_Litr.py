import pygame
import sys
import math

pygame.init()

# okno
WIDTH, HEIGHT = 1000, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Litr Kostek")

# barvy
BLACK = (0,0,0)
RED = (255,0,0)
BLUE = (0,0,255)
YELLOW = (255,255,0)
WHITE = (255,255,255)


# kostka
x = 100
y = 100
size = 40
vx = 4
vy = 4

# naboje
bullets = []
bullet_speed = 10
max_bounces = 1
max_bullets = 6
bullets_shot = 0
cooldown_time = 0
cooldown_duration = 3000  # 3 seconds in milliseconds

# Font
font = pygame.font.SysFont("consolas",20)
bullet_font = pygame.font.SysFont("consolas",60)

clock = pygame.time.Clock()

# kolco velikost
overlay_size = 250
overlay = pygame.Surface((overlay_size, overlay_size), pygame.SRCALPHA)
# kolco barva
pygame.draw.circle(overlay, (255, 255, 255, 128), (overlay_size//2, overlay_size//2), overlay_size//2)

running = True
while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if bullets_shot < max_bullets and cooldown_time == 0:
                    mx, my = pygame.mouse.get_pos()

                    cx = x + size/2
                    cy = y + size/2

                    dx = mx - cx
                    dy = my - cy
                    dist = math.hypot(dx, dy)

                    if dist != 0:
                        dx /= dist
                        dy /= dist

                    bullets.append({
                        "x": cx,
                        "y": cy,
                        "vx": dx * bullet_speed,
                        "vy": dy * bullet_speed,
                        "bounces": 0
                    })
                    
                    bullets_shot += 1
                    
                    if bullets_shot == max_bullets:
                        cooldown_time = pygame.time.get_ticks()

    # cooldown pro naboje
    if cooldown_time != 0:
        elapsed = pygame.time.get_ticks() - cooldown_time
        if elapsed >= cooldown_duration:
            cooldown_time = 0
            bullets = []
            bullets_shot = 0

    # pohyb kostky
    x += vx
    y += vy

    if x <= 0 or x >= WIDTH - size:
        vx = -vx
    if y <= 0 or y >= HEIGHT - size:
        vy = -vy

    # pocinani pohybu naboju
    for b in bullets[:]:

        b["x"] += b["vx"]
        b["y"] += b["vy"]

        bounced = False

        if b["x"] <= 0 or b["x"] >= WIDTH:
            b["vx"] = -b["vx"]
            bounced = True

        if b["y"] <= 0 or b["y"] >= HEIGHT:
            b["vy"] = -b["vy"]
            bounced = True

        if bounced:
            b["bounces"] += 1

        if b["bounces"] > max_bounces:
            bullets.remove(b)

    # Nakresleni pozadi
    screen.fill(BLACK)

    # Nakresleni Kostky
    pygame.draw.rect(screen, RED, (x, y, size, size))

    # Čara pistole
    mx, my = pygame.mouse.get_pos()
    cx = x + size/2
    cy = y + size/2
    pygame.draw.line(screen, WHITE, (cx, cy), (mx, my), 5)

    # Nakresleni naboju
    for b in bullets:
        pygame.draw.circle(screen, YELLOW, (int(b["x"]), int(b["y"])), 5)

    # Kordinace
    coords = font.render(f"X: {int(x)}  Y: {int(y)}", True, WHITE)
    screen.blit(coords, (10,10))

    # kolecko praveho rohu
    screen.blit(overlay, (WIDTH - overlay.get_width(), 0))
    
    # Nakresleni textu naboju a cooldownu
    circle_center_x = WIDTH - overlay_size // 2
    circle_center_y = overlay_size // 2
    
    bullet_text = bullet_font.render(f"{max_bullets - bullets_shot}/{max_bullets}", True, WHITE)
    text_rect = bullet_text.get_rect(center=(circle_center_x, circle_center_y - 15))
    screen.blit(bullet_text, text_rect)
    
    if cooldown_time != 0:
        elapsed = pygame.time.get_ticks() - cooldown_time
        remaining = (cooldown_duration - elapsed) / 1000.0
        if remaining > 0:
            cooldown_text = font.render(f"{remaining:.1f}s", True, RED)
            cooldown_rect = cooldown_text.get_rect(center=(circle_center_x, circle_center_y + 15))
            screen.blit(cooldown_text, cooldown_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()