import pygame
import sys
import math
import random

pygame.init()

# okno
WIDTH, HEIGHT = pygame.display.get_desktop_sizes()[0]
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Litr Kostek")

# barvy
BLACK = (0,0,0)
RED = (255,0,0)
BLUE = (0,0,255)
YELLOW = (255,255,0)
GREEN = (0,255,0)
WHITE = (255,255,255)
PURPLE = (128,0,128)
OLD_GOLD = (207,181,59)
VEGAS_GOLD = (197,179,88)


# kostka
x = 100
y = 100
size = 50
vx = 8
vy = 8

# sledujici kostka
follower_x = 1000
follower_y = 0
follower_speed = 2
follower_hp = 5
follower_max_hp = 5

# zeleni nepratele (velci)
big_enemies = [{'x': 500, 'y': 500, 'hp': 2}]
green_speed = 2
green_max_hp = 2
green_size = 50

# male zelene nepratele
small_enemies = []

# void effect pri smrti follower kostky
void_x = None
void_y = None
void_time = None
void_duration = 2000  # 2 sekundy v milisekundách
void_radius = 50
follower_void_created = False
paused = False
pause_start_time = None
cooldown_remaining_on_pause = None

# naboje
bullets = []
bullet_speed = 10
bullet_acceleration = 0.5  # kolik rychlosti naboj ziska kazdou sekundu (progresivne zrychlovani)
max_bullet_speed = 50  # max aby naboje nezacaly glitchovat nebo padat kvuli extremni rychlosti
max_bounces = 100
max_bullets = 6
bullets_shot = 0
cooldown_time = 0
cooldown_duration = 3000  # 3 sekundy v milisekundách

# Font
font = pygame.font.SysFont("consolas",20)
bullet_font = pygame.font.SysFont("consolas",60)
paused_font = pygame.font.SysFont("consolas", 126)
button_font = pygame.font.SysFont("consolas", 72)

