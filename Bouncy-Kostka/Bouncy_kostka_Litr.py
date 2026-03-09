import pygame
import sys
import math

pygame.init()

# okno
WIDTH, HEIGHT = 1200, 900
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Litr Kostek")

# barvy
BLACK = (0,0,0)
RED = (255,0,0)
WHITE = (255,255,255)
YELLOW = (255,255,0)

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

# Font
font = pygame.font.SysFont("consolas",20)

clock = pygame.time.Clock()

running = True
while running:

    for event in pygame.event.get():

        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:

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
    pygame.draw.line(screen, WHITE, (cx, cy), (mx, my), 2)

    # Nakresleni naboju
    for b in bullets:
        pygame.draw.circle(screen, YELLOW, (int(b["x"]), int(b["y"])), 5)

    # Kordinace
    coords = font.render(f"X: {int(x)}  Y: {int(y)}", True, WHITE)
    screen.blit(coords, (10,10))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()