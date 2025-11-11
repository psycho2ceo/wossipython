import pygame
import random

pygame.init()

# Okno fullscreen
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Otevírání bedny - Loot boty")

clock = pygame.time.Clock()

# Background (klidně bílý obrázek)
background = pygame.image.load("background.png").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Bedna
case_size = (300, 300)
case_img = pygame.image.load("case.png").convert_alpha()
case_img = pygame.transform.scale(case_img, case_size)

# Loot obrázky
loot_images = {
    "none": pygame.image.load("af1.png").convert_alpha(),
    "rare": pygame.image.load("yeezy.png").convert_alpha(),
    "epic": pygame.image.load("balenciaga.png").convert_alpha(),
    "mythic": pygame.image.load("crocs.png").convert_alpha(),
    "legendary": pygame.image.load("rickowens.png").convert_alpha()
}

# Zmenšíme je, ať se vejde hezká řada
ITEM_SIZE = 150
for k in loot_images:
    loot_images[k] = pygame.transform.scale(loot_images[k], (ITEM_SIZE, ITEM_SIZE))

# Pravděpodobnosti
loot_table = [
    ("none", 80),
    ("rare", 10),
    ("epic", 5),
    ("mythic", 4),
    ("legendary", 1)
]

# Hezké názvy a barvy
loot_names = {
    "none": "Dneska nic. Zkus to znovu",
    "rare": "Sleva 5%",
    "epic": "Sleva 20%",
    "mythic": "Free AirForce1 + doprava zdarma k tomu",
    "legendary": "200$ kredit v nasem obchode"
}

rarity_colors = {
    "none": (180, 180, 180),
    "rare": (0, 120, 255),
    "epic": (190, 0, 255),
    "mythic": (255, 140, 0),
    "legendary": (255, 215, 0)
}

# Fonts
info_font = pygame.font.SysFont("arial", 26)
label_font = pygame.font.SysFont("arial", 28, True)
result_font = pygame.font.SysFont("arial", 40, True)

# Parametry řady
ITEM_GAP = 20
SLOT_WIDTH = ITEM_SIZE + ITEM_GAP

row_height = ITEM_SIZE + 60
row_y = HEIGHT // 2 - row_height // 2
item_y = row_y + (row_height - ITEM_SIZE) // 2
center_x = WIDTH // 2

# EKONOMIKA / KREDITY
crate_price = 20            # cena jedné bedny
credits = 999999            # prakticky nekonečný kapital pro teď
no_credit_until = 0         # do kdy zobrazovat hlášku o nedostatku kreditů (timestamp v ms)

# Stav hry
running = True
opening = False
animation_time = 2500  # ms
start_time = 0

items = []             # list rarit, co se točí
base_offset_start = 0
base_offset_end = 0
base_offset = 0

win_loot = None        # rarita, která má padnout
loot_result = None     # finální výsledek (po dokončení animace)

def roll_loot():
    """Výběr lootu podle pravděpodobností."""
    rand = random.randint(1, 100)
    cumulative = 0
    for loot, chance in loot_table:
        cumulative += chance
        if rand <= cumulative:
            return loot
    return loot_table[-1][0]

def start_spin():
    """Inicializace nového spinu."""
    global opening, start_time, items
    global base_offset_start, base_offset_end, base_offset
    global win_loot, loot_result

    opening = True
    start_time = pygame.time.get_ticks()
    loot_result = None

    # Tohle bude rarita, která skončí uprostřed
    win_loot = roll_loot()

    num_items = 40
    win_index = random.randint(15, 25)

    keys = list(loot_images.keys())
    items = []
    for i in range(num_items):
        if i == win_index:
            items.append(win_loot)
        else:
            items.append(random.choice(keys))

    # Startovní pozice – celá řada začíná vpravo
    base_offset_start = WIDTH + 50

    # Konečná pozice – win_index přesně uprostřed obrazovky
    global SLOT_WIDTH
    base_offset_end = center_x - (win_index * SLOT_WIDTH + ITEM_SIZE / 2)

    base_offset = base_offset_start

