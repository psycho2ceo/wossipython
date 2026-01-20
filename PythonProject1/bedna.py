import pygame
import random
import db_utils   # ⬅️ DB
import time

pygame.init()
db_utils.init_db()  # ⬅️ DB init

# Okno fullscreen
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Otevírání bedny - Loot boty")

clock = pygame.time.Clock()

# Background
background = pygame.image.load("background.png").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

# Bedna
case_size = (300, 300)
case_img = pygame.image.load("case.png").convert_alpha()
case_img = pygame.transform.scale(case_img, case_size)

# Loot obrázky
loot_images = {
    "none": pygame.image.load("none.png").convert_alpha(),
    "rare": pygame.image.load("pet.png").convert_alpha(),
    "epic": pygame.image.load("dva.png").convert_alpha(),
    "mythic": pygame.image.load("force1.png").convert_alpha(),
    "legendary": pygame.image.load("dveste.png").convert_alpha()
}

ITEM_SIZE = 150
for k in loot_images:
    loot_images[k] = pygame.transform.scale(loot_images[k], (ITEM_SIZE, ITEM_SIZE))

# Pravděpodobnosti (fallback)
loot_table = [
    ("none", 80),
    ("rare", 10),
    ("epic", 5),
    ("mythic", 4),
    ("legendary", 1)
]

# Názvy a barvy
loot_names = {
    "none": "Dneska nic. Zkus to znovu",
    "rare": "Sleva 5%",
    "epic": "Sleva 20%",
    "mythic": "Free AirForce1 + doprava zdarma k tomu",
    "legendary": "200$ kredit v našem obchodě"
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

# EKONOMIKA / KREDITY (⬅️ Z DB)
crate_price = 20
user = db_utils.get_user(1)
credits = user["credits"] if user else 20
no_credit_until = 0

# Stav hry
running = True
opening = False
animation_time = 5000
start_time = 0

items = []
base_offset_start = 0
base_offset_end = 0
base_offset = 0

win_loot = None
loot_result = None

def roll_loot():
    rand = random.randint(1, 100)
    cumulative = 0
    for loot, chance in loot_table:
        cumulative += chance
        if rand <= cumulative:
            return loot
    return loot_table[-1][0]

def start_spin():
    global opening, start_time, items
    global base_offset_start, base_offset_end, base_offset
    global win_loot, loot_result, credits

    opening = True
    start_time = pygame.time.get_ticks()
    loot_result = None

    # 🔵 JEDINÁ ZMĚNA: DB místo random
    db_result = db_utils.open_case_local(1, 1)
    if db_result.get("success"):
        win_loot = db_result["loot"]["key"]
        credits = db_result["user_credits"]
    else:
        win_loot = roll_loot()

    num_items = 40
    win_index = random.randint(15, 25)

    keys = list(loot_images.keys())
    items = []
    for i in range(num_items):
        items.append(win_loot if i == win_index else random.choice(keys))

    base_offset_start = WIDTH + 50
    base_offset_end = center_x - (win_index * SLOT_WIDTH + ITEM_SIZE / 2)
    base_offset = base_offset_start

def ease_out_quint(t):
    return 1 - (1 - t) ** 5

def draw_row_and_get_center_key():
    global base_offset
    pygame.draw.rect(screen, (236, 236, 236), (0, row_y, WIDTH, row_height))

    center_key = None
    min_dist = 10**9

    for idx, key in enumerate(items):
        x = base_offset + idx * SLOT_WIDTH
        if x + ITEM_SIZE < 0 or x > WIDTH:
            continue
        screen.blit(loot_images[key], (x, item_y))
        dist = abs((x + ITEM_SIZE / 2) - center_x)
        if dist < min_dist:
            min_dist = dist
            center_key = key

    pygame.draw.rect(
        screen, (255, 255, 255),
        (center_x - ITEM_SIZE // 2 - 10, item_y - 10, ITEM_SIZE + 20, ITEM_SIZE + 20), 3
    )

    return center_key

# ---------------- MAIN LOOP ----------------
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                running = False

            if event.key == pygame.K_SPACE and not opening:
                if credits >= crate_price:
                    start_spin()
                else:
                    no_credit_until = pygame.time.get_ticks() + 1500

    if opening:
        t = min((pygame.time.get_ticks() - start_time) / animation_time, 1)
        base_offset = base_offset_start + (base_offset_end - base_offset_start) * ease_out_quint(t)
        if t >= 1:
            opening = False
            loot_result = win_loot

    screen.blit(background, (0, 0))

    if loot_result is None:
        screen.blit(case_img, ((WIDTH - case_size[0]) // 2, HEIGHT // 6))

    if items:
        draw_row_and_get_center_key()

    if loot_result:
        txt = result_font.render(
            f"{loot_names[loot_result]} [{loot_result.upper()}]",
            True, rarity_colors[loot_result]
        )
        screen.blit(txt, txt.get_rect(center=(center_x, row_y + row_height + 70)))

    screen.blit(info_font.render(f"Kredity: ${credits}", True, (0,0,0)), (20,20))
    screen.blit(info_font.render("SPACE = otevřít | ESC = konec", True, (0,0,0)),
                (WIDTH//2 - 150, HEIGHT - 30))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()