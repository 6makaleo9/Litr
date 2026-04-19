import pygame
import sys
import math

# Inicializace Pygame
pygame.init()

# Nastavení okna
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()
pygame.display.set_caption("Dashing Kostka")

# Barvy
BLACK        = (0,   0,   0)
RED          = (255, 0,   0)
BLUE         = (30,  90,  220)   # sytější modrá kostka
BLUE_DARK    = (15,  45,  130)   # tmavší okraj kostky
BLUE_LIGHT   = (90,  150, 255)   # světlý highlight kostky
WHITE        = (255, 255, 255)
BLADE_COLOR  = (210, 228, 255)   # lehce namodralá ocel čepele
GUARD_COLOR  = (185, 185, 205)   # stříbrná tsuba / hlavice
HANDLE_COLOR = (75,  42,  18)    # tmavě hnědá rukojeť (ovinouí)
ARROW_COLOR  = (255, 255, 160)   # žlutobílý indikátor směru

# Třída nepřátel
class Enemy:
    def __init__(self, x, y, type_name="skeleton", hp=10):
        self.x = x
        self.y = y
        self.type_name = type_name
        self.hp = hp
        self.max_hp = hp
        self.color = WHITE
        self.size = 45

ENEMY_SPEED = 1.0
SPOT_RADIUS = 500

