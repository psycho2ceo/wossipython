import pygame
import random
import db_utils

pygame.init()
db_utils.init_db()

# Okno
info = pygame.display.Info()
WIDTH, HEIGHT = info.current_w, info.current_h
screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.FULLSCREEN)
pygame.display.set_caption("Case opening")

clock = pygame.time.Clock()

# Fonts
info_font = pygame.font.SysFont("arial", 26)
result_font = pygame.font.SysFont("arial", 40, True)

# LOGIN
def login():
    username = ""
    font = pygame.font.SysFont("arial", 50)

    while True:
        screen.fill((240,240,240))

        txt = font.render("Zadej username", True, (0,0,0))
        screen.blit(txt, txt.get_rect(center=(WIDTH//2, HEIGHT//3)))

        box = pygame.Rect(WIDTH//2 - 200, HEIGHT//2 - 40, 400, 70)
        pygame.draw.rect(screen, (255,255,255), box)
        pygame.draw.rect(screen, (0,0,0), box, 3)

        text = font.render(username, True, (0,0,0))
        screen.blit(text, (box.x+10, box.y+10))

        pygame.display.flip()

        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                pygame.quit()
                exit()

            if e.type == pygame.KEYDOWN:
                if e.key == pygame.K_RETURN and username.strip():
                    db_utils.get_or_create_user(username)
                    return username
                elif e.key == pygame.K_BACKSPACE:
                    username = username[:-1]
                else:
                    if len(username) < 15:
                        username += e.unicode

CURRENT_USER = login()
user = db_utils.get_or_create_user(CURRENT_USER)
credits = user["credits"]

# Assets
background = pygame.image.load("background.png").convert()
background = pygame.transform.scale(background, (WIDTH, HEIGHT))

case_img = pygame.image.load("case.png").convert_alpha()
case_img = pygame.transform.scale(case_img, (300,300))

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

loot_names = {
    "none": "Dneska jsi nic nevyhral. Zkus to znovu",
    "rare": "Vyhra: sleva 5%",
    "epic": "Vyhra: sleva 20%",
    "mythic": "Vyhra: AirForce1",
    "legendary": "Vyhra: store kredit 200$"
}

# Game vars
crate_price = 20
ITEM_GAP = 20
SLOT_WIDTH = ITEM_SIZE + ITEM_GAP

center_x = WIDTH // 2
row_y = HEIGHT // 2 + 100
item_y = row_y - ITEM_SIZE // 2

running = True
opening = False
animation_time = 4000
start_time = 0

items = []
base_offset = 0
base_offset_start = 0
base_offset_end = 0

win_loot = None
loot_result = None

def start_spin():
    global opening, start_time, items
    global base_offset_start, base_offset_end, base_offset
    global win_loot, credits, loot_result

    result = db_utils.open_case(CURRENT_USER)

    if not result.get("success"):
        return

    win_loot = result["loot"]["key"]
    credits = result["user_credits"]

    opening = True
    start_time = pygame.time.get_ticks()
    loot_result = None

    num_items = 40
    win_index = random.randint(15, 25)

    keys = list(loot_images.keys())
    items.clear()

    for i in range(num_items):
        items.append(win_loot if i == win_index else random.choice(keys))

    base_offset_start = WIDTH + 100
    base_offset_end = center_x - (win_index * SLOT_WIDTH + ITEM_SIZE / 2)
    base_offset = base_offset_start

def ease(t):
    return 1 - (1 - t)**5

# MAIN LOOP
while running:

    for e in pygame.event.get():
        if e.type == pygame.QUIT:
            running = False

        if e.type == pygame.KEYDOWN:
            if e.key == pygame.K_ESCAPE:
                running = False

            if e.key == pygame.K_SPACE and not opening:
                if credits >= crate_price:
                    start_spin()

    if opening:
        t = min((pygame.time.get_ticks() - start_time) / animation_time, 1)
        base_offset = base_offset_start + (base_offset_end - base_offset_start) * ease(t)

        if t >= 1:
            opening = False
            loot_result = win_loot

    # DRAW
    screen.blit(background, (0,0))

    # case
    if loot_result is None:
        screen.blit(case_img, ((WIDTH-300)//2, HEIGHT//4))

    # items
    for i, key in enumerate(items):
        x = base_offset + i * SLOT_WIDTH
        if x + ITEM_SIZE > 0 and x < WIDTH:
            screen.blit(loot_images[key], (x, item_y))

    # středová čára (CSGO style)
    if opening:
        pygame.draw.line(
            screen,
            (109, 169, 155), #zelena (muzes zmenit)
            (center_x, row_y - ITEM_SIZE // 2 - 20),
            (center_x, row_y + ITEM_SIZE // 2 + 20),
            4
        )

    # result
    if loot_result:
        txt = result_font.render(loot_names[loot_result], True, (0,0,0))
        screen.blit(txt, txt.get_rect(center=(center_x, row_y + 120)))

    # HUD (LEFT TOP)
    x = 20
    y = 20

    screen.blit(info_font.render(f"User: {CURRENT_USER}", True, (109, 169, 155)), (x, y))
    x += 250

    screen.blit(info_font.render(f"Kredity: ${credits}", True, (109, 169, 155)), (x, y))
    x += 250

    screen.blit(info_font.render(f"Cena: ${crate_price}", True, (109, 169, 155)), (x, y))
    x += 200

    screen.blit(info_font.render("SPACE = spin", True, (109, 169, 155)), (x, y))

    pygame.display.flip()
    clock.tick(60)

pygame.quit()