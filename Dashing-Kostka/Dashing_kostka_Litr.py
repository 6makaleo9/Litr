import pygame
import sys
import math

# Inicializace Pygame
pygame.init()

# Nastavení okna
WIDTH, HEIGHT = 1200, 800
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dashing Kostka")

# Barvy
BLACK = (0, 0, 0)
RED   = (255, 0, 0)
BLUE  = (0, 0, 255)
WHITE = (255, 255, 255)

# Vlastnosti kostky
cube_size = 50
cube_x = float(50)
cube_y = float(HEIGHT // 2 - cube_size // 2)

# Dash
DASH_SPEED    = 18
DASH_FRICTION = 0.82
vel_x = 0.0
vel_y = 0.0

# Slash – rychlý tah katany
# Záporný úhel = záď (před tasením), kladný = předek (ve směru pohledu)
# → čára se prohoupne od zádi DOPŘEDU, tedy ve směru pohledu kostky
SLASH_DURATION    = 10         # počet snímků animace
SLASH_START_ANGLE = -90.0      # začátek: čepel vzadu
SLASH_END_ANGLE   =  90.0      # konec:   čepel vpředu (ve směru pohledu)
slash_timer = 0

def ease_katana(t):
    """Agresivní ease-out: okamžitý start, mírné zpomalení na konci."""
    return 1.0 - (1.0 - t) ** 3

def rotate_point(px, py, angle_deg):
    """Otočit bod (px, py) kolem počátku o angle_deg stupňů."""
    r = math.radians(angle_deg)
    c, s = math.cos(r), math.sin(r)
    return px * c - py * s, px * s + py * c

clock = pygame.time.Clock()

# Pomocná plocha musí být dost velká na kostku + indikátory po otočení
SURF_SIZE   = cube_size * 5
SURF_CENTER = SURF_SIZE // 2

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        # Zrušení pomocí ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

        # Kliknutí → dash ve směru pohledu + spuštění slash animace
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            cx0 = cube_x + cube_size / 2
            cy0 = cube_y + cube_size / 2
            ddx = pygame.mouse.get_pos()[0] - cx0
            ddy = pygame.mouse.get_pos()[1] - cy0
            dist = math.hypot(ddx, ddy)
            if dist > 0:
                vel_x = (ddx / dist) * DASH_SPEED
                vel_y = (ddy / dist) * DASH_SPEED
            slash_timer = SLASH_DURATION

    # ── Pohyb kostky ──────────────────────────────────────────────────────────
    cube_x += vel_x
    cube_y += vel_y
    vel_x  *= DASH_FRICTION
    vel_y  *= DASH_FRICTION
    cube_x  = max(0, min(WIDTH  - cube_size, cube_x))
    cube_y  = max(0, min(HEIGHT - cube_size, cube_y))
    if abs(vel_x) < 0.1: vel_x = 0.0
    if abs(vel_y) < 0.1: vel_y = 0.0

    # ── Pohled na kurzor ──────────────────────────────────────────────────────
    cx = cube_x + cube_size / 2
    cy = cube_y + cube_size / 2
    mx, my = pygame.mouse.get_pos()
    # Negativní, protože pygame má y dolů (atan2 je CCW, rotate() je CCW)
    angle = -math.degrees(math.atan2(my - cy, mx - cx))

    # ── Stav slash animace ────────────────────────────────────────────────────
    is_slashing = slash_timer > 0
    if is_slashing:
        # raw_t jde od 0 (začátek) do 1 (konec animace)
        raw_t    = 1.0 - slash_timer / SLASH_DURATION
        progress = ease_katana(raw_t)
        slash_angle = SLASH_START_ANGLE + (SLASH_END_ANGLE - SLASH_START_ANGLE) * progress

        # Čepel se "tasí": roste od 0 na plnou délku v prvních ~2 snímcích
        DRAW_FRAC = 2.0 / SLASH_DURATION
        grow_frac = min(1.0, raw_t / DRAW_FRAC)
        slash_thick = 3
        slash_timer -= 1
    else:
        # Klidová poloha: čára leží vodorovně nahoře
        slash_angle = 0.0
        grow_frac   = 1.0
        slash_thick = 2

    # ── Krajní body čáry v lokálním prostoru kostky ───────────────────────────
    half_w      = cube_size * grow_frac   # roste od 0 → cube_size (= polovina 2× délky)
    top_y_local = -(cube_size / 2)        # horní hrana kostky v lokálním prostoru

    lp1x, lp1y = -half_w, top_y_local
    lp2x, lp2y =  half_w, top_y_local

    # Aplikovat slash rotaci v lokálním prostoru
    r1x, r1y = rotate_point(lp1x, lp1y, slash_angle)
    r2x, r2y = rotate_point(lp2x, lp2y, slash_angle)

    # ── Vykreslení ────────────────────────────────────────────────────────────
    screen.fill(BLACK)

    # Kostka a indikátory na pomocné průhledné ploše
    cube_surf = pygame.Surface((SURF_SIZE, SURF_SIZE), pygame.SRCALPHA)

    # Vykreslení samotné kostky
    pygame.draw.rect(cube_surf, BLUE, (
        SURF_CENTER - cube_size // 2,
        SURF_CENTER - cube_size // 2,
        cube_size, cube_size,
    ))

    # Indikátor směru – polovina čáry uvnitř kostky, polovina vyčnívá vpravo
    dir_len = 15
    dir_x_s = SURF_CENTER + cube_size // 2 - dir_len // 2
    pygame.draw.line(cube_surf, WHITE,
                     (dir_x_s, SURF_CENTER),
                     (dir_x_s + dir_len, SURF_CENTER), 2)

    # Slash / horní čára (otočená dle animace)
    p1s = (int(SURF_CENTER + r1x), int(SURF_CENTER + r1y))
    p2s = (int(SURF_CENTER + r2x), int(SURF_CENTER + r2y))
    pygame.draw.line(cube_surf, WHITE, p1s, p2s, slash_thick)

    # Otočit celou plochu ke kurzoru a vykreslit na střed kostky
    rotated_surf = pygame.transform.rotate(cube_surf, angle)
    rotated_rect = rotated_surf.get_rect(center=(int(cx), int(cy)))
    screen.blit(rotated_surf, rotated_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
