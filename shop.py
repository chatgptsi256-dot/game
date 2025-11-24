import pygame
import os
import json

class FontCompat:
    def __init__(self, size, bold=False):
        # Prefer fonts with широкая кириллица поддержка
        candidates = ["DejaVu Sans", "Arial Unicode MS", "Noto Sans", "Arial", "Liberation Sans", "consolas"]
        # pygame.font
        for name in candidates:
            try:
                self._mode = "font"
                self._font = pygame.font.SysFont(name, size, bold=bold)
                # Ensure it actually created a font
                if self._font:
                    break
            except Exception:
                self._font = None
        if not getattr(self, "_font", None):
            # Fallback to freetype
            import pygame.freetype as ft
            ft.init()
            self._mode = "freetype"
            for name in candidates:
                try:
                    self._font = ft.SysFont(name, size)
                    if self._font:
                        if bold:
                            try:
                                self._font.style = ft.STYLE_STRONG
                            except Exception:
                                pass
                        break
                except Exception:
                    self._font = None
        # As a last resort, create a default font to avoid crashes
        if not getattr(self, "_font", None):
            self._mode = "font"
            self._font = pygame.font.Font(None, size)

    def render(self, text, antialias, color):
        if self._mode == "font":
            return self._font.render(text, antialias, color)
        surface, _ = self._font.render(text, color)
        return surface

PURCHASES_FILE = "purchases.json"

