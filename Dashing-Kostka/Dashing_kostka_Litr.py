import pygame
import sys

# Inicializace Pygame
pygame.init()

# Nastavení okna 
WIDTH, HEIGHT = 800, 600
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Dashing Kostka")

# Barvy
BLACK = (0, 0, 0)
RED = (255, 0, 0)

# Vlastnosti kostky
cube_size = 50
cube_x = WIDTH // 2 - cube_size // 2
cube_y = HEIGHT // 2 - cube_size // 2

clock = pygame.time.Clock()

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
            
        # Zrušení pomocí ESC
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            running = False

    # Vykreslení
    screen.fill(BLACK) # Černé pozadí
    
    # Vykreslení červené kostky uprostřed
    pygame.draw.rect(screen, RED, (cube_x, cube_y, cube_size, cube_size))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
