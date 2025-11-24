import pygame
import os

class FontCompat:
    def __init__(self, size, bold=False):
        try:
            self._mode = "font"
            self._font = pygame.font.SysFont("consolas", size, bold=bold)
        except Exception:
            # Fallback to freetype if pygame.font is unavailable in this env
            import pygame.freetype as ft
            ft.init()
            self._mode = "freetype"
            self._font = ft.SysFont("consolas", size)
            if bold:
                try:
                    self._font.style = ft.STYLE_STRONG
                except Exception:
                    pass

    def render(self, text, antialias, color):
        if self._mode == "font":
            return self._font.render(text, antialias, color)
        # pygame.freetype returns (surface, rect)
        surface, _ = self._font.render(text, color)
        return surface

FULLSCREEN = False

def _create_window(width, height):
    flags = pygame.FULLSCREEN if FULLSCREEN else 0
    win = pygame.display.set_mode((width, height), flags)
    pygame.display.set_caption("Main Menu")
    return win

def show_menu():
    global FULLSCREEN
    WIDTH, HEIGHT = 800, 600
    WIN = _create_window(WIDTH, HEIGHT)

    GRAY = (40, 40, 40)
    GREEN = (0, 200, 0)
    RED = (200, 0, 0)
    LIGHT_GREEN = (0, 255, 0)
    LIGHT_RED = (255, 80, 80)
    WHITE = (255, 255, 255)

    font = FontCompat(36)
    small_font = FontCompat(28)
    clock = pygame.time.Clock()

    # --- читаем рекорд ---
    if os.path.exists("top_score.txt"):
        with open("top_score.txt", "r") as f:
            top_score = f.read().strip()
            if not top_score.isdigit():
                top_score = "0"
    else:
        top_score = "0"

    while True:
        WIN.fill(GRAY)
        mx, my = pygame.mouse.get_pos()
        cur_w, cur_h = WIN.get_size()
        cx = cur_w // 2

        # Кнопка START
        start_color = LIGHT_GREEN if 300 < mx < 500 and 250 < my < 300 else GREEN
        start_text = font.render("START GAME", True, start_color)
        start_rect = start_text.get_rect(center=(cx, int(cur_h * 0.43)))

        # Кнопка SHOP
        shop_color = (255, 215, 0)
        shop_text = font.render("SHOP", True, shop_color)
        shop_rect = shop_text.get_rect(center=(cx, int(cur_h * 0.53)))

        # Кнопка FULLSCREEN TOGGLE
        fs_label = "Fullscreen: ON" if FULLSCREEN else "Fullscreen: OFF"
        fs_color = (180, 180, 255)
        fs_text = small_font.render(fs_label, True, fs_color)
        fs_rect = fs_text.get_rect(center=(cx, int(cur_h * 0.61)))

        # Кнопка EXIT
        exit_color = LIGHT_RED if 300 < mx < 500 and 350 < my < 400 else RED
        exit_text = font.render("EXIT", True, exit_color)
        exit_rect = exit_text.get_rect(center=(cx, int(cur_h * 0.70)))

        # Текст TOP SCORE
        score_text = small_font.render(f"Top Score: {top_score}", True, WHITE)
        score_rect = score_text.get_rect(center=(cx, int(cur_h * 0.80)))

        # Рисуем + белый контур при наведении
        def draw_with_hover(text_surf, rect):
            WIN.blit(text_surf, rect)
            if rect.collidepoint(mx, my):
                box = rect.inflate(24, 12)
                pygame.draw.rect(WIN, WHITE, box, 2, border_radius=6)

        draw_with_hover(start_text, start_rect)
        draw_with_hover(shop_text, shop_rect)
        draw_with_hover(fs_text, fs_rect)
        draw_with_hover(exit_text, exit_rect)
        WIN.blit(score_text, score_rect)
        pygame.display.flip()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "exit"
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_rect.collidepoint(mx, my):
                    return "start"
                elif shop_rect.collidepoint(mx, my):
                    return "shop"
                elif fs_rect.collidepoint(mx, my):
                    # переключаем флаг и пересоздаём окно
                    FULLSCREEN = not FULLSCREEN
                    WIN = _create_window(cur_w, cur_h)
                elif exit_rect.collidepoint(mx, my):
                    return "exit"

        clock.tick(60)