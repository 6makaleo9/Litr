import pygame
import sys
import math
import random
import json
import os

# Spustí pygame knihovnu
pygame.init()

# Vytvoří okno na celou obrazovku
screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
WIDTH, HEIGHT = screen.get_size()  # Rozměr okna
pygame.display.set_caption("Dashing Kostka")

# Barvy 
BLACK        = (0,   0,   0)     
RED          = (255, 0,   0)
BLUE         = (30,  90,  220)   # sytější modrá kostka
BLUE_DARK    = (15,  45,  130)   # tmavší okraj kostky
BLUE_LIGHT   = (90,  150, 255)   # světlý highlight kostky
WHITE        = (255, 255, 255)
BLADE_COLOR  = (210, 228, 255)   # lehce namodralá ocel čepele
GUARD_COLOR  = (185, 185, 205)   # stříbrná hlavice
HANDLE_COLOR = (75,  42,  18)    # tmavě hnědá rukojeť
ARROW_COLOR  = (255, 255, 160)   # žlutobílý indikátor směru
GOBLIN_GREEN = (25,  90,  25)    # tmavě zelená pro gobliny

# Barvy pro Bránu (Dungeon Door)
DOOR_WOOD      = (65, 35, 15)    # Tmavé dřevo
DOOR_IRON      = (45, 45, 50)    # Železné kování
DOOR_LIGHT     = (255, 210, 100) # Zlaté světlo zevnitř
GATE_FRAME     = (40, 40, 45)    # Kamenný rám
GATE_CYAN      = (200, 200, 210) # Prach/Debris

# Třída nepřátel - co je nepřítel?
class Enemy:
    def __init__(self, x, y, type_name="skeleton"):
        self.x = x  # Pozice X
        self.y = y  # Pozice Y
        self.type_name = type_name  # Jaký typ nepřítele
        
        if type_name == "goblin":
            self.hp = 7
            self.color = GOBLIN_GREEN
            self.size = 35
        else:
            self.hp = 10
            self.color = WHITE
            self.size = 45
            
        self.max_hp = self.hp  # Maximální zdraví (pro zdravotní lištu)

# Jak rychle se nepřítel pohybuje
ENEMY_SPEED = 1.0
# Jak daleko vidí nepřítel (radius dohledu v pixelech)
SPOT_RADIUS = 500

# ─── EFEKT PRASKÁNÍ SKELETU ────────────────────────────────
# Definuje předem vyrobené trhliny pro každou fázi poškození (0 = žádné, 4 = max).
# Každá trhlina je seznam úseček [(x1,y1,x2,y2), ...] v normalizovaných souřadnicích (0.0–1.0).
_CRACK_STAGES = [
    # Stupeň 1 - jedna trhlina shora dolů
    [
        (0.50, 0.00, 0.52, 0.45),
        (0.52, 0.45, 0.48, 0.80),
    ],
    # Stupeň 2 - dvě trhliny ze shora
    [
        (0.50, 0.00, 0.52, 0.45),
        (0.52, 0.45, 0.48, 0.80),
        (0.52, 0.45, 0.70, 0.75),
    ],
    # Stupeň 3 - tři větve shora dolů
    [
        (0.50, 0.00, 0.53, 0.40),
        (0.53, 0.40, 0.46, 0.80),
        (0.53, 0.40, 0.72, 0.78),
        (0.30, 0.00, 0.35, 0.35),
        (0.35, 0.35, 0.28, 0.70),
    ],
    # Stupeň 4 - mnoho trhlin shora až na dno
    [
        (0.50, 0.00, 0.53, 0.38),
        (0.53, 0.38, 0.44, 0.75),
        (0.44, 0.75, 0.48, 1.00),
        (0.53, 0.38, 0.74, 0.72),
        (0.74, 0.72, 0.78, 1.00),
        (0.30, 0.00, 0.34, 0.32),
        (0.34, 0.32, 0.25, 0.68),
        (0.25, 0.68, 0.22, 1.00),
        (0.34, 0.32, 0.50, 0.60),
        (0.70, 0.00, 0.68, 0.38),
        (0.68, 0.38, 0.76, 0.70),
    ],
]

def draw_cracks(surface, rx, ry, rsize, hp_ratio):
    """Nakresli trhliny na skeleton podle zbývajícího HP (0.0=mrtvý, 1.0=plné HP)."""
    if hp_ratio >= 1.0:
        return  # Žádné poškození - žádné trhliny
    damage_ratio = 1.0 - hp_ratio  # 0=čerstvý, 1=zničený
    # Vyber stupeň trhlin (0-3)
    stage_idx = min(3, int(damage_ratio * 4))
    lines = _CRACK_STAGES[stage_idx]
    # Temně šedá barva trhlin + tmavší obrys
    crack_color  = (30, 30, 30)
    shadow_color = (0, 0, 0)
    for x1n, y1n, x2n, y2n in lines:
        x1 = int(rx + x1n * rsize)
        y1 = int(ry + y1n * rsize)
        x2 = int(rx + x2n * rsize)
        y2 = int(ry + y2n * rsize)
        pygame.draw.line(surface, shadow_color, (x1+1, y1+1), (x2+1, y2+1), 3)
        pygame.draw.line(surface, crack_color,  (x1,   y1  ), (x2,   y2  ), 2)
# ─────────────────────────────────────────────────────────────────────────────

# Vlastnosti kostky - hráčův modrý čtverec
cube_size = 50  # Velikost kostky
cube_x = float(50)  # Pozice kostky X (vlevo, na start)
cube_y = float(HEIGHT // 2 - cube_size // 2)  # Pozice kostky Y (uprostřed obrazovky)
START_X = cube_x  # Zapamatuj si startovní pozici X
START_Y = cube_y  # Zapamatuj si startovní pozici Y

# Respawn checkpoint - zelená krabička vpravo pro konec levelu
RESPAWN_WIDTH = 40  # Šířka zelené kostky
RESPAWN_HEIGHT = 200  # Výška zelené kostky
respawn_x = WIDTH - RESPAWN_WIDTH  # Pozice vpravo
respawn_y = HEIGHT // 2 - RESPAWN_HEIGHT // 2  # Uprostřed obrazovky
RESPAWN_COLOR = (100, 200, 100)  # Zelená barva

# Kde se nepřátelé poprvé objeví
def get_level_enemies(level):
    """Vrátí seznam nepřátel pro daný level"""
    # Pozice jsou pro teď stejné
    positions = [
        (WIDTH // 2 + 200, HEIGHT // 2),
        (WIDTH // 2 + 200, HEIGHT // 2 - 100),
        (WIDTH // 2 + 200, HEIGHT // 2 + 100)
    ]
    
    # První level (0) = skeletoni, Druhý level (1) = goblini
    if level == 1:
        return [Enemy(x, y, "goblin") for x, y in positions]
    else:
        # Ostatní levely (nebo liché) zatím skeletoni, nebo můžeme střídat
        etype = "skeleton" if level % 2 == 0 else "goblin"
        return [Enemy(x, y, etype) for x, y in positions]


# Dash - rychlý pohyb hráče
DASH_SPEED    = 40  # Jak rychle se kostka pohybuje
DASH_FRICTION = 0.82  # Jak rychle zpomaluje (0.82 = zastaví se pomalu)
vel_x = 0.0  # Aktuální rychlost X
vel_y = 0.0  # Aktuální rychlost Y
is_charging = False  # Nabíjí se teď dash?
charge_start_ticks = 0  # Kdy začalo nabíjení?
show_hitboxes = False  # Zobrazit hitboxy? (H klávesa)

# Animace Brány
gate_anim_timer = 0.0
gate_opening_scale = 0.0
gate_particles = []
shake_intensity = 0.0

# ─── ZDRAVÍ HRÁČE ────────────────────────────────────────────────────────────
PLAYER_MAX_HP      = 5    # Maximální počet životů
player_hp          = PLAYER_MAX_HP  # Aktuální životy
PLAYER_INVINCIBLE_FRAMES = 90  # Počet snímků nezranitelnosti po zásahu (~1.5 s)
player_invincible  = 0    # Zbývající snímky nezranitelnosti (0 = zranitelný)
PLAYER_DAMAGE      = 1    # Zranění způsobené nepřítelem při dotyku

# Počitadlo Dokončených levelů
# ─── ULOŽENÁ HRA ──────────────────────────────────────────────────────────────
SAVE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "savegame.json")

def save_game(level):
    """Uloží postup hry do souboru"""
    with open(SAVE_FILE, "w") as f:
        json.dump({"level_completed": level}, f)

def load_game():
    """Načte uložený postup hry, nebo vrátí 0 pokud soubor neexistuje"""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r") as f:
                data = json.load(f)
                return int(data.get("level_completed", 0))
        except (json.JSONDecodeError, KeyError, ValueError):
            return 0
    return 0

level_completed = load_game()  # Načti uložený postup

# Vytvoř seznam nepřátel na mapě (podle aktuálního levelu)
enemies = get_level_enemies(level_completed)
font        = pygame.font.SysFont(None, 48)

# ─── HERNÍ STAV ──────────────────────────────────────────────────────────────
# Hra může být v menu nebo ve hře
GAME_STATE_MENU     = "menu"
GAME_STATE_PLAYING  = "playing"
GAME_STATE_SETTINGS = "settings"
GAME_STATE_PAUSED   = "paused"
game_state = GAME_STATE_MENU  # Začínáme v menu

# ─── FONTY PRO MENU ──────────────────────────────────────────────────────────
font_title    = pygame.font.SysFont('impact', 120)  # Velký název hry
font_subtitle = pygame.font.SysFont(None, 42)   # Podtitulek
font_controls = pygame.font.SysFont(None, 32)   # Ovládání
font_button   = pygame.font.SysFont(None, 52)   # Text tlačítka

# ─── ANIMACE TLAČÍTKA PLAY ───────────────────────────────────────────────────
btn_hover       = False   # Je myš nad tlačítkem?
btn_hover_scale = 1.0     # Aktuální velikost tlačítka (animace)
btn_pulse_t     = 0.0     # Čítač pro pulzování tlačítka


# Útok - zranění
attack_damage = 1  # Kolik bodů zranění způsobí útok
enemies_hit_this_slash = set()  # Jaké nepřátele jsme už v tomhle útoku zasáhli?

# Slash - animace máchnutí katany
SLASH_DURATION    = 10          # Jak dlouho trvá animace (10 snímků)
SLASH_START_ANGLE =    0.0      # Začátek: čepel leží vzadu
SLASH_END_ANGLE   =  200.0      # Konec: čepel je nahoře
slash_timer = 0  # Kolik snímků zbývá do konce animace?

# Funkce - jak rychle se katana otáčí (hladký pohyb)
def ease_katana(t):
    """Začne rychle, zpomalí se na konci"""
    return 1.0 - (1.0 - t) ** 3

# Funkce - otočit bod ve 2D (pro rotaci zbraně)
def rotate_point(px, py, angle_deg):
    """Otočí bod (px, py) o angle_deg stupňů"""
    r = math.radians(angle_deg)  # Převod stupňů na radiány
    c, s = math.cos(r), math.sin(r)  # Cos a sin pro rotaci
    return px * c - py * s, px * s + py * c  # Rotovaný bod

# Hodiny - aby se hra měla fixní počet snímků za vteřinu (FPS)
clock = pygame.time.Clock()

# Pomocná průhledná plocha - zde si nakreslíme kostku a katanu
SURF_SIZE   = cube_size * 5  # Velikost plochy
SURF_CENTER = SURF_SIZE // 2  # Střed plochy

# ─── SYSTÉM POZADÍ ───────────────────────────────────────────────────────────

# Kamenná dlažba - nakreslí se jen jednou do bg_surf pro rychlost
TILE      = 64           # Velikost jedné dlaždice v pixelech
TILE_BASE = (22, 22, 28) # Základní tmavě modrošedá barva kamene
TILE_VAR  = 8            # O kolik se barva každé dlaždice náhodně liší
GROUT     = (10, 10, 14) # Barva spáry mezi dlaždicemi

bg_surf = pygame.Surface((WIDTH, HEIGHT))  # Plocha na celou obrazovku
bg_surf.fill(GROUT)                        # Vyplň vše barvou spáry
rng = random.Random(42)  # Seeded generátor - dlaždice jsou vždy stejné
for ty in range(0, HEIGHT, TILE):          # Procházej řádky dlaždic
    for tx in range(0, WIDTH, TILE):       # Procházej sloupce dlaždic
        v = rng.randint(-TILE_VAR, TILE_VAR)             # Náhodná odchylka barvy
        col = (TILE_BASE[0]+v, TILE_BASE[1]+v, TILE_BASE[2]+v)  # Výsledná barva
        col = tuple(max(0, min(255, c)) for c in col)    # Ořízni na 0-255
        # Nakresli vnitřek dlaždice (1px spára kolem dokola)
        pygame.draw.rect(bg_surf, col, (tx+1, ty+1, TILE-2, TILE-2))
        # Světlejší linka vlevo nahoře - simuluje dopad světla
        hi = tuple(min(255, c+18) for c in col)
        pygame.draw.line(bg_surf, hi, (tx+1, ty+1), (tx+TILE-2, ty+1))
        pygame.draw.line(bg_surf, hi, (tx+1, ty+1), (tx+1, ty+TILE-2))
        # Tmavší linka vpravo dole - simuluje stín
        sh = tuple(max(0, c-14) for c in col)
        pygame.draw.line(bg_surf, sh, (tx+1, ty+TILE-2), (tx+TILE-2, ty+TILE-2))
        pygame.draw.line(bg_surf, sh, (tx+TILE-2, ty+1),  (tx+TILE-2, ty+TILE-2))

# Vinětace - tmavý okraj obrazovky, střed je světlejší
# Nakreslí se jednou do průhledné plochy, pak se přikládá každý snímek
vignette_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
cx_v = WIDTH  // 2  # Střed obrazovky X
cy_v = HEIGHT // 2  # Střed obrazovky Y
# Vykreslíme 80 vrstev elips od středu ven - každá vrstva je tmavší
vignette_surf.fill((0, 0, 0, 0))  # Začni s prázdnou (průhlednou) plochou
for step in range(80):
    ratio = (80 - step) / 80       # 1 = okraj (tmavé), 0 = střed (světlé)
    alpha = int(210 * ratio ** 2.5)  # Kvadratický nárůst tmy ke kraji
    ew    = int(WIDTH  * (step / 80 * 0.95 + 0.05))  # Šířka elipsy
    eh    = int(HEIGHT * (step / 80 * 0.95 + 0.05))  # Výška elipsy
    s     = pygame.Surface((ew, eh), pygame.SRCALPHA)  # Dočasná plocha
    pygame.draw.ellipse(s, (0, 0, 0, alpha), (0, 0, ew, eh))  # Černá elipsa
    # Přilož elipsu na střed vinětace (BLEND_RGBA_MAX = vezmi nejtmavší)
    vignette_surf.blit(s, (cx_v - ew//2, cy_v - eh//2), special_flags=pygame.BLEND_RGBA_MAX)



# Prachové částice - malé světlé tečky pomalu plavající po místnosti
NUM_DUST = 500  # Kolik částic najednou létá v místnosti
class DustParticle:
    def __init__(self, rand=None):
        r = rand or random
        self.x     = r.uniform(0, WIDTH)    # Náhodná počáteční pozice X
        self.y     = r.uniform(0, HEIGHT)   # Náhodná počáteční pozice Y
        self.size  = r.uniform(1.0, 2.5)    # Velikost tečky (1-2.5 px)
        self.speed = r.uniform(0.08, 0.35)  # Rychlost pohybu
        self.angle = r.uniform(0, 360)      # Směr pohybu (stupně)
        self.drift = r.uniform(-0.3, 0.3)   # Jak moc se směr pomalu otáčí
        self.alpha = r.randint(30, 90)      # Průhlednost (30=skoro nevidět)
        self.fade  = r.choice([-1, 1]) * r.uniform(0.2, 0.6)  # Zda mizí nebo se objevuje

    def update(self):
        rad        = math.radians(self.angle)       # Převod stupňů na radiány
        self.x    += math.cos(rad) * self.speed     # Pohyb ve směru X
        self.y    += math.sin(rad) * self.speed     # Pohyb ve směru Y
        self.angle += self.drift                    # Pomalu měníme směr
        self.alpha = max(20, min(100, self.alpha + self.fade))  # Průhlednost 20-100
        if self.alpha in (20, 100):                 # Na krajích otočí fade
            self.fade = -self.fade
        # Pokud vyletí z obrazovky, vynoří se na druhé straně
        if self.x < -5:       self.x = WIDTH  + 5
        if self.x > WIDTH+5:  self.x = -5
        if self.y < -5:       self.y = HEIGHT + 5
        if self.y > HEIGHT+5: self.y = -5

dust_rng       = random.Random(7)  # Vlastní generátor - konzistentní rozmístění
dust_particles = [DustParticle(dust_rng) for _ in range(NUM_DUST)]  # Vytvoř všechny částice
dust_surf      = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)   # Průhledná plocha pro kreslení

# Částice pro Bránu (Prach a úlomky)
class GateParticle:
    def __init__(self, x, y):
        self.x = x + random.uniform(-RESPAWN_WIDTH//2, RESPAWN_WIDTH//2)
        self.y = y + random.uniform(-10, 10)
        self.vx = random.uniform(-0.5, 0.5)
        self.vy = random.uniform(0.5, 2.0) # Padá dolů
        self.life = 1.0
        self.size = random.uniform(1, 3)
        self.color = random.choice([GATE_CYAN, (100, 100, 110), (150, 130, 110)])

    def update(self, speed_mult=1.0):
        self.x += self.vx * speed_mult
        self.y += self.vy * speed_mult
        self.life -= 0.01 * speed_mult
        return self.life > 0

    def draw(self, surface):
        alpha = int(200 * self.life)
        s = pygame.Surface((int(self.size*2), int(self.size*2)), pygame.SRCALPHA)
        pygame.draw.circle(s, (*self.color, alpha), (int(self.size), int(self.size)), self.size)
        surface.blit(s, (int(self.x - self.size), int(self.y - self.size)))
# ─────────────────────────────────────────────────────────────────────────────

# Hlavní herní smyčka - běží, dokud hra neběží
running = True
while running:
    # Kontroluj co dělá hráč (klávesnice, myš, zavření okna)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False  # Zavření okna = konec hry

        # Klávesa ESC = pauza z hry
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            if game_state == GAME_STATE_PLAYING:
                game_state = GAME_STATE_PAUSED  # Zapauzovat hru
            elif game_state == GAME_STATE_PAUSED:
                game_state = GAME_STATE_PLAYING  # Pokračovat v hře

        # ─── MENU VSTUPY ──────────────────────────────────────────────────────
        if game_state == GAME_STATE_MENU:
            # Enter nebo Space = spustit hru
            if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_SPACE):
                game_state = GAME_STATE_PLAYING
            # Klik myší - zkontroluj jestli klikl na Resume tlačítko
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx_btn, my_btn = pygame.mouse.get_pos()
                # Souřadnice tlačítka Resume (zarovnáno vlevo s textem)
                btn_w, btn_h = 300, 60
                btn_x = 40
                btn_y = (HEIGHT // 2) - (btn_h // 2)
                resume_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                if resume_btn_rect.collidepoint(mx_btn, my_btn):
                    game_state = GAME_STATE_PLAYING
                
                # Tlačítko New Game - resetuje hru a uloží nulu
                new_game_y = btn_y + btn_h + 20
                new_game_btn_rect = pygame.Rect(btn_x, new_game_y, btn_w, btn_h)
                if new_game_btn_rect.collidepoint(mx_btn, my_btn):
                    # Resetuj veškerý stav hry
                    level_completed = 0
                    save_game(level_completed)
                    cube_x = float(START_X)
                    cube_y = float(START_Y)
                    vel_x = 0.0
                    vel_y = 0.0
                    enemies = get_level_enemies(level_completed)
                    slash_timer = 0
                    enemies_hit_this_slash.clear()
                    player_hp = PLAYER_MAX_HP          # Obnov zdraví hráče
                    player_invincible = 0              # Zruš nezranitelnost
                    game_state = GAME_STATE_PLAYING

                # Tlačítko Settings
                settings_y = new_game_y + btn_h + 20
                settings_btn_rect = pygame.Rect(btn_x, settings_y, btn_w, btn_h)
                if settings_btn_rect.collidepoint(mx_btn, my_btn):
                    game_state = GAME_STATE_SETTINGS

                # Tlačítko Quit
                quit_y = settings_y + btn_h + 20
                quit_btn_rect = pygame.Rect(btn_x, quit_y, btn_w, btn_h)
                if quit_btn_rect.collidepoint(mx_btn, my_btn):
                    running = False
            continue  # Přeskoč zbytek event smyčky pokud jsme v menu

        # ─── SETTINGS VSTUPY ──────────────────────────────────────────────────
        if game_state == GAME_STATE_SETTINGS:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                game_state = GAME_STATE_MENU
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                game_state = GAME_STATE_MENU  # Kliknutí kamkoliv vrací zpět
            continue

        # ─── PAUSE MENU VSTUPY ────────────────────────────────────────────────
        if game_state == GAME_STATE_PAUSED:
            # Klik myší - zkontroluj jestli klikl na Resume tlačítko
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx_btn, my_btn = pygame.mouse.get_pos()
                # Souřadnice panelu (musí odpovídat renderovacímu kódu)
                p_w, p_h = 600, 400
                p_rect = pygame.Rect(WIDTH // 2 - p_w // 2, HEIGHT // 2 - p_h // 2, p_w, p_h)
                
                # Souřadnice tlačítka Resume
                btn_w, btn_h = 250, 50
                btn_x = p_rect.centerx - btn_w // 2
                btn_y = p_rect.centery - 40
                resume_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
                if resume_btn_rect.collidepoint(mx_btn, my_btn):
                    game_state = GAME_STATE_PLAYING
                
                # Tlačítko Back to Main Menu
                back_y = btn_y + btn_h + 20
                back_btn_rect = pygame.Rect(btn_x, back_y, btn_w, btn_h)
                if back_btn_rect.collidepoint(mx_btn, my_btn):
                    game_state = GAME_STATE_MENU
            continue

        # ─── HERNÍ VSTUPY ─────────────────────────────────────────────────────
        # Klávesa H = zapni/vypni zobrazení hitboxů (pro debug)
        if event.type == pygame.KEYDOWN and event.key == pygame.K_h:
            show_hitboxes = not show_hitboxes

        # Klik myší = začít nabíjení dashe
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            is_charging = True  # Zahájit nabíjení
            charge_start_ticks = pygame.time.get_ticks()  # Zapamatuj si čas

        # Puštění myši = vypusť dash
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if is_charging:  # Bylo nabíjení?
                is_charging = False  # Nabíjení konec
                hold_time_ms = pygame.time.get_ticks() - charge_start_ticks  # Jak dlouho jsme drželi?
                hold_seconds = hold_time_ms / 1000.0  # Převedi na vteřiny
                
                # Kolik je nabito? (0 = nic, 1 = plně nabito po 3 sekundách)
                charge_factor = min(1.0, hold_seconds / 3.0)
                
                # Čím více nabito, tím rychlejší dash (1x až 2x)
                speed_multiplier = 1.0 + charge_factor
                final_dash_speed = DASH_SPEED * speed_multiplier  # Finální rychlost
                
                # Střed kostky
                cx0 = cube_x + cube_size / 2
                cy0 = cube_y + cube_size / 2
                mx, my = pygame.mouse.get_pos()  # Pozice myši
                ddx = mx - cx0  # Rozdíl X
                ddy = my - cy0  # Rozdíl Y
                dist = math.hypot(ddx, ddy)  # Vzdálenost ke kurzoru
                if dist > 0:  # Pokud se myš pohybuje
                    # Vypočítej směr a nastav rychlost
                    vel_x = (ddx / dist) * final_dash_speed
                    vel_y = (ddy / dist) * final_dash_speed
                slash_timer = SLASH_DURATION  # Spusť animaci katany

                # Pokud je plně nabito, způsobí více zranění
                attack_damage = 5 if charge_factor >= 1.0 else 1
                enemies_hit_this_slash.clear()  # Vyčisti seznam zasažených nepřátel

    # ─── VYKRESLENÍ MENU ──────────────────────────────────────────────────────
    if game_state == GAME_STATE_MENU:
        # Pozadí (dlažba + prach + vinětace) - pravá strana viditelná
        screen.blit(bg_surf, (0, 0))
        dust_surf.fill((0, 0, 0, 0))
        for dp in dust_particles:
            dp.update()
            r = max(1, int(dp.size))
            pygame.draw.circle(dust_surf, (200, 210, 230, int(dp.alpha)),
                               (int(dp.x), int(dp.y)), r)
        screen.blit(dust_surf, (0, 0))
        screen.blit(vignette_surf, (0, 0))

        # Černý čtverec přes celou levou polovinu obrazovky
        panel_w = WIDTH // 2
        pygame.draw.rect(screen, BLACK, (0, 0, panel_w, HEIGHT))

        # Černý pravoúhlý trojúhelník překrývající horní část pravé strany
        # Pravý úhel je v bodě (WIDTH//2, 0) - levý horní roh pravé poloviny
        # Jedna strana jde vpravo podél horní hrany, druhá dolů podél středu
        pygame.draw.polygon(screen, BLACK, [
            (panel_w,  0),       # 90° roh - levý horní roh pravé poloviny
            (WIDTH,    0),       # pravý horní roh obrazovky
            (panel_w,  HEIGHT),  # levý dolní roh pravé poloviny
        ])

        # Text názvu hry na levé straně
        title_surf = font_title.render("DASHING KOSTKA", True, WHITE)
        screen.blit(title_surf, (40, 40))

        # Poloha myši pro hover efekty tlačítek
        mx_hover, my_hover = pygame.mouse.get_pos()

        # Tlačítko Resume Game - zarovnáno vlevo s názvem
        resume_text = font_button.render("Resume Game", True, WHITE)
        btn_w, btn_h = 300, 60
        btn_x = 40
        btn_y = (HEIGHT // 2) - (btn_h // 2)
        resume_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        
        if resume_btn_rect.collidepoint(mx_hover, my_hover):  # Pozadí a okraj jen při hoveru
            pygame.draw.rect(screen, (20, 20, 20), resume_btn_rect)
            pygame.draw.rect(screen, (70, 70, 70), resume_btn_rect, 2)
        screen.blit(resume_text, (resume_btn_rect.centerx - resume_text.get_width() // 2,
                                  resume_btn_rect.centery - resume_text.get_height() // 2))

        # Tlačítko New Game - pod Resume Game
        new_game_text = font_button.render("New Game", True, WHITE)
        new_game_y = btn_y + btn_h + 20
        new_game_btn_rect = pygame.Rect(btn_x, new_game_y, btn_w, btn_h)
        if new_game_btn_rect.collidepoint(mx_hover, my_hover):  # Pozadí a okraj jen při hoveru
            pygame.draw.rect(screen, (20, 20, 20), new_game_btn_rect)
            pygame.draw.rect(screen, (70, 70, 70), new_game_btn_rect, 2)
        screen.blit(new_game_text, (new_game_btn_rect.centerx - new_game_text.get_width() // 2,
                                     new_game_btn_rect.centery - new_game_text.get_height() // 2))
        
        # Tlačítko Settings - pod New Game
        settings_text = font_button.render("Settings", True, WHITE)
        settings_y = new_game_y + btn_h + 20
        settings_btn_rect = pygame.Rect(btn_x, settings_y, btn_w, btn_h)
        
        if settings_btn_rect.collidepoint(mx_hover, my_hover):  # Pozadí a okraj jen při hoveru
            pygame.draw.rect(screen, (20, 20, 20), settings_btn_rect)
            pygame.draw.rect(screen, (70, 70, 70), settings_btn_rect, 2)
        screen.blit(settings_text, (settings_btn_rect.centerx - settings_text.get_width() // 2,
                                     settings_btn_rect.centery - settings_text.get_height() // 2))

        # Tlačítko Quit - pod Settings
        quit_text = font_button.render("Quit", True, WHITE)
        quit_y = settings_y + btn_h + 20
        quit_btn_rect = pygame.Rect(btn_x, quit_y, btn_w, btn_h)
        
        if quit_btn_rect.collidepoint(mx_hover, my_hover):  # Pozadí a okraj jen při hoveru
            pygame.draw.rect(screen, (20, 20, 20), quit_btn_rect)
            pygame.draw.rect(screen, (70, 70, 70), quit_btn_rect, 2)
        screen.blit(quit_text, (quit_btn_rect.centerx - quit_text.get_width() // 2,
                                quit_btn_rect.centery - quit_text.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)
        continue  # Přeskoč zbytek herní smyčky - ještě nehrajeme

    # ─── VYKRESLENÍ PAUSE MENU ────────────────────────────────────────────────
    if game_state == GAME_STATE_PAUSED:
        # Pozadí (dlažba + prach + vinětace)
        screen.blit(bg_surf, (0, 0))
        dust_surf.fill((0, 0, 0, 0))
        for dp in dust_particles:
            dp.update()
            r = max(1, int(dp.size))
            pygame.draw.circle(dust_surf, (200, 210, 230, int(dp.alpha)),
                               (int(dp.x), int(dp.y)), r)
        screen.blit(dust_surf, (0, 0))
        screen.blit(vignette_surf, (0, 0))

        # Centrální čtverec Pause Menu
        p_w, p_h = 600, 400
        p_rect = pygame.Rect(WIDTH // 2 - p_w // 2, HEIGHT // 2 - p_h // 2, p_w, p_h)
        pygame.draw.rect(screen, BLACK, p_rect)
        pygame.draw.rect(screen, (150, 150, 150), p_rect, 4)  # Šedý obrys

        # Text "PAUSED" - na horní části panelu
        paused_text = font_title.render("PAUSED", True, WHITE)
        screen.blit(paused_text, (p_rect.centerx - paused_text.get_width() // 2,
                                  p_rect.top + 20))

        # Poloha myši pro hover efekty tlačítek pauzy
        mx_hover, my_hover = pygame.mouse.get_pos()

        # Tlačítko Resume - pod textem
        resume_text = font_button.render("Resume", True, WHITE)
        btn_w, btn_h = 250, 50
        btn_x = p_rect.centerx - btn_w // 2
        btn_y = p_rect.centery - 40
        resume_btn_rect = pygame.Rect(btn_x, btn_y, btn_w, btn_h)
        
        if resume_btn_rect.collidepoint(mx_hover, my_hover):  # Pozadí a okraj jen při hoveru
            pygame.draw.rect(screen, (20, 20, 20), resume_btn_rect)
            pygame.draw.rect(screen, (70, 70, 70), resume_btn_rect, 2)
        screen.blit(resume_text, (resume_btn_rect.centerx - resume_text.get_width() // 2,
                                  resume_btn_rect.centery - resume_text.get_height() // 2))

        # Tlačítko Back to Main Menu
        back_to_menu_text = font_button.render("Back to Menu", True, WHITE)
        back_y = btn_y + btn_h + 20
        back_btn_rect = pygame.Rect(btn_x, back_y, btn_w, btn_h)
        
        if back_btn_rect.collidepoint(mx_hover, my_hover):  # Pozadí a okraj jen při hoveru
            pygame.draw.rect(screen, (20, 20, 20), back_btn_rect)
            pygame.draw.rect(screen, (70, 70, 70), back_btn_rect, 2)
        screen.blit(back_to_menu_text, (back_btn_rect.centerx - back_to_menu_text.get_width() // 2,
                                        back_btn_rect.centery - back_to_menu_text.get_height() // 2))

        pygame.display.flip()
        clock.tick(60)
        continue  # Přeskoč zbytek herní smyčky - jsme v pauze

    # ─── VYKRESLENÍ SETTINGS ──────────────────────────────────────────────────
    if game_state == GAME_STATE_SETTINGS:
        # Pozadí (dlažba + prach + vinětace)
        screen.blit(bg_surf, (0, 0))
        dust_surf.fill((0, 0, 0, 0))
        for dp in dust_particles:
            dp.update()
            r = max(1, int(dp.size))
            pygame.draw.circle(dust_surf, (200, 210, 230, int(dp.alpha)),
                               (int(dp.x), int(dp.y)), r)
        screen.blit(dust_surf, (0, 0))
        screen.blit(vignette_surf, (0, 0))

        # Centrální čtverec Settings
        s_w, s_h = 600, 400
        s_rect = pygame.Rect(WIDTH // 2 - s_w // 2, HEIGHT // 2 - s_h // 2, s_w, s_h)
        pygame.draw.rect(screen, BLACK, s_rect)
        pygame.draw.rect(screen, (150, 150, 150), s_rect, 4) # Šedý obrys

        # Text "Comming Soon..."
        soon_text = font_title.render("Comming Soon...", True, WHITE)
        screen.blit(soon_text, (s_rect.centerx - soon_text.get_width() // 2,
                                s_rect.centery - soon_text.get_height() // 2))
        
        # Nápověda pro návrat
        back_text = font_controls.render("Click anywhere to return", True, (150, 150, 150))
        screen.blit(back_text, (s_rect.centerx - back_text.get_width() // 2, s_rect.bottom + 20))

        pygame.display.flip()
        clock.tick(60)
        continue

    # Aktualizace animace brány
    gate_speed_mult = 1.0
    if len(enemies) == 0:
        # Plynulé otevírání
        if gate_opening_scale < 1.0:
            if gate_opening_scale == 0.0:
                shake_intensity = 15.0 # Silný shake při otevření
            gate_opening_scale += 0.02
        
        # Proximity speed (čím blíže hráč, tím rychleji kmitá)
        dist_to_gate = math.hypot(cube_x - respawn_x, cube_y - (respawn_y + RESPAWN_HEIGHT//2))
        gate_speed_mult = 1.0 + max(0, (500 - dist_to_gate) / 250)
        
        gate_anim_timer += 0.05 * gate_speed_mult
        # Spawnování částic brány
        if random.random() < 0.4 * gate_speed_mult:
            gate_particles.append(GateParticle(respawn_x + RESPAWN_WIDTH, respawn_y + RESPAWN_HEIGHT // 2))
    else:
        gate_opening_scale = 0.0 # Reset pokud se nepřátelé nějak obnoví
    
    # Útlum screen shaku
    if shake_intensity > 0:
        shake_intensity *= 0.9
    if shake_intensity < 0.1:
        shake_intensity = 0.0

    # Aktualizace částic brány
    gate_particles = [p for p in gate_particles if p.update(gate_speed_mult)]

    # POHYB KOSTKY - hráčův modrý čtverec se pohybuje
    cube_x += vel_x  # Přidej rychlost X
    cube_y += vel_y  # Přidej rychlost Y
    vel_x  *= DASH_FRICTION  # Zpomaluji rychlost (tření)
    vel_y  *= DASH_FRICTION  # Zpomaluji rychlost (tření)
    
    # Kostka se nemůže jít mimo obrazovku
    cube_x  = max(0, min(WIDTH  - cube_size, cube_x))
    cube_y  = max(0, min(HEIGHT - cube_size, cube_y))
    
    # Pokud je rychlost velmi malá, zastav se
    if abs(vel_x) < 0.1: vel_x = 0.0
    if abs(vel_y) < 0.1: vel_y = 0.0

    # RESPAWN CHECKPOINT - kontrola když se dotkneš zelené krabičky
    if (len(enemies) == 0 and
        cube_x < respawn_x + RESPAWN_WIDTH and 
        cube_x + cube_size > respawn_x and
        cube_y < respawn_y + RESPAWN_HEIGHT and 
        cube_y + cube_size > respawn_y):  # Kontrola dotyku
        # Přidej skóre a ulož postup
        level_completed += 1
        save_game(level_completed)
        
        # Přeskoč kostku zpět na start
        cube_x = float(START_X)
        cube_y = float(START_Y)
        vel_x = 0.0  # Zastav pohyb
        vel_y = 0.0  # Zastav pohyb
        
        # Obnovi všechny nepřátelé na jejich startu podle nového levelu
        enemies = get_level_enemies(level_completed)
        slash_timer = 0  # Zastavit animaci
        enemies_hit_this_slash.clear()  # Vyčisti seznam
        player_hp = min(PLAYER_MAX_HP, player_hp + 1)  # Obnov 1 HP za dokončení levelu
        player_invincible = 0       # Zruš nezranitelnost

    # AI NEPŘÁTEL - jak se nepřátelé pohybují
    cx = cube_x + cube_size / 2  # Střed kostky
    cy = cube_y + cube_size / 2  # Střed kostky

    # Nezranitelnost při dashu - pokud je hráč ve vysoké rychlosti, je nezranitelný
    DASH_INVINCIBLE_THRESHOLD = 8.0  # Minimální rychlost pro nezranitelnost při dashu
    is_dashing = math.hypot(vel_x, vel_y) > DASH_INVINCIBLE_THRESHOLD

    # Odpočet nezranitelnosti hráče (neodpočítává se během dashu)
    if player_invincible > 0 and not is_dashing:
        player_invincible -= 1
    
    for enemy in enemies:
        ecx = enemy.x + enemy.size / 2  # Střed nepřítele
        ecy = enemy.y + enemy.size / 2  # Střed nepřítele
        dist = math.hypot(cx - ecx, cy - ecy)  # Vzdálenost k hráči
        
        # Vidí nepřítel hráče?
        if dist < SPOT_RADIUS and dist > 0:
            dx = (cx - ecx) / dist  # Směr X
            dy = (cy - ecy) / dist  # Směr Y
            
            if enemy.hp <= 5:  # Když má málo zdraví
                # Utíká od hráče
                enemy.x -= dx * ENEMY_SPEED
                enemy.y -= dy * ENEMY_SPEED
            else:  # Má dost zdraví
                # Pronásleduje hráče
                if dist > (cube_size / 2 + enemy.size / 2 - 5):
                    enemy.x += dx * ENEMY_SPEED
                    enemy.y += dy * ENEMY_SPEED

        # KONTAKTNÍ ZRANĚNÍ - nepřítel se dotkl hráče?
        # Při dashu je hráč nezranitelný
        player_rect = pygame.Rect(cube_x, cube_y, cube_size, cube_size)
        enemy_rect_col = pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size)
        if player_rect.colliderect(enemy_rect_col) and player_invincible == 0 and not is_dashing:
            player_hp -= PLAYER_DAMAGE          # Odeber život
            player_invincible = PLAYER_INVINCIBLE_FRAMES  # Nastav nezranitelnost
                    
        # Nepřítel se nemůže jít mimo obrazovku
        enemy.x = max(0, min(WIDTH - enemy.size, enemy.x))
        enemy.y = max(0, min(HEIGHT - enemy.size, enemy.y))

    # SMRT HRÁČE - žádné životy? Respawn na start
    if player_hp <= 0:
        player_hp = PLAYER_MAX_HP           # Obnov životy
        player_invincible = PLAYER_INVINCIBLE_FRAMES  # Krátká nezranitelnost po respawnu
        cube_x = float(START_X)             # Přeskoč na start
        cube_y = float(START_Y)
        vel_x = 0.0
        vel_y = 0.0
        slash_timer = 0
        enemies_hit_this_slash.clear()

    # ROTACE KE KURZORU - otáčej katanu tak aby ukazovala na myš
    cx = cube_x + cube_size / 2  # Střed kostky X
    cy = cube_y + cube_size / 2  # Střed kostky Y
    mx, my = pygame.mouse.get_pos()  # Pozice myši
    angle = -math.degrees(math.atan2(my - cy, mx - cx))  # Vypočítej úhel

    # ANIMACE KATANY - automatické máchnutí zbraní
    is_slashing = slash_timer > 0  # Probíhá teď slash?
    if is_slashing:  # Pokud ano
        # Kolik procent animace je hotovo?
        raw_t    = 1.0 - slash_timer / SLASH_DURATION
        progress = ease_katana(raw_t)  # Hladký pohyb (ease)
        # Vypočítej aktuální úhel katany
        blade_pivot = SLASH_START_ANGLE + (SLASH_END_ANGLE - SLASH_START_ANGLE) * progress
        slash_timer -= 1  # Zmenši čítač
        
        # Zraňuj nepřátele během útoku (ale jen jednou za útok)
        # Tvar katany pro detekci zranění
        c_half = cube_size / 2  # Poloviny
        tip_dist = -10 - int(cube_size * 1.65)  # Vzdálenost hrotu
        
        # Vytvoř polygon - tvar katany
        hitbox_poly = []
        w_px, w_py = rotate_point(c_half, -c_half, -angle)  # Zápěstí
        hitbox_poly.append((cx + w_px, cy + w_py))
        
        # Přidej body po čepeli
        for p_angle in range(0, int(SLASH_END_ANGLE) + 5, 5):
            rx, ry = rotate_point(tip_dist - 25, 0, p_angle)
            lx = rx + c_half
            ly = ry - c_half
            w_lx, w_ly = rotate_point(lx, ly, -angle)
            hitbox_poly.append((cx + w_lx, cy + w_ly))
            
        # Zkontroluj všechny nepřátele
        for enemy in enemies[:]:
            if enemy in enemies_hit_this_slash:  # Už jsme ho zasáhli?
                continue  # Přeskoči ho
                
            # Střed nepřítele
            ecx = enemy.x + enemy.size / 2
            ecy = enemy.y + enemy.size / 2
            
            # Je nepřítel uvnitř tvaru katany? (polygon test)
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
                
            if inside:  # Je nepřítel zasažen?
                enemy.hp -= attack_damage  # Způsobí zranění
                enemies_hit_this_slash.add(enemy)  # Vyznač jako zasažený
                if enemy.hp <= 0:  # Je mrtvý?
                    enemies.remove(enemy)  # Odstraň z hry
    else:  # Když ne slashing
        # Katana v klidu - leží vzadu
        blade_pivot = 0.0

    # KATANA - tvar a rozměry zbraně
    HALF       = cube_size // 2  # Poloviny kostky
    TOP_Y      = -HALF  # Horní okraj
    HANDLE_LEN = 20  # Délka rukojeti
    BLADE_LEN  = int(cube_size * 1.65)  # Délka čepele
    BLADE_W    = 3  # Šířka čepele
    GUARD_HW   = 10  # Garda - výška
    GUARD_HD   = 3  # Garda - hloubka

    # Kde jsou jednotlivé části katany?
    pommel_x = HALF + 10  # Konec rukojeti
    guard_x  = pommel_x - HANDLE_LEN  # Garda (přechod)
    tip_x    = guard_x - BLADE_LEN  # Hrot čepele

    # Bod kolem kterého se katana otáčí
    pivot_x = (pommel_x + guard_x) / 2.0
    pivot_y = TOP_Y

    # Funkce - transformuj body katany (otočení + posun)
    def _transform(pts):
        res = []
        for x, y in pts:
            # Přesuň bod k pivotu (otočovacímu bodu)
            lx = x - pivot_x
            ly = y - pivot_y
            # Otočí bod
            rx, ry = rotate_point(lx, ly, blade_pivot)
            # Přesuň zpět a na plochu
            res.append((int(SURF_CENTER + rx + pivot_x), int(SURF_CENTER + ry + pivot_y)))
        return res

    # Tvary jednotlivých částí katany
    # Rukojeť - krabička
    handle_local = [
        (pommel_x, TOP_Y - 2), (guard_x, TOP_Y - 2),
        (guard_x,  TOP_Y + 2), (pommel_x, TOP_Y + 2),
    ]
    # Garda - kosmovitý tvar
    guard_local = [
        (guard_x - GUARD_HD, TOP_Y),
        (guard_x,            TOP_Y - GUARD_HW),
        (guard_x + GUARD_HD, TOP_Y),
        (guard_x,            TOP_Y + GUARD_HW),
    ]
    # Čepel - ostrý trojúhelník
    blade_local = [
        (guard_x, TOP_Y + BLADE_W),
        (tip_x,   TOP_Y),
        (guard_x, TOP_Y - BLADE_W),
    ]

    # Transformuj všechny tvary (otočení)
    handle_surf    = _transform(handle_local)  # Rukojeť s rotací
    guard_surf_pts = _transform(guard_local)   # Garda s rotací
    blade_surf     = _transform(blade_local)   # Čepel s rotací
    
    # Speciální body pro detaily
    pommel_surf  = _transform([(pommel_x, TOP_Y)])[0]  # Konec
    guard_c_surf = _transform([(guard_x, TOP_Y)])[0]   # Garda střed
    tip_surf     = _transform([(tip_x, TOP_Y)])[0]     # Hrot

    # INDIKÁTOR NABITÍ - malá šipka která roste když nabíjíš dash
    if is_charging:  # Právě nabíjíš?
        current_hold = (pygame.time.get_ticks() - charge_start_ticks) / 1000.0
        c_factor = min(1.0, current_hold / 3.0)  # Kolik procent nabito?
    else:
        c_factor = 0.0  # Není nabíjeno

    if c_factor >= 1.0:  # Plně nabito?
        # Velká šipka - červená barva
        ARROW_LEN  = 30   # Dlouhá
        ARROW_HALF = 12   # Široká
        draw_arrow_color = RED  # Červená
    else:  # Nabíjení
        # Malá šipka - roste s nabitím
        ARROW_LEN  = 10 + int(10 * c_factor)  # Od 10 do 20
        ARROW_HALF = 5 + int(3 * c_factor)   # Od 5 do 8
        draw_arrow_color = ARROW_COLOR  # Žluté

    # Tvar šipky (trojúhelník)
    arrow_face_x = HALF  # Přilep k pravé hraně kostky
    arrow_tip_local   = (arrow_face_x + ARROW_LEN,  0)   # Hrot
    arrow_base1_local = (arrow_face_x,               ARROW_HALF)   # Spodek
    arrow_base2_local = (arrow_face_x,              -ARROW_HALF)   # Vrch
    
    # Vytvoř body šipky na ploše (šipka se nekroutí se slashem)
    arrow_pts_surf = [
        (int(SURF_CENTER + arrow_tip_local[0]),   int(SURF_CENTER + arrow_tip_local[1])),
        (int(SURF_CENTER + arrow_base1_local[0]), int(SURF_CENTER + arrow_base1_local[1])),
        (int(SURF_CENTER + arrow_base2_local[0]), int(SURF_CENTER + arrow_base2_local[1])),
    ]

    # VYKRESLOVÁNÍ - co vidíš na obrazovce
    # ─── Pozadí ───────────────────────────────────────────────────────────────
    # 1. Kamenná dlažba jako základ
    screen.blit(bg_surf, (0, 0))

    # 2. Prachové částice - animuj a nakresli každou tečku
    dust_surf.fill((0, 0, 0, 0))  # Vymazat staré pozice (průhledné pozadí)
    for dp in dust_particles:
        dp.update()               # Posuň částici o jeden snímek
        r = int(dp.size)          # Zaokrouhli velikost na celé číslo
        if r < 1: r = 1           # Minimálně 1 pixel
        pygame.draw.circle(dust_surf, (200, 210, 230, int(dp.alpha)),
                           (int(dp.x), int(dp.y)), r)  # Nakresli světlou tečku
    screen.blit(dust_surf, (0, 0))  # Přilož všechny částice na obrazovku

    # 3. Vinětace - tmavý okraj přes celou obrazovku (kreslí se jako poslední vrstva pozadí)
    screen.blit(vignette_surf, (0, 0))
    # ─────────────────────────────────────────────────────────────────────────

    # 3. SILUETOVÁ BRÁNA
    # Celá brána má tvar vašeho nákresu. 
    # Černá část (dřík) je průchod. Vrch a spodek jsou pilíře.
    rx, ry = respawn_x, respawn_y
    rw, rh = RESPAWN_WIDTH, RESPAWN_HEIGHT
    bx, by = rx + rw // 2, ry
    
    # Parametry siluety 
    w_max   = rw + 100  
    w_head  = rw + 60   
    w_neck  = rw + 20   
    w_opening = rw + 20 
    
    # Masivní zvětšení celkové výšky
    extra_h = 400
    total_h = rh + extra_h
    
    h_pillar = 120      # Vyšší pilíře pro balanc
    h_opening = total_h - h_pillar * 2 
    
    # --- KRESLENÍ RÁMU BRÁNY (Monolith Frame) ---
    top_y = by - extra_h // 2
    top_pillar = [
        (bx, top_y - 50),                      
        (bx - w_head//2, top_y + h_pillar//3), 
        (bx - w_neck//2, top_y + h_pillar//2),
        (bx - w_max//2, top_y + h_pillar//2), 
        (bx - w_max//2, top_y + h_pillar),
        (bx + w_max//2, top_y + h_pillar), 
        (bx + w_max//2, top_y + h_pillar//2),
        (bx + w_neck//2, top_y + h_pillar//2), 
        (bx + w_head//2, top_y + h_pillar//3),
    ]
    s_by = top_y + total_h + 50
    bot_pillar = [
        (bx, s_by), 
        (bx - w_head//2, s_by - h_pillar//3), 
        (bx - w_neck//2, s_by - h_pillar//2),
        (bx - w_max//2, s_by - h_pillar//2), 
        (bx - w_max//2, s_by - h_pillar),
        (bx + w_max//2, s_by - h_pillar), 
        (bx + w_max//2, s_by - h_pillar//2),
        (bx + w_neck//2, s_by - h_pillar//2), 
        (bx + w_head//2, s_by - h_pillar//3),
    ]
    
    pygame.draw.polygon(screen, GATE_FRAME, top_pillar)
    pygame.draw.polygon(screen, (20, 20, 25), top_pillar, 2)
    pygame.draw.polygon(screen, GATE_FRAME, bot_pillar)
    pygame.draw.polygon(screen, (20, 20, 25), bot_pillar, 2)
    
    side_w = 18 # Ještě silnější stěny
    pygame.draw.rect(screen, GATE_FRAME, (bx - w_opening//2 - side_w, top_y + h_pillar, side_w, h_opening + 50))
    pygame.draw.rect(screen, GATE_FRAME, (bx + w_opening//2, top_y + h_pillar, side_w, h_opening + 50))

    # --- PRŮCHOD (The Black Part / Doorway) ---
    doorway_rect = pygame.Rect(bx - w_opening//2, top_y + h_pillar, w_opening, h_opening + 50)
    if len(enemies) == 0:
        alpha = int(180 * gate_opening_scale)
        s_glow = pygame.Surface((w_opening, doorway_rect.height), pygame.SRCALPHA)
        pygame.draw.rect(s_glow, (*DOOR_LIGHT, alpha), (0, 0, w_opening, doorway_rect.height))
        screen.blit(s_glow, doorway_rect.topleft)
        if gate_opening_scale > 0:
            light_w = int(w_opening * 2.5 * gate_opening_scale)
            l_surf = pygame.Surface((light_w, doorway_rect.height), pygame.SRCALPHA)
            for i in range(12):
                l_alpha = int(50 * (1.0 - i/12) * gate_opening_scale)
                pygame.draw.ellipse(l_surf, (*DOOR_LIGHT, l_alpha), (0, 0, light_w, doorway_rect.height))
            screen.blit(l_surf, (bx - light_w//2, doorway_rect.y), special_flags=pygame.BLEND_ADD)
    else:
        pygame.draw.rect(screen, BLACK, doorway_rect)

    # 5. ČÁSTICE (Dust)


        # 5. ČÁSTICE (Dust)
        for p in gate_particles:
            p.draw(screen)

    # Nakresli všechny nepřátele (skeletony) a jejich praskání
    for enemy in enemies:
        # Telo nepřítele - základní čtverec
        enemy_rect = pygame.Rect(enemy.x, enemy.y, enemy.size, enemy.size)
        pygame.draw.rect(screen, enemy.color, enemy_rect)
        if enemy.type_name != "goblin":
            pygame.draw.rect(screen, (255, 255, 255), enemy_rect, 2)  # Bílý okraj pro definici
        
        # Oči - dva černé kruhy (pro gobliny můžou být menší nebo jiné)
        eye_size = 5 if enemy.type_name == "goblin" else 6
        eye_offset_x = enemy.size // 4
        eye_offset_y = enemy.size // 3
        pygame.draw.circle(screen, (0, 0, 0), 
                          (int(enemy.x + eye_offset_x), int(enemy.y + eye_offset_y)), eye_size)
        pygame.draw.circle(screen, (0, 0, 0), 
                          (int(enemy.x + enemy.size - eye_offset_x), int(enemy.y + eye_offset_y)), eye_size)
        
        # Nos - jen pro skeletony
        if enemy.type_name == "skeleton":
            nose_x = enemy.x + enemy.size // 2
            nose_y = enemy.y + enemy.size // 2
            nose_size = 4
            pygame.draw.polygon(screen, (0, 0, 0), [
                (nose_x, nose_y - nose_size),
                (nose_x - nose_size, nose_y + nose_size),
                (nose_x + nose_size, nose_y + nose_size)
            ])
        
        # Trhliny Minecraft-stylu místo HP lišty
        hp_ratio = enemy.hp / enemy.max_hp
        draw_cracks(screen, enemy.x, enemy.y, enemy.size, hp_ratio)

    # Vytvoř pomocnou plochu - sem si nakreslíme kostku a katanu
    cube_surf = pygame.Surface((SURF_SIZE, SURF_SIZE), pygame.SRCALPHA)

    # Nakresli modrý čtverec (kostka) s efektem 3D
    cube_rect = pygame.Rect(
        SURF_CENTER - cube_size // 2,
        SURF_CENTER - cube_size // 2,
        cube_size, cube_size,
    )
    pygame.draw.rect(cube_surf, BLUE, cube_rect)  # Modrý čtverec
    
    # Horní a levý okraj - světlejší (3D efekt)
    pygame.draw.line(cube_surf, BLUE_LIGHT,
                     (cube_rect.left,  cube_rect.top),
                     (cube_rect.right - 1, cube_rect.top), 2)
    pygame.draw.line(cube_surf, BLUE_LIGHT,
                     (cube_rect.left,  cube_rect.top),
                     (cube_rect.left,  cube_rect.bottom - 1), 2)
    
    # Dolní a pravý okraj - tmavší (3D efekt)
    pygame.draw.line(cube_surf, BLUE_DARK,
                     (cube_rect.left,  cube_rect.bottom - 1),
                     (cube_rect.right - 1, cube_rect.bottom - 1), 2)
    pygame.draw.line(cube_surf, BLUE_DARK,
                     (cube_rect.right - 1, cube_rect.top),
                     (cube_rect.right - 1, cube_rect.bottom - 1), 2)

    # Nakresli indikátor nabití (šipka)
    pygame.draw.polygon(cube_surf, draw_arrow_color, arrow_pts_surf)

    # Nakresli katanu - jednotlivé části
    # 1. Rukojeť (tmavě hnědá)
    pygame.draw.polygon(cube_surf, HANDLE_COLOR, handle_surf)
    # 2. Konec rukojeti (stříbrný kruh)
    pygame.draw.circle(cube_surf, GUARD_COLOR, pommel_surf, 4)
    # 3. Garda - kosočtverec (stříbrný)
    pygame.draw.polygon(cube_surf, GUARD_COLOR, guard_surf_pts)
    # 4. Čepel - trojúhelník (modrá ocel)
    pygame.draw.polygon(cube_surf, BLADE_COLOR, blade_surf)
    # 5. Lesk čepele - tenká bílá čára (pro lesklý efekt)
    pygame.draw.line(cube_surf, WHITE, guard_c_surf, tip_surf, 1)

    # Otočí celou plochu tak aby katana ukazovala na myš
    rotated_surf = pygame.transform.rotate(cube_surf, angle)
    rotated_rect = rotated_surf.get_rect(center=(int(cx), int(cy)))
    screen.blit(rotated_surf, rotated_rect)  # Vykresli na obrazovku

    # DEBUG - Zobrazení hitboxů (pokud stiskneš H)
    if show_hitboxes:  # Je zapnuto?
        # Vytvořit plochu pro debug
        hitbox_surf = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
        
        # Nakresli tvar katany - červeně (pro debug)
        c_half = cube_size / 2
        tip_dist = -10 - int(cube_size * 1.65)
        
        draw_poly = []  # Body polygonu
        w_px, w_py = rotate_point(c_half, -c_half, -angle)
        draw_poly.append((cx + w_px, cy + w_py))  # Zápěstí
        
        # Přidej body po řadě
        for p_angle in range(0, int(SLASH_END_ANGLE) + 5, 5):
            rx, ry = rotate_point(tip_dist, 0, p_angle) 
            lx = rx + c_half
            ly = ry - c_half
            w_lx, w_ly = rotate_point(lx, ly, -angle)
            draw_poly.append((cx + w_lx, cy + w_ly))
            
        pygame.draw.polygon(hitbox_surf, (255, 0, 0, 40), draw_poly) # Poloprůhledná výplň čepele
        pygame.draw.polygon(hitbox_surf, RED, draw_poly, 2)          # Červený okraj přesně podle dráhy
        
        # Znázornění středu a okraje nepřátel + HP lišta
        for enemy in enemies:
            ecx = enemy.x + enemy.size / 2
            ecy = enemy.y + enemy.size / 2
            pygame.draw.circle(hitbox_surf, (0, 255, 0, 150), (int(ecx), int(ecy)), 4)
            # HP lišta nad nepřítelem (jen v debug módu)
            bar_w = int(enemy.size * (enemy.hp / enemy.max_hp))
            pygame.draw.rect(hitbox_surf, (180, 0, 0, 200), (enemy.x, enemy.y - 14, enemy.size, 7))
            pygame.draw.rect(hitbox_surf, (0, 220, 60, 220), (enemy.x, enemy.y - 14, bar_w, 7))
            hp_txt = font_controls.render(f"{enemy.hp}/{enemy.max_hp}", True, WHITE)
            screen.blit(hp_txt, (int(ecx) - hp_txt.get_width() // 2, int(enemy.y) - 30))
            
        # Znázornění zápěstí hráče
        pygame.draw.circle(hitbox_surf, (0, 255, 255, 150), (int(cx + w_px), int(cy + w_py)), 4)
            
        # Znázornění dohledu nepřátel (Agro radius)
        pygame.draw.circle(hitbox_surf, (255, 255, 0, 70), (int(cx), int(cy)), SPOT_RADIUS, 1)
            
        screen.blit(hitbox_surf, (0, 0))

    # Vykresli skóre vpravo nahoře
    score_surf = font.render(f"Level Reached: {level_completed}", True, WHITE)
    screen.blit(score_surf, (WIDTH - score_surf.get_width() - 20, 20))

    # ─── HUD ZDRAVÍ HRÁČE (vlevo dole) ───────────────────────────────────────
    heart_size = 38                 # Velikost jednoho srdce
    heart_gap  = 12                 # Mezera mezi srdci
    hp_label   = font_button.render("HP", True, (200, 200, 200))
    hud_y      = HEIGHT - heart_size - 28  # Dolní okraj s odsazením
    hud_x      = 24                        # Levý okraj
    screen.blit(hp_label, (hud_x, hud_y + (heart_size - hp_label.get_height()) // 2))
    # Nakresli srdce - plná (červená) nebo prázdná (šedá)
    for i in range(PLAYER_MAX_HP):
        hx = hud_x + hp_label.get_width() + 14 + i * (heart_size + heart_gap)
        hy = hud_y
        color_heart  = (220, 50, 50) if i < player_hp else (55, 55, 65)
        border_color = (255, 130, 130) if i < player_hp else (85, 85, 95)
        pygame.draw.circle(screen, color_heart,  (hx + heart_size // 2, hy + heart_size // 2), heart_size // 2)
        pygame.draw.circle(screen, border_color, (hx + heart_size // 2, hy + heart_size // 2), heart_size // 2, 3)
    # ─────────────────────────────────────────────────────────────────────────

    # Výpočet screen shaku pro finální blit
    shake_x = random.uniform(-shake_intensity, shake_intensity)
    shake_y = random.uniform(-shake_intensity, shake_intensity)

    # Refresh obrazovky - vidíš nový frame
    # Pokud je shake, posuneme celou obrazovku (pomocí dočasného povrchu nebo blitnutí na offset)
    if shake_intensity > 0:
        temp_screen = screen.copy()
        screen.fill(BLACK)
        screen.blit(temp_screen, (shake_x, shake_y))

    pygame.display.flip()
    # Udržuj 60 FPS (snímků za vteřinu)
    clock.tick(60)

# Vypni pygame a ukonči program
pygame.quit()
sys.exit()