def _load_purchases():
    try:
        with open(PURCHASES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_purchases(data):
    try:
        with open(PURCHASES_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def _wrap_text(text, font_obj, max_width):
    """
    Naive word-wrap using rendered width measurement.
    font_obj is FontCompat; we measure by rendering and reading surface width.
    """
    if not text:
        return [""]
    words = text.split()
    lines = []
    cur = ""
    for w in words:
        test = w if not cur else cur + " " + w
        surf = font_obj.render(test, True, (255, 255, 255))
        if surf.get_width() <= max_width:
            cur = test
        else:
            if cur:
                lines.append(cur)
            cur = w
    if cur:
        lines.append(cur)
    return lines

def show_shop(fullscreen=False):
    WIDTH, HEIGHT = 800, 600
    flags = pygame.FULLSCREEN if fullscreen else 0
    win = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    pygame.display.set_caption("Shop")

    GRAY = (40, 40, 40)
    WHITE = (255, 255, 255)
    GOLD = (255, 215, 0)
    RED = (200, 0, 0)
    LIGHT_RED = (255, 80, 80)
    HOVER = (120, 120, 255)
    GREEN = (0, 200, 120)

    title_font = FontCompat(42, bold=True)
    font = FontCompat(28)
    small = FontCompat(22)
    clock = pygame.time.Clock()

    # Read coins if present (optional), else 0
    coins = 0
    if os.path.exists("coins.txt"):
        try:
            with open("coins.txt", "r", encoding="utf-8") as f:
                coins = int(f.read().strip() or 0)
        except Exception:
            coins = 0

    # Load icons from assets/shop_icons
    icons = []
    icons_dir = os.path.join("assets", "shop_icons")
    if os.path.isdir(icons_dir):
        for fname in sorted(os.listdir(icons_dir)):
            if fname.lower().endswith(".png"):
                try:
                    img = pygame.image.load(os.path.join(icons_dir, fname)).convert_alpha()
                    img = pygame.transform.smoothscale(img, (64, 64))

                    # Heuristic filter: skip "planet-like" round icons
                    # 1) find opaque bounding box
                    w, h = img.get_width(), img.get_height()
                    minx, miny, maxx, maxy = w, h, 0, 0
                    opaque = 0
                    px = pygame.PixelArray(img)
                    # sample every 2 px for speed
                    for y in range(0, h, 2):
                        for x in range(0, w, 2):
                            a = (img.unmap_rgb(px[x, y]).a if hasattr(img, "unmap_rgb") else img.get_at((x, y)).a)
                            if a > 10:
                                opaque += 1
                                if x < minx: minx = x
                                if y < miny: miny = y
                                if x > maxx: maxx = x
                                if y > maxy: maxy = y
                    del px
                    if maxx > minx and maxy > miny:
                        bw, bh = (maxx - minx + 1), (maxy - miny + 1)
                        aspect = bw / bh if bh else 1.0
                        fill_ratio = opaque / ((w//2) * (h//2) + 1e-6)
                        # circle-like if nearly square bbox and medium-high fill density
                        if 0.9 <= aspect <= 1.1 and 0.60 <= fill_ratio <= 0.90:
                            continue

                    icons.append((fname, img))
                except Exception:
                    continue

    # Ability mapping (initial: 1.png → quantum_capacitor, price 0)
    ABILITIES = {
        "quantum_capacitor.png": {
            "id": "quantum_capacitor",
            "name": "Quantum Capacitor",
            "price": 0,
            "desc": "Стоя 5 сек — заряжается быстрый луч. Все выстрелы станут лучами до начала движения."
        },
        "singularity_surge.png": {
            "id": "singularity_surge",
            "name": "Singularity Surge",
            "price": 0,
            "desc": "Активная способность (Q): ставит гравитационный якорь, который тянет врагов, замедляет их и наносит урон по площади 6 секунд. Кулдаун 12 секунд."
        },
        "shield_matrix.png": {
            "id": "shield_matrix",
            "name": "Shield Matrix",
            "price": 0,
            "desc": "Пассивный щит: каждые 5 секунд автоматически блокирует одну атаку врага."
        },
        "explosive_blast.png": {
            "id": "explosive_blast",
            "name": "Explosive Blast",
            "price": 0,
            "desc": "Активная способность (E): создаёт мощный взрыв вокруг корабля, уничтожая всех врагов в радиусе. Кулдаун 8 секунд."
        },
        "repair_kit.png": {
            "id": "repair_kit",
            "name": "Repair Kit",
            "price": 0,
            "desc": "Активная способность (R): восстанавливает 50 HP. Кулдаун 30 секунд."
        }
    }
    purchases = _load_purchases()
    selected = None

    # Pagination (arrow navigation)
    cols = 4
    rows_per_page = 2
    per_page = cols * rows_per_page  # 8
    page = 0
    pages = (len(icons) + per_page - 1) // per_page if icons else 1
    start_y = 150
    gap_x = 190
    gap_y = 160
    total_width = gap_x * (cols - 1)
    start_x = (WIDTH // 2) - (total_width // 2)

    while True:
        win.fill(GRAY)
        mx, my = pygame.mouse.get_pos()

        title = title_font.render("SHOP", True, GOLD)
        win.blit(title, title.get_rect(center=(WIDTH // 2, 80)))

        coins_text = font.render(f"Coins: {coins}", True, WHITE)
        win.blit(coins_text, (20, 20))

        # Draw icon grid for current page
        if not icons:
            empty = small.render("No items available", True, (190, 190, 190))
            win.blit(empty, empty.get_rect(center=(WIDTH // 2, HEIGHT // 2)))
        else:
            start_index = page * per_page
            end_index = min(len(icons), start_index + per_page)
            for i in range(start_index, end_index):
                col = (i - start_index) % cols
                row = (i - start_index) // cols
                x = start_x + col * gap_x
                y = start_y + row * gap_y
                rect = pygame.Rect(0, 0, 96, 96)
                rect.center = (x, y)
                hovered = rect.collidepoint(mx, my)
                border_color = HOVER if hovered else (90, 90, 90)
                pygame.draw.rect(win, border_color, rect, 2)
                fname, icon_img = icons[i]
                win.blit(icon_img, icon_img.get_rect(center=rect.center))
                # Render price/owned for abilities
                if fname in ABILITIES:
                    meta = ABILITIES[fname]
                    is_owned = purchases.get(meta["id"], False)
                    label = "OWNED" if is_owned else f"{meta['price']} COINS"
                    color = GREEN if is_owned else WHITE
                    lbl = small.render(label, True, color)
                    win.blit(lbl, lbl.get_rect(center=(rect.centerx, rect.bottom + 18)))
                    # owned highlight
                    if is_owned:
                        pygame.draw.rect(win, GREEN, rect.inflate(6, 6), 2, border_radius=6)

            # Page controls
            left_rect = pygame.Rect(0, 0, 48, 48)
            right_rect = pygame.Rect(0, 0, 48, 48)
            left_rect.center = (WIDTH // 2 - 120, HEIGHT - 70)
            right_rect.center = (WIDTH // 2 + 120, HEIGHT - 70)
            pg_text = small.render(f"{page + 1}/{max(1, pages)}", True, WHITE)
            win.blit(pg_text, pg_text.get_rect(center=(WIDTH // 2, HEIGHT - 70)))
            # draw arrows with hover highlight
            left_hover = left_rect.collidepoint(mx, my)
            right_hover = right_rect.collidepoint(mx, my)
            left_color = HOVER if left_hover else (200, 200, 200)
            right_color = HOVER if right_hover else (200, 200, 200)
            pygame.draw.polygon(win, left_color, [(left_rect.centerx + 12, left_rect.centery - 14),
                                                  (left_rect.centerx - 12, left_rect.centery),
                                                  (left_rect.centerx + 12, left_rect.centery + 14)], 0)
            pygame.draw.polygon(win, right_color, [(right_rect.centerx - 12, right_rect.centery - 14),
                                                   (right_rect.centerx + 12, right_rect.centery),
                                                   (right_rect.centerx - 12, right_rect.centery + 14)], 0)

        # Modal overlay for selected ability
        if selected:
            overlay = pygame.Surface((WIDTH, HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 160))
            win.blit(overlay, (0, 0))
            panel = pygame.Rect(0, 0, 520, 320)
            panel.center = (WIDTH // 2, HEIGHT // 2)
            pygame.draw.rect(win, (30, 30, 30), panel, border_radius=10)
            pygame.draw.rect(win, (220, 220, 220), panel, 2, border_radius=10)
            title = font.render(selected["name"], True, GOLD)
            win.blit(title, title.get_rect(midtop=(panel.centerx, panel.top + 16)))
            # icon preview
            try:
                icon_fname = selected.get("_filename", "quantum_capacitor.png")  # используем сохранённое имя файла
                icon_img = pygame.image.load(os.path.join(icons_dir, icon_fname)).convert_alpha()
                icon_img = pygame.transform.smoothscale(icon_img, (96, 96))
                win.blit(icon_img, icon_img.get_rect(topleft=(panel.left + 24, panel.top + 60)))
            except Exception:
                pass
            # description (wrapped)
            desc = selected.get("desc", "")
            text_x = panel.left + 140
            # разместим описание чуть ниже строки с ценой/OWNED,
            # чтобы текст не перекрывался
            text_y = panel.top + 96
            maxw = panel.width - (text_x - panel.left) - 24
            for line in _wrap_text(desc, small, maxw):
                txt = small.render(line, True, WHITE)
                win.blit(txt, (text_x, text_y))
                text_y += txt.get_height() + 4
            # price / owned
            is_owned = purchases.get(selected["id"], False)
            price_text = "OWNED" if is_owned else f"Price: {selected['price']} COINS"
            price_color = GREEN if is_owned else WHITE
            win.blit(small.render(price_text, True, price_color), (panel.left + 140, panel.top + 60))
            # buy button
            buy_rect = pygame.Rect(0, 0, 160, 44)
            buy_rect.midbottom = (panel.centerx, panel.bottom - 24)
            buy_hover = buy_rect.collidepoint(mx, my)
            buy_color = (0, 180, 0) if buy_hover else (0, 140, 0)
            pygame.draw.rect(win, buy_color, buy_rect, border_radius=8)
            pygame.draw.rect(win, (220, 220, 220), buy_rect, 2, border_radius=8)
            btn_label = "Close" if is_owned else "Buy"
            lbl = font.render(btn_label, True, WHITE)
            win.blit(lbl, lbl.get_rect(center=buy_rect.center))

        # Back button
        back = font.render("BACK", True, WHITE)
        back_rect = back.get_rect(topleft=(20, HEIGHT - 70))
        back_hover = back_rect.collidepoint(mx, my)
        # draw back with hover color similar to menu buttons
        back_color = LIGHT_RED if back_hover else RED
        back = font.render("BACK", True, back_color)
        win.blit(back, back_rect)

        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "back"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if back_rect.collidepoint(mx, my):
                    return "back"
                # modal buy/close click
                if selected:
                    # compute buy rect again
                    buy_rect = pygame.Rect(0, 0, 160, 44)
                    buy_rect.midbottom = (WIDTH // 2, HEIGHT // 2 + 320//2 - 24)
                    if buy_rect.collidepoint(mx, my):
                        if purchases.get(selected["id"], False):
                            selected = None
                        else:
                            # price check (currently 0)
                            price = selected.get("price", 0)
                            if coins >= price:
                                coins -= price
                                try:
                                    with open("coins.txt", "w", encoding="utf-8") as f:
                                        f.write(str(coins))
                                except Exception:
                                    pass
                                purchases[selected["id"]] = True
                                _save_purchases(purchases)
                            selected = None
                # opening modal by clicking on ability icon
                elif icons:
                    start_index = page * per_page
                    end_index = min(len(icons), start_index + per_page)
                    for i in range(start_index, end_index):
                        col = (i - start_index) % cols
                        row = (i - start_index) // cols
                        x = start_x + col * gap_x
                        y = start_y + row * gap_y
                        rect = pygame.Rect(0, 0, 96, 96)
                        rect.center = (x, y)
                        if rect.collidepoint(mx, my):
                            fname, _img = icons[i]
                            if fname in ABILITIES:
                                selected = ABILITIES[fname].copy()
                                selected["_filename"] = fname  # сохраняем имя файла для иконки
                # arrows
                left_rect = pygame.Rect(0, 0, 40, 40); left_rect.center = (WIDTH // 2 - 120, HEIGHT - 70)
                right_rect = pygame.Rect(0, 0, 40, 40); right_rect.center = (WIDTH // 2 + 120, HEIGHT - 70)
                if icons and left_rect.collidepoint(mx, my) and pages > 1:
                    page = (page - 1) % pages
                elif icons and right_rect.collidepoint(mx, my) and pages > 1:
                    page = (page + 1) % pages
            # Keyboard arrows
            if event.type == pygame.KEYDOWN and icons and pages > 1:
                if event.key == pygame.K_LEFT:
                    page = (page - 1) % pages
                elif event.key == pygame.K_RIGHT:
                    page = (page + 1) % pages

        clock.tick(60)