def draw_row_and_get_center_key():
    """Nakreslí řadu na tmavým pozadí, vrátí rarity key itemu nejblíž středu."""
    global base_offset

    # Tmavý pruh pod řadou
    pygame.draw.rect(screen, (15, 15, 15), (0, row_y, WIDTH, row_height))

    center_key = None
    min_dist = 10**9

    # Loot položky
    for idx, key in enumerate(items):
        x = base_offset + idx * SLOT_WIDTH
        if x + ITEM_SIZE < 0 or x > WIDTH:
            continue  # mimo obrazovku

        screen.blit(loot_images[key], (x, item_y))

        # Zjištění, která bota je nejblíž středu
        x_center = x + ITEM_SIZE / 2
        dist = abs(x_center - center_x)
        if dist < min_dist:
            min_dist = dist
            center_key = key

    # Highlight slot uprostřed (rámeček)
    highlight_rect = pygame.Rect(
        center_x - ITEM_SIZE // 2 - 10,
        item_y - 10,
        ITEM_SIZE + 20,
        ITEM_SIZE + 20
    )
    pygame.draw.rect(screen, (255, 255, 255), highlight_rect, 3)

    return center_key

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_SPACE and not opening:
                # Pokus o otevření bedny → kontrola kreditu
                if credits >= crate_price:
                    credits -= crate_price
                    start_spin()
                else:
                    # Nastavíme čas, do kdy se má zobrazovat warning
                    no_credit_until = pygame.time.get_ticks() + 1500  # 1.5 s hláška

    # Logika animace
    if opening:
        now = pygame.time.get_ticks()
        elapsed = now - start_time
        progress = min(elapsed / animation_time, 1.0)

        base_offset = base_offset_start + (base_offset_end - base_offset_start) * progress

        if progress >= 1.0:
            # Hotovo – stojíme na výherní botě
            opening = False
            loot_result = win_loot

    # Vykreslení
    screen.blit(background, (0, 0))

    # Cena bedny a kredity nahoře
    price_text = info_font.render(f"Cena bedny: ${crate_price}", True, (0, 0, 0))
    screen.blit(price_text, (20, 20))

    credits_text = info_font.render(f"Kredity: ${credits}", True, (0, 0, 0))
    credits_rect = credits_text.get_rect(topright=(WIDTH - 20, 20))
    screen.blit(credits_text, credits_rect)

    # Bedna – zmizí, když máme výsledek
    if loot_result is None:
        case_x = (WIDTH - case_size[0]) // 2
        case_y = HEIGHT // 6
        screen.blit(case_img, (case_x, case_y))

    center_key = None
    if items:
        center_key = draw_row_and_get_center_key()

    # Text k výsledku – pod řadou
    if loot_result is not None and center_key is not None:
        rarity = loot_result
        name = loot_names.get(rarity, rarity.upper())
        color = rarity_colors.get(rarity, (255, 255, 255))

        label_text = label_font.render("Padlo ti", True, (255, 255, 255))
        label_rect = label_text.get_rect(center=(center_x, row_y + row_height + 30))
        screen.blit(label_text, label_rect)

        result_str = f"{name} [{rarity.upper()}]"
        result_text = result_font.render(result_str, True, color)
        result_rect = result_text.get_rect(center=(center_x, row_y + row_height + 70))
        screen.blit(result_text, result_rect)

    # Info text dole
    info_text = info_font.render("SPACE = otevřít bednu | ESC = konec", True, (0, 0, 0))
    info_rect = info_text.get_rect(midbottom=(WIDTH // 2, HEIGHT - 20))
    screen.blit(info_text, info_rect)

    # Hláška při nedostatku kreditu
    now_time = pygame.time.get_ticks()
    if now_time < no_credit_until:
        warn_text = info_font.render("Nedostatek kreditů!", True, (200, 0, 0))
        warn_rect = warn_text.get_rect(midbottom=(WIDTH // 2, HEIGHT - 60))
        screen.blit(warn_text, warn_rect)

    pygame.display.flip()
    clock.tick(60)

pygame.quit()