# definice tlacitek
button_width = 450
button_height = 100
resume_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, 340, button_width, button_height)
quit_button_rect = pygame.Rect(WIDTH // 2 - button_width // 2, 460, button_width, button_height)

clock = pygame.time.Clock()

# kolco velikost
overlay_size = 250
overlay = pygame.Surface((overlay_size, overlay_size), pygame.SRCALPHA)
# kolco barva
pygame.draw.circle(overlay, (255, 255, 255, 100), (overlay_size//2, overlay_size//2), overlay_size//2)

# paused overlay
paused_overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
pygame.draw.rect(paused_overlay, (128, 128, 128, 128), (0, 0, WIDTH, HEIGHT))

running = True
while running:

    # delta cas (sekundy)
    dt = clock.tick(60) / 1000.0

    for event in pygame.event.get():


        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            paused = not paused
            now = pygame.time.get_ticks()
            if paused:
                pause_start_time = now
                if cooldown_time != 0:
                    cooldown_remaining_on_pause = max(0, cooldown_duration - (now - cooldown_time))
            else:
                if pause_start_time is not None:
                    pause_delta = now - pause_start_time
                    pause_start_time = None
                    if void_time is not None:
                        void_time += pause_delta
                if cooldown_remaining_on_pause is not None:
                    cooldown_time = now - (cooldown_duration - cooldown_remaining_on_pause)
                    cooldown_remaining_on_pause = None

        if not paused and event.type == pygame.MOUSEBUTTONDOWN:
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

                    gun_length = 80
                    bullet_x = cx + dx * gun_length
                    bullet_y = cy + dy * gun_length

                    bullets.append({
                        "x": bullet_x,
                        "y": bullet_y,
                        "vx": dx * bullet_speed,
                        "vy": dy * bullet_speed,
                        "bounces": 0
                    })
                    
                    bullets_shot += 1
                    
                    if bullets_shot == max_bullets:
                        cooldown_time = pygame.time.get_ticks()

        if paused and event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mx, my = pygame.mouse.get_pos()
                if resume_button_rect.collidepoint(mx, my):
                    paused = False
                    if pause_start_time is not None:
                        pause_delta = pygame.time.get_ticks() - pause_start_time
                        pause_start_time = None
                        if void_time is not None:
                            void_time += pause_delta
                        if cooldown_remaining_on_pause is not None:
                            cooldown_time = pygame.time.get_ticks() - (cooldown_duration - cooldown_remaining_on_pause)
                            cooldown_remaining_on_pause = None
                elif quit_button_rect.collidepoint(mx, my):
                    running = False

    if not paused:
        # cooldown pro naboje
        if cooldown_time != 0:
            elapsed = pygame.time.get_ticks() - cooldown_time
            if elapsed >= cooldown_duration:
                cooldown_time = 0
                bullets_shot = 0
                bullets_shot = 0

        # pohyb kostky
        x += vx
        y += vy

        if x <= 0 or x >= WIDTH - size:
            vx = -vx
        if y <= 0 or y >= HEIGHT - size:
            vy = -vy

        # pohyb sledujici kostky
        fx = x + size/2
        fy = y + size/2
        dfx = fx - follower_x - size/2
        dfy = fy - follower_y - size/2
        dist = math.hypot(dfx, dfy)
        
        if dist > 0:
            dfx /= dist
            dfy /= dist
            follower_x += dfx * follower_speed
            follower_y += dfy * follower_speed
        dist = math.hypot(dfx, dfy)
        
        if dist > 0:
            dfx /= dist
            dfy /= dist
            follower_x += dfx * follower_speed
            follower_y += dfy * follower_speed
        
        # pohyb velkych zelenych nepratel
        for b_enemy in big_enemies:
            if b_enemy['hp'] > 0:
                dfx = fx - b_enemy['x'] - green_size/2
                dfy = fy - b_enemy['y'] - green_size/2
                dist = math.hypot(dfx, dfy)
                
                if dist > 0:
                    dfx /= dist
                    dfy /= dist
                    b_enemy['x'] += dfx * green_speed
                    b_enemy['y'] += dfy * green_speed
        
        # pohyb malych zelenych nepratel
        for s in small_enemies:
            dfx = fx - s['x'] - s['size']/2
            dfy = fy - s['y'] - s['size']/2
            dist = math.hypot(dfx, dfy)
            
            if dist > 0:
                dfx /= dist
                dfy /= dist
                s['x'] += dfx * s['speed']
                s['y'] += dfy * s['speed']
        
        # kontrola smrti follower kostky
        if follower_hp <= 0 and not follower_void_created:
            void_x = follower_x + size/2
            void_y = follower_y + size/2
            void_time = pygame.time.get_ticks()
            follower_void_created = True
        
        # kontrola smrti velkych zelenych nepratel
        for b_enemy in big_enemies[:]:
            if b_enemy['hp'] <= 0:
                # rozdeleni na dva male nepratele
                small_enemies.append({
                    'x': b_enemy['x'] + green_size/4,
                    'y': b_enemy['y'],
                    'hp': 2,
                    'size': 25,
                    'speed': 4,
                    'color': GREEN
                })
                small_enemies.append({
                    'x': b_enemy['x'] - green_size/4,
                    'y': b_enemy['y'],
                    'hp': 2,
                    'size': 25,
                    'speed': 4,
                    'color': GREEN
                })
                big_enemies.remove(b_enemy)
        
        # kontrola konce void efektu
        if void_time is not None:
            elapsed = pygame.time.get_ticks() - void_time
            if elapsed >= void_duration:
                void_time = None
                void_x = None
                void_y = None

        # pocinani pohybu naboju
        for b in bullets[:]:

            # nabirani rychlosti naboje
            speed = math.hypot(b["vx"], b["vy"])
            if speed > 0:
                factor = 1 + bullet_acceleration * dt
                b["vx"] *= factor
                b["vy"] *= factor
                
                # max aby naboje nezacaly glitchovat nebo padat kvuli extremni rychlosti
                new_speed = math.hypot(b["vx"], b["vy"])
                if new_speed > max_bullet_speed:
                    b["vx"] = (b["vx"] / new_speed) * max_bullet_speed
                    b["vy"] = (b["vy"] / new_speed) * max_bullet_speed

            b["x"] += b["vx"]
            b["y"] += b["vy"]

            # kolize s follower kostkou
            if follower_hp > 0 and (follower_x < b["x"] < follower_x + size and 
                follower_y < b["y"] < follower_y + size):
                if b in bullets:
                    bullets.remove(b)
                    follower_hp -= 1
                continue
            
            # kolize se zelenym nepritelem (velkym)
            hit_big = False
            for b_enemy in big_enemies:
                if b_enemy['hp'] > 0 and (b_enemy['x'] < b["x"] < b_enemy['x'] + green_size and 
                    b_enemy['y'] < b["y"] < b_enemy['y'] + green_size):
                    if b in bullets:
                        bullets.remove(b)
                        b_enemy['hp'] -= 1
                    hit_big = True
                    break
            if hit_big:
                continue
            
            # kolize s malymi zelenymi neprateli
            for s in small_enemies[:]:
                if s['x'] < b["x"] < s['x'] + s['size'] and s['y'] < b["y"] < s['y'] + s['size']:
                    if b in bullets:
                        bullets.remove(b)
                        s['hp'] -= 1
                        if s['hp'] <= 0:
                            small_enemies.remove(s)
                            # kazdy kill maleho spawne jednoho velkeho na nahodne pozici
                            big_enemies.append({
                                'x': random.randint(0, WIDTH - green_size),
                                'y': random.randint(0, HEIGHT - green_size),
                                'hp': green_max_hp
                            })
                    break  # jeden naboj jeden nepritel
            
            # kolize s void efektem
            if void_time is not None and math.hypot(b["x"] - void_x, b["y"] - void_y) < void_radius:
                if b in bullets:
                    bullets.remove(b)
                continue

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
                if b in bullets:
                    bullets.remove(b)

    # Nakresleni pozadi
    screen.fill(BLACK)

    # Nakresleni Kostky
    pygame.draw.rect(screen, RED, (x, y, size, size))

    # Nakresleni sledujici kostky
    if follower_hp > 0:
        pygame.draw.rect(screen, BLUE, (follower_x, follower_y, size, size))
    
    # Nakresleni velkych zelenych nepratel
    for b_enemy in big_enemies:
        if b_enemy['hp'] > 0:
            pygame.draw.rect(screen, GREEN, (b_enemy['x'], b_enemy['y'], green_size, green_size))
    
    # Nakresleni malych zelenych nepratel
    for s in small_enemies:
        pygame.draw.rect(screen, s['color'], (s['x'], s['y'], s['size'], s['size']))
    
    # Nakresleni void efektu
    if void_time is not None:
        pygame.draw.circle(screen, PURPLE, (int(void_x), int(void_y)), void_radius, 3)

    # Čara pistole
    mx, my = pygame.mouse.get_pos()
    cx = x + size/2
    cy = y + size/2
    
    dx = mx - cx
    dy = my - cy
    dist = math.hypot(dx, dy)
    
    if dist != 0:
        dx /= dist
        dy /= dist
    
    gun_length = 80
    end_x = cx + dx * gun_length
    end_y = cy + dy * gun_length
    pygame.draw.line(screen, WHITE, (cx, cy), (end_x, end_y), 5)

    # Nakresleni naboju
    for b in bullets:
        pygame.draw.circle(screen, YELLOW, (int(b["x"]), int(b["y"])), 5)

    # Kordinace
    coords = font.render(f"X: {int(x)}  Y: {int(y)}", True, WHITE)
    screen.blit(coords, (10,10))

    # kolecko praveho rohu
    screen.blit(overlay, (WIDTH - overlay.get_width(), 0))
    
    # stred velkeho kruhu
    circle_center_x = WIDTH - overlay_size // 2
    circle_center_y = overlay_size // 2

    remaining_bullets = max_bullets - bullets_shot

    # vzdalenost malych kruhu od stredu
    radius = 70
    bullet_radius = 26.25

    # uhly pro 6 naboju rozlozenych kolem kruhu
    angles = [90, 150, 210, 270, 330, 30]

    for i in range(max_bullets):
        angle = math.radians(angles[i])

        bx = circle_center_x + math.cos(angle) * radius
        by = circle_center_y - math.sin(angle) * radius

        if i < remaining_bullets:
            pygame.draw.circle(screen, VEGAS_GOLD, (int(bx), int(by)), bullet_radius)

    # cooldown cislo uprostred
    if cooldown_time != 0:
        if cooldown_remaining_on_pause is not None:
            remaining = cooldown_remaining_on_pause / 1000.0
        else:
            elapsed = pygame.time.get_ticks() - cooldown_time
            remaining = (cooldown_duration - elapsed) / 1000.0

        if remaining > 0:
            cooldown_text = bullet_font.render(f"{remaining:.1f}", True, RED)
            cooldown_rect = cooldown_text.get_rect(center=(circle_center_x, circle_center_y))
            screen.blit(cooldown_text, cooldown_rect)

    if paused:
        screen.blit(paused_overlay, (0, 0))
        # nakresleni textu "PAUSED" uprostred obrazovky
        paused_text = paused_font.render("PAUSED", True, RED)
        paused_rect = paused_text.get_rect(center=(WIDTH // 2, 127))
        screen.blit(paused_text, paused_rect)
        # nakresleni tlacitek
        pygame.draw.rect(screen, (192, 192, 192), resume_button_rect)  # Brighter gray
        pygame.draw.rect(screen, (192, 192, 192), quit_button_rect)
        # nakresleni textu tlacitek
        resume_text = button_font.render("Resume", True, BLACK)
        quit_text = button_font.render("Quit", True, BLACK)
        resume_text_rect = resume_text.get_rect(center=resume_button_rect.center)
        quit_text_rect = quit_text.get_rect(center=quit_button_rect.center)
        screen.blit(resume_text, resume_text_rect)
        screen.blit(quit_text, quit_text_rect)

    pygame.display.flip()

pygame.quit()
sys.exit()