# Vlastnosti kostky
cube_size = 50
cube_x = float(50)
cube_y = float(HEIGHT // 2 - cube_size // 2)

enemies = [
    Enemy(WIDTH // 2 + 200, HEIGHT // 2),
    Enemy(WIDTH // 2 + 200, HEIGHT // 2 - 100),
    Enemy(WIDTH // 2 + 200, HEIGHT // 2 + 100)
]

# Dash
DASH_SPEED    = 40
DASH_FRICTION = 0.82
vel_x = 0.0
vel_y = 0.0
is_charging = False
charge_start_ticks = 0
show_hitboxes = False

attack_damage = 1
enemies_hit_this_slash = set()

# Slash – celá katana se otáčí v zápěstí (kolem středu rukojeti)
# 0° = čepel za kostkou (-X), kladné úhly = oblouk nahoru přes hlavu dopředu
SLASH_DURATION    = 10          # počet snímků animace
SLASH_START_ANGLE =    0.0      # začátek: leží vodorovně na vrchu
SLASH_END_ANGLE   =  200.0      # konec:   čepel skončí přesně ve směru dopředu nad indikátorem
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

        # Přepínání zobrazení hitboxů pomocí "H"
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            show_hitboxes = not show_hitboxes

        # Stisknutí tlačítka zahájí nabíjení dashe
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_charging = True
            charge_start_ticks = pygame.time.get_ticks()

        # Pustění tlačítka uvolní dash a spustí animaci
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if is_charging:
                is_charging = False
                hold_time_ms = pygame.time.get_ticks() - charge_start_ticks
                hold_seconds = hold_time_ms / 1000.0
                
                # Nabití limitováno na 3 vteřiny (poměr od 0 do 1)
                charge_factor = min(1.0, hold_seconds / 3.0)
                
                # Rychlost od 1x (úplně nízko / 0 vteřin) do 2x (po 3 vteřinách)
                speed_multiplier = 1.0 + charge_factor
                final_dash_speed = DASH_SPEED * speed_multiplier
                
                cx0 = cube_x + cube_size / 2
                cy0 = cube_y + cube_size / 2
                mx, my = pygame.mouse.get_pos()
                ddx = mx - cx0
                ddy = my - cy0
                dist = math.hypot(ddx, ddy)
                if dist > 0:
                    vel_x = (ddx / dist) * final_dash_speed
                    vel_y = (ddy / dist) * final_dash_speed
                slash_timer = SLASH_DURATION

                # Inicializace kontinuální detekce zasažení pro tento útok
                attack_damage = 5 if charge_factor >= 1.0 else 1
                enemies_hit_this_slash.clear()

    # ── Pohyb kostky ──────────────────────────────────────────────────────────
    cube_x += vel_x
    cube_y += vel_y
    vel_x  *= DASH_FRICTION
    vel_y  *= DASH_FRICTION
    cube_x  = max(0, min(WIDTH  - cube_size, cube_x))
    cube_y  = max(0, min(HEIGHT - cube_size, cube_y))
    if abs(vel_x) < 0.1: vel_x = 0.0
    if abs(vel_y) < 0.1: vel_y = 0.0

    # ── Pohyb nepřátel (AI) ───────────────────────────────────────────────────
    cx = cube_x + cube_size / 2
    cy = cube_y + cube_size / 2
    for enemy in enemies:
        ecx = enemy.x + enemy.size / 2
        ecy = enemy.y + enemy.size / 2
        dist = math.hypot(cx - ecx, cy - ecy)
        
        if dist < SPOT_RADIUS and dist > 0:
            dx = (cx - ecx) / dist
            dy = (cy - ecy) / dist
            
            if enemy.hp <= 5:
                # Má 5 HP nebo méně -> utíká pomalu DOkud není mimo radius dohledu
                enemy.x -= dx * ENEMY_SPEED
                enemy.y -= dy * ENEMY_SPEED
            else:
                # Pronásleduje hráče
                if dist > (cube_size / 2 + enemy.size / 2 - 5): # Zabrání vstupu přesně do středu
                    enemy.x += dx * ENEMY_SPEED
                    enemy.y += dy * ENEMY_SPEED
                    
        # Udržování nepřítele v hrací ploše
        enemy.x = max(0, min(WIDTH - enemy.size, enemy.x))
        enemy.y = max(0, min(HEIGHT - enemy.size, enemy.y))

    # ── Pohled na kurzor ──────────────────────────────────────────────────────
    cx = cube_x + cube_size / 2
    cy = cube_y + cube_size / 2
    mx, my = pygame.mouse.get_pos()
    # Negativní, protože pygame má y dolů (atan2 je CCW, rotate() je CCW)
    angle = -math.degrees(math.atan2(my - cy, mx - cx))

    # ── Stav slash animace ────────────────────────────────────────────────────
    is_slashing = slash_timer > 0
    if is_slashing:
        raw_t    = 1.0 - slash_timer / SLASH_DURATION
        progress = ease_katana(raw_t)
        blade_pivot = SLASH_START_ANGLE + (SLASH_END_ANGLE - SLASH_START_ANGLE) * progress
        slash_timer -= 1
        
        # Kontinuální aplikace poškození po celou dobu trvání dashe/slashe (nedochází ke stackování na stejný cíl)
        c_half = cube_size / 2
        tip_dist = -10 - int(cube_size * 1.65)
        
        hitbox_poly = []
        w_px, w_py = rotate_point(c_half, -c_half, -angle)
        hitbox_poly.append((cx + w_px, cy + w_py)) # Zápěstí
        
        for p_angle in range(0, int(SLASH_END_ANGLE) + 5, 5):
            rx, ry = rotate_point(tip_dist - 25, 0, p_angle) # Posunuto o 25 (poloměr nepřítele)
            lx = rx + c_half
            ly = ry - c_half
            w_lx, w_ly = rotate_point(lx, ly, -angle)
            hitbox_poly.append((cx + w_lx, cy + w_ly))
            
        for enemy in enemies[:]:
            if enemy in enemies_hit_this_slash:
                continue
                
            ecx = enemy.x + enemy.size / 2
            ecy = enemy.y + enemy.size / 2
            
            inside = False
            n = len(hitbox_poly)
            p1x, p1y = hitbox_poly[0]
            for i in range(1, n + 1):
                p2x, p2y = hitbox_poly[i % n]
                if ecy > min(p1y, p2y) and ecy <= max(p1y, p2y) and ecx <= max(p1x, p2x):
                    if p1y != p2y:
                        xints = (ecy - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or ecx <= xints:
                            inside = not inside
                p1x, p1y = p2x, p2y
                
            if inside:
                enemy.hp -= attack_damage
                enemies_hit_this_slash.add(enemy)
                if enemy.hp <= 0:
                    enemies.remove(enemy)
    else:
        # Klidová poloha: čepel leží vodorovně vzadu
        blade_pivot = 0.0

    # ── Katana geometry (celá zbraň se otáčí kolem rukojeti) ────────────────────
    # +X = přední strana (look direction / indicator).
    # Při blade_pivot=0° čepel leží vodorovně vzadu (-X).
    HALF       = cube_size // 2
    TOP_Y      = -HALF
    HANDLE_LEN = 20
    BLADE_LEN  = int(cube_size * 1.65)
    BLADE_W    = 3
    GUARD_HW   = 10
    GUARD_HD   = 3

    # Základní poloha bez rotace
    pommel_x = HALF + 10
    guard_x  = pommel_x - HANDLE_LEN
    tip_x    = guard_x - BLADE_LEN

    # Bod otáčení (pivot) = zápěstí / střed rukojeti
    pivot_x = (pommel_x + guard_x) / 2.0
    pivot_y = TOP_Y

    def _transform(pts):
        res = []
        for x, y in pts:
            # Posun do lokálního počátku (k pivotu)
            lx = x - pivot_x
            ly = y - pivot_y
            # Rotace bodu kolem pivotu (zápěstí)
            rx, ry = rotate_point(lx, ly, blade_pivot)
            # Návrat pozice a posun do středu Surface
            res.append((int(SURF_CENTER + rx + pivot_x), int(SURF_CENTER + ry + pivot_y)))
        return res

    # Tvary v neotočeném stavu (vodorovně ležící zbraň)
    handle_local = [
        (pommel_x, TOP_Y - 2), (guard_x, TOP_Y - 2),
        (guard_x,  TOP_Y + 2), (pommel_x, TOP_Y + 2),
    ]
    guard_local = [
        (guard_x - GUARD_HD, TOP_Y),
        (guard_x,            TOP_Y - GUARD_HW),
        (guard_x + GUARD_HD, TOP_Y),
        (guard_x,            TOP_Y + GUARD_HW),
    ]
    blade_local = [
        (guard_x, TOP_Y + BLADE_W),
        (tip_x,   TOP_Y),
        (guard_x, TOP_Y - BLADE_W),
    ]

    # Aplikace rotací
    handle_surf    = _transform(handle_local)
    guard_surf_pts = _transform(guard_local)
    blade_surf     = _transform(blade_local)
    
    # Body pro vykreslení drobných detailů
    pommel_surf  = _transform([(pommel_x, TOP_Y)])[0]
    guard_c_surf = _transform([(guard_x, TOP_Y)])[0]
    tip_surf     = _transform([(tip_x, TOP_Y)])[0]

    # ── Indikátor směru: malý šipkový trojúhelník na pravé hraně kostky ──────────
    # Trojúhelník špičkou ven (vpravo v lokálním prostoru), PŘED slash rotací
    if is_charging:
        current_hold = (pygame.time.get_ticks() - charge_start_ticks) / 1000.0
        c_factor = min(1.0, current_hold / 3.0)
    else:
        c_factor = 0.0

    if c_factor >= 1.0:
        # Plné nabití: šipka vyskočí a zčervená
        ARROW_LEN  = 30
        ARROW_HALF = 12
        draw_arrow_color = RED
    else:
        # Nabíjení: plynulý růst
        ARROW_LEN  = 10 + int(10 * c_factor)
        ARROW_HALF = 5 + int(3 * c_factor)
        draw_arrow_color = ARROW_COLOR

    arrow_face_x = HALF                             # přilepeno na pravou hranu
    arrow_tip_local   = (arrow_face_x + ARROW_LEN,  0)
    arrow_base1_local = (arrow_face_x,               ARROW_HALF)
    arrow_base2_local = (arrow_face_x,              -ARROW_HALF)
    # Tento indikátor se NEOTÁČÍ se slashem – vždy ukazuje přísně doprava
    arrow_pts_surf = [
        (int(SURF_CENTER + arrow_tip_local[0]),   int(SURF_CENTER + arrow_tip_local[1])),
        (int(SURF_CENTER + arrow_base1_local[0]), int(SURF_CENTER + arrow_base1_local[1])),
        (int(SURF_CENTER + arrow_base2_local[0]), int(SURF_CENTER + arrow_base2_local[1])),
    ]

    # ── Vykreslení ────────────────────────────────────────────────────────────
    screen.fill(BLACK)

    # Vykreslení nepřátel
    for enemy in enemies:
        enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size)
        pygame.draw.rect(screen, enemy.color, enemy_rect)
        
        # Health bar nad nepřítelem
        bar_w = int(enemy.size * (enemy.hp / enemy.max_hp))
        pygame.draw.rect(screen, RED, (enemy.x, enemy.y - 12, enemy.size, 6))
        pygame.draw.rect(screen, (0, 255, 0), (enemy.x, enemy.y - 12, bar_w, 6))

    # Kostka a indikátory na pomocné průhledné ploše
    cube_surf = pygame.Surface((SURF_SIZE, SURF_SIZE), pygame.SRCALPHA)

    # ── Kostka: tmavý okraj + světlý highlight ────────────────────────────────
    cube_rect = pygame.Rect(
        SURF_CENTER - cube_size // 2,
        SURF_CENTER - cube_size // 2,
        cube_size, cube_size,
    )
    pygame.draw.rect(cube_surf, BLUE, cube_rect)
    # Horní + levý highlight (světlá hrana)
    pygame.draw.line(cube_surf, BLUE_LIGHT,
                     (cube_rect.left,  cube_rect.top),
                     (cube_rect.right - 1, cube_rect.top), 2)
    pygame.draw.line(cube_surf, BLUE_LIGHT,
                     (cube_rect.left,  cube_rect.top),
                     (cube_rect.left,  cube_rect.bottom - 1), 2)
    # Dolní + pravý tmavý okraj
    pygame.draw.line(cube_surf, BLUE_DARK,
                     (cube_rect.left,  cube_rect.bottom - 1),
                     (cube_rect.right - 1, cube_rect.bottom - 1), 2)
    pygame.draw.line(cube_surf, BLUE_DARK,
                     (cube_rect.right - 1, cube_rect.top),
                     (cube_rect.right - 1, cube_rect.bottom - 1), 2)

    # ── Indikátor směru (šipka, bez slash rotace) ─────────────────────────────
    pygame.draw.polygon(cube_surf, draw_arrow_color, arrow_pts_surf)

    # ── Katana: rukojeť → garda → čepel ───────────────────────────────────────────
    # 1. Rukojeť (tsuka) – tmavě hnědý grip
    pygame.draw.polygon(cube_surf, HANDLE_COLOR, handle_surf)
    # 2. Hlavice (pommel) – malý kruh na konci rukojeti
    pygame.draw.circle(cube_surf, GUARD_COLOR, pommel_surf, 4)
    # 3. Garda (tsuba) – stříbrý kosotverec
    pygame.draw.polygon(cube_surf, GUARD_COLOR, guard_surf_pts)
    # 4. Čepel – zhužující se trojúhelník
    pygame.draw.polygon(cube_surf, BLADE_COLOR, blade_surf)
    # 5. Bláskový lesk: tenká bílá čára po středu čepele (boční léza)
    pygame.draw.line(cube_surf, WHITE, guard_c_surf, tip_surf, 1)

    # Otočit celou plochu ke kurzoru a vykreslit na střed kostky
    rotated_surf = pygame.transform.rotate(cube_surf, angle)
    rotated_rect = rotated_surf.get_rect(center=(int(cx), int(cy)))
    screen.blit(rotated_surf, rotated_rect)

    # ── Vykreslení Hitboxů (pokud je zapnuto) ─────────────────────────────────
    if show_hitboxes:
        hitbox_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Vykreslení dokonalého polygonu, který ukazuje přesný rozsah katany
        c_half = cube_size / 2
        tip_dist = -10 - int(cube_size * 1.65)
        
        draw_poly = []
        w_px, w_py = rotate_point(c_half, -c_half, -angle)
        draw_poly.append((cx + w_px, cy + w_py)) # Zápěstí
        
        for p_angle in range(0, int(SLASH_END_ANGLE) + 5, 5):
            rx, ry = rotate_point(tip_dist, 0, p_angle) 
            lx = rx + c_half
            ly = ry - c_half
            w_lx, w_ly = rotate_point(lx, ly, -angle)
            draw_poly.append((cx + w_lx, cy + w_ly))
            
        pygame.draw.polygon(hitbox_surf, (255, 0, 0, 40), draw_poly) # Poloprůhledná výplň čepele
        pygame.draw.polygon(hitbox_surf, RED, draw_poly, 2)          # Červený okraj přesně podle dráhy
        
        # Znázornění středu a okraje nepřátel
        for enemy in enemies:
            ecx = enemy.x + enemy.size / 2
            ecy = enemy.y + enemy.size / 2
            pygame.draw.circle(hitbox_surf, (0, 255, 0, 150), (int(ecx), int(ecy)), 4)
            
        # Znázornění zápěstí hráče
        pygame.draw.circle(hitbox_surf, (0, 255, 255, 150), (int(cx + w_px), int(cy + w_py)), 4)
            
        # Znázornění dohledu nepřátel (Agro radius)
        pygame.draw.circle(hitbox_surf, (255, 255, 0, 70), (int(cx), int(cy)), SPOT_RADIUS, 1)
            
        screen.blit(hitbox_surf, (0, 0))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
