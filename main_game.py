import pygame
import math
import random
import os

class FontCompat:
    def __init__(self, size, bold=False):
        try:
            self._mode = "font"
            self._font = pygame.font.SysFont("consolas", size, bold=bold)
        except Exception:
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
        surface, _ = self._font.render(text, color)
        return surface

# ==============================
#         Настройки
# ==============================
WIDTH, HEIGHT = 800, 600
FPS = 60

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (200, 30, 30)
GREEN = (30, 200, 30)
YELLOW = (250, 250, 70)
GRAY = (40, 40, 40)

PLAYER_SPEED_BASE = 5
PLAYER_SPEED = PLAYER_SPEED_BASE
BULLET_SPEED = 10
ENEMY_SPEED = 2
SPAWN_INTERVAL = 1000  # мс
POWERUP_INTERVAL = 7000  # каждые 7 секунд шанс спавна бонуса
POWERUP_DURATION = 5000  # эффект длится 5 секунд
DIFFICULTY_INTERVAL = 10000  # каждые 10 сек сложность ↑
MAX_ENEMY_LEVEL = 15
PLAYER_ROT_OFFSET = 0  # базовый спрайт смотрит вверх; смещение не требуется
PLAYER_MUZZLE_DIST = 28  # пиксели вперёд от центра до "носа" корабля (в базовой ориентации)
USE_PROCEDURAL_STARFIELD = True  # включить качественный процедурный фон без артефактов скейлинга


# ==============================
#         Загрузчик ассетов
# ==============================
class Assets:
    _cache = {}

    @staticmethod
    def load_image(path, size=None):
        key = (path, size)
        if key in Assets._cache:
            return Assets._cache[key]
        img = pygame.image.load(path).convert_alpha()
        if size is not None:
            img = pygame.transform.smoothscale(img, size)
        Assets._cache[key] = img
        return img

    @staticmethod
    def game_dir():
        return os.path.dirname(os.path.abspath(__file__))

    @staticmethod
    def assets_dir():
        return os.path.join(Assets.game_dir(), "assets")

    @staticmethod
    def prepare_dir(path):
        os.makedirs(path, exist_ok=True)
        return path

    @staticmethod
    def prepare_assets():
        """
        Ensure local assets subfolders exist. No external references or copies.
        """
        Assets.prepare_dir(Assets.assets_dir())
        Assets.prepare_dir(os.path.join(Assets.assets_dir(), "player"))
        Assets.prepare_dir(os.path.join(Assets.assets_dir(), "enemies"))
        Assets.prepare_dir(os.path.join(Assets.assets_dir(), "explosions"))
        Assets.prepare_dir(os.path.join(Assets.assets_dir(), "lasers"))
        Assets.prepare_dir(os.path.join(Assets.assets_dir(), "backgrounds"))

    @staticmethod
    def player_base():
        # Only use file from assets
        return os.path.join(Assets.assets_dir(), "player", "Main Ship - Base - Full health.png")

    @staticmethod
    def player_damage_variants():
        """
        Return dict of health-state -> path if present in assets/player.
        Keys: 'full', 'slight', 'very', 'damaged'
        """
        base = os.path.join(Assets.assets_dir(), "player")
        candidates = {
            "full": "Main Ship - Base - Full health.png",
            "slight": "Main Ship - Base - Slight damage.png",
            "very": "Main Ship - Base - Very damaged.png",
            "damaged": "Main Ship - Base - Damaged.png",
        }
        result = {}
        for k, fname in candidates.items():
            p = os.path.join(base, fname)
            if os.path.exists(p):
                result[k] = p
        return result

    @staticmethod
    def background_image():
        """
        Path to chosen background under assets/backgrounds. Replace space.png if you want another.
        """
        return os.path.join(Assets.assets_dir(), "backgrounds", "space.png")

    @staticmethod
    def background_strip():
        """
        Optional spritesheet under assets/backgrounds/space_strip.png (e.g., 4 frames in a row).
        """
        return os.path.join(Assets.assets_dir(), "backgrounds", "space_strip.png")

    @staticmethod
    def bullet_auto():
        return os.path.join(
            Assets.game_dir(),
            "Foozle_2DS0011_Void_MainShip",
            "Main ship weapons",
            "PNGs",
            "Main ship weapon - Projectile - Auto cannon bullet.png",
        )

    @staticmethod
    def enemy_candidates():
        # Only use assets/enemies
        root = os.path.join(Assets.assets_dir(), "enemies")
        ships = []
        try:
            for name in os.listdir(root):
                if name.lower().endswith(".png"):
                    ships.append(os.path.join(root, name))
        except Exception:
            ships = []
        return ships

    @staticmethod
    def powerup_icons():
        shields = os.path.join(
            Assets.game_dir(),
            "Foozle_2DS0011_Void_MainShip",
            "Main Ship",
            "Main Ship - Shields",
            "PNGs",
        )
        engines_fx = os.path.join(
            Assets.game_dir(),
            "Foozle_2DS0011_Void_MainShip",
            "Main Ship",
            "Main Ship - Engine Effects",
            "PNGs",
        )
        icons = []
        for folder in (shields, engines_fx):
            try:
                icons.extend(
                    [os.path.join(folder, f) for f in os.listdir(folder) if f.lower().endswith(".png")]
                )
            except Exception:
                continue
        return icons

    @staticmethod
    def explosion_frame_paths():
        # Only use assets/explosions
        base = os.path.join(Assets.assets_dir(), "explosions")
        frames = []
        try:
            frames = [os.path.join(base, f) for f in sorted(os.listdir(base)) if f.lower().endswith(".png")]
        except Exception:
            frames = []
        return frames
    
    @staticmethod
    def shot_frame_paths():
        # Only use assets/lasers
        user_laser_dir = os.path.join(Assets.assets_dir(), "lasers")
        if os.path.isdir(user_laser_dir):
            try:
                files = [os.path.join(user_laser_dir, f) for f in os.listdir(user_laser_dir) if f.lower().endswith(".png")]
                def num_key(p):
                    name = os.path.splitext(os.path.basename(p))[0]
                    try:
                        return int(name)
                    except Exception:
                        return name
                files = sorted(files, key=num_key)
                if files:
                    return files
            except Exception:
                pass
        return []

    @staticmethod
    def beam_sprite_path():
        # Specific beam sprite requested by user
        return os.path.join(Assets.assets_dir(), "lasers", "03.png")

# ==============================
#         Классы
# ==============================

class Player(pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        # Load player damage variants (if present), scaled to ~50x50
        self.images_by_state = {}
        variants = Assets.player_damage_variants()
        for key, path in variants.items():
            try:
                self.images_by_state[key] = Assets.load_image(path, (50, 50))
            except Exception:
                pass
        # Fallback: at least full health image
        if "full" not in self.images_by_state:
            try:
                ship_path = Assets.player_base()
                self.images_by_state["full"] = Assets.load_image(ship_path, (50, 50))
            except Exception:
                surf = pygame.Surface((50, 50), pygame.SRCALPHA)
                pygame.draw.polygon(surf, (0, 180, 0), [(25, 0), (45, 45), (25, 35), (5, 45)])
                self.images_by_state["full"] = surf
        # Current base image depends on health
        self.base_image = self.images_by_state.get("full")

        self.image = self.base_image.copy()
        self.rect = self.image.get_rect(center=(x, y))
        self.pos = pygame.Vector2(x, y)
        self.health = 100
        self.last_angle_deg = 0
        self.muzzle_pos = (x, y)

    def _select_base_image_for_health(self):
        # Thresholds: >70 full, >40 slight, >20 very, else damaged
        if self.health > 70:
            return self.images_by_state.get("full", self.base_image)
        if self.health > 40:
            return self.images_by_state.get("slight", self.images_by_state.get("full", self.base_image))
        if self.health > 20:
            return self.images_by_state.get("very", self.images_by_state.get("slight", self.images_by_state.get("full", self.base_image)))
        return self.images_by_state.get("damaged", self.images_by_state.get("very", self.images_by_state.get("slight", self.images_by_state.get("full", self.base_image))))

    def update(self, keys):
        move = pygame.Vector2(0, 0)
        if keys[pygame.K_w]:
            move.y -= 1
        if keys[pygame.K_s]:
            move.y += 1
        if keys[pygame.K_a]:
            move.x -= 1
        if keys[pygame.K_d]:
            move.x += 1

        if move.length_squared() > 0:
            move = move.normalize() * PLAYER_SPEED
            self.pos += move

        self.pos.x = max(25, min(WIDTH - 25, self.pos.x))
        self.pos.y = max(25, min(HEIGHT - 25, self.pos.y))

        mx, my = pygame.mouse.get_pos()
        # Перед поворотом выберем базовый спрайт под текущее HP
        self.base_image = self._select_base_image_for_health()
        # Математический угол (0° вправо, +90° вниз из-за экранных координат)
        dx, dy = mx - self.pos.x, my - self.pos.y
        angle_math = math.degrees(math.atan2(dy, dx))
        # Для спрайта, который изначально "смотрит вверх"
        angle = -angle_math - 90 + PLAYER_ROT_OFFSET
        rotated_image = pygame.transform.rotate(self.base_image, angle)
        rect = rotated_image.get_rect(center=self.pos)
        self.image = rotated_image
        self.rect = rect
        self.last_angle_deg = angle
        # больше не используем привязку к локальной геометрии — спавним по вектору направления
        self.muzzle_pos = (self.pos.x, self.pos.y)


class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        # Animated laser frames if available
        if not hasattr(Bullet, "_frames_cache"):
            Bullet._frames_cache = None
        if Bullet._frames_cache is None:
            paths = Assets.shot_frame_paths()
            if paths:
                try:
                    # Load base frames un-rotated; we'll rotate per tick to aim at target
                    Bullet._frames_cache = [Assets.load_image(p, (8, 24)) for p in paths]
                except Exception:
                    Bullet._frames_cache = []
            else:
                Bullet._frames_cache = []

        if Bullet._frames_cache:
            self.frames = Bullet._frames_cache
            self.frame_index = 0
            self.timer = 0
            self.frame_delay = 2  # faster flicker for laser look
            self.angle = angle
            base = pygame.transform.rotate(self.frames[0], self._pygame_angle(self.angle))
            self.image = base.copy()
            self.half_len = 12
        else:
            # Fallback: simple rectangle bullet
            self.frames = None
            self.image = pygame.Surface((6, 16), pygame.SRCALPHA)
            pygame.draw.rect(self.image, (255, 255, 100), (0, 0, 6, 12))
            pygame.draw.rect(self.image, (255, 255, 255, 80), (0, 10, 6, 6))
            self.half_len = 8

        # Сместим центр спрайта назад, чтобы точка спавна совпадала с "носом" пули
        a = math.radians(angle)
        sina = math.sin(a)
        cosa = math.cos(a)
        # Если "нос" пули находится в верхней части исходного спрайта (mid-top),
        # то вектор от центра к носу в локальных координатах (0, -half_len).
        # После поворота: (dx, dy) = (half_len * sin(a), -half_len * cos(a))
        # Центр = точка_носа - (dx, dy).
        cx = x - (self.half_len * sina)
        cy = y + (self.half_len * cosa)
        self.rect = self.image.get_rect(center=(cx, cy))
        self.vx = math.cos(math.radians(angle)) * BULLET_SPEED
        self.vy = math.sin(math.radians(angle)) * BULLET_SPEED
        self.angle = angle
        self.charged = False

    def _pygame_angle(self, angle_deg):
        # Our frames are vertical; rotate so that 0 deg faces right in pygame => add 90 offset
        # We want bullet to point towards mouse; our velocity uses math angle (0 to right, 90 up)
        return -angle_deg + 90

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if self.frames:
            self.timer += 1
            if self.timer >= self.frame_delay:
                self.timer = 0
                self.frame_index = (self.frame_index + 1) % len(self.frames)
                base = pygame.transform.rotate(self.frames[self.frame_index], self._pygame_angle(self.angle))
                if self.charged:
                    # overlay green tint for charged bullets
                    overlay = pygame.Surface(base.get_size(), pygame.SRCALPHA)
                    overlay.fill((0, 255, 120, 100))
                    base.blit(overlay, (0, 0), special_flags=pygame.BLEND_PREMULTIPLIED)
                self.image = base
        if not pygame.Rect(0, 0, WIDTH, HEIGHT).collidepoint(self.rect.center):
            self.kill()

class BeamBullet(pygame.sprite.Sprite):
    def __init__(self, x, y, angle):
        super().__init__()
        BEAM_LATERAL_OFFSET = -6  # сместим чуть влево относительно направления, чтобы выйти строго из носа
        path = Assets.beam_sprite_path()
        try:
            base = Assets.load_image(path)
        except Exception:
            base = pygame.Surface((12, 48), pygame.SRCALPHA)
            pygame.draw.rect(base, (150, 220, 255), (4, 0, 4, 48))
        # scale 5x relative to обычного снаряда (~8x24)
        scaled = pygame.transform.smoothscale(base, (40, 120))
        rotated = pygame.transform.rotate(scaled, -angle + 90)
        self.image = rotated
        a = math.radians(angle)
        sina = math.sin(a); cosa = math.cos(a)
        half_len = 60
        # точка центра: от носа назад на половину длины луча
        cx = x - half_len * cosa
        cy = y - half_len * sina
        # поперечная поправка "влево" к направлению (перпендикуляр)
        px = -sina
        py =  cosa
        cx += px * BEAM_LATERAL_OFFSET
        cy += py * BEAM_LATERAL_OFFSET
        self.rect = self.image.get_rect(center=(cx, cy))
        speed = BULLET_SPEED * 2.2
        # скорость — вдоль направления
        self.vx =  cosa * speed
        self.vy =  sina * speed
        self.pierce = 999  # goes through many enemies

    def update(self):
        self.rect.x += self.vx
        self.rect.y += self.vy
        if not pygame.Rect(0, 0, WIDTH, HEIGHT).collidepoint(self.rect.center):
            self.kill()


class Enemy(pygame.sprite.Sprite):
    def __init__(self, level=1):
        super().__init__()
        self.level = level
        # Use enemy ship PNGs from the new pack
        try:
            candidate = random.choice(Assets.enemy_candidates())
            self.image = Assets.load_image(candidate, (40, 40))
        except Exception:
            self.image = pygame.Surface((40, 40), pygame.SRCALPHA)

        self.rect = self.image.get_rect()
        side = random.choice(['top', 'bottom', 'left', 'right'])
        if side == 'top':
            self.rect.center = (random.randint(0, WIDTH), -20)
        elif side == 'bottom':
            self.rect.center = (random.randint(0, WIDTH), HEIGHT + 20)
        elif side == 'left':
            self.rect.center = (-20, random.randint(0, HEIGHT))
        else:
            self.rect.center = (WIDTH + 20, random.randint(0, HEIGHT))

    def update(self, player):
        px, py = player.rect.center
        ex, ey = self.rect.center
        angle = math.atan2(py - ey, px - ex)
        self.rect.x += math.cos(angle) * ENEMY_SPEED
        self.rect.y += math.sin(angle) * ENEMY_SPEED


class PowerUp(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        self.type = random.choice(["speed", "autofire", "heal"])
        self.image = pygame.Surface((30, 30), pygame.SRCALPHA)

        if self.type == "speed":
            pygame.draw.circle(self.image, (0, 200, 255), (15, 15), 13)
            pygame.draw.polygon(self.image, (255, 255, 255),
                                [(10, 8), (20, 8), (20, 15), (25, 15), (15, 25), (15, 18), (10, 18)])
        elif self.type == "autofire":
            pygame.draw.circle(self.image, (255, 220, 0), (15, 15), 13)
            pygame.draw.rect(self.image, (255, 255, 255), (8, 12, 14, 6))
            pygame.draw.rect(self.image, (255, 255, 255), (14, 6, 3, 20))
        elif self.type == "heal":
            pygame.draw.circle(self.image, (0, 220, 0), (15, 15), 13)
            pygame.draw.rect(self.image, (255, 255, 255), (13, 6, 4, 18))
            pygame.draw.rect(self.image, (255, 255, 255), (6, 13, 18, 4))

        self.rect = self.image.get_rect(center=(random.randint(50, WIDTH - 50),
                                                random.randint(50, HEIGHT - 50)))

    def update(self):
        pass


class Flash(pygame.sprite.Sprite):
    """Вспышка при подборе бонуса"""
    def __init__(self, pos):
        super().__init__()
        self.image = pygame.Surface((100, 100), pygame.SRCALPHA)
        self.rect = self.image.get_rect(center=pos)
        self.radius = 10
        self.life = 15  # кадров

    def update(self):
        self.life -= 1
        self.radius += 8
        alpha = max(0, int(255 * (self.life / 15)))
        self.image.fill((0, 0, 0, 0))
        pygame.draw.circle(self.image, (255, 255, 255, alpha), (50, 50), self.radius)
        if self.life <= 0:
            self.kill()


class Explosion(pygame.sprite.Sprite):
    """Анимация взрыва при уничтожении врага"""
    _frames_cache = None

    def __init__(self, pos, size=(48, 48), fps=18):
        super().__init__()
        if Explosion._frames_cache is None:
            paths = Assets.explosion_frame_paths()
            if paths:
                try:
                    Explosion._frames_cache = [Assets.load_image(p, size) for p in paths]
                except Exception:
                    Explosion._frames_cache = []
            else:
                Explosion._frames_cache = []
        self.frames = Explosion._frames_cache
        if not self.frames:
            # Fallback simple white flash if no frames available
            surf = pygame.Surface(size, pygame.SRCALPHA)
            pygame.draw.circle(surf, (255, 255, 255, 200), (size[0] // 2, size[1] // 2), min(size) // 2)
            self.frames = [surf] * 8
        self.frame_index = 0
        self.timer = 0
        self.frame_delay = max(1, int(60 / fps))  # in ticks at 60 FPS
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=pos)

    def update(self):
        self.timer += 1
        if self.timer >= self.frame_delay:
            self.timer = 0
            self.frame_index += 1
            if self.frame_index >= len(self.frames):
                self.kill()
                return
            self.image = self.frames[self.frame_index]


class Starfield:
    """Простой, но качественный процедурный фон: параллакс-слои звёзд без масштабирования текстур"""
    def __init__(self, width, height, layers=3, density_per_100px=0.8):
        self.width = width
        self.height = height
        self.layers = []
        rng = random.Random(42)
        # для каждого слоя — различная скорость и размер
        for i in range(layers):
            speed = 0.3 + i * 0.5
            radius = 1 + i  # 1,2,3 px
            alpha = 140 + i * 40
            num_stars = int(density_per_100px * (width * height) / 10000 * (0.6 + i * 0.6))
            stars = []
            for _ in range(num_stars):
                x = rng.uniform(0, width)
                y = rng.uniform(0, height)
                twinkle_phase = rng.uniform(0, 2 * math.pi)
                stars.append([x, y, twinkle_phase])
            self.layers.append({
                "speed": speed,
                "radius": radius,
                "alpha": alpha,
                "stars": stars,
            })
        # подготовим поверхности для слоёв для более дешёвого рендера
        self.layer_surfaces = [pygame.Surface((width, height), pygame.SRCALPHA) for _ in self.layers]

    def update(self, dt_ms):
        for idx, layer in enumerate(self.layers):
            spd = layer["speed"] * (dt_ms / 16.666)  # нормируем к ~60 FPS
            for star in layer["stars"]:
                star[1] += spd
                if star[1] > self.height:
                    star[0] = (star[0] + random.uniform(-20, 20)) % self.width
                    star[1] -= self.height
                star[2] += 0.05  # твинг
            # перерисуем слой на буфер
            surf = self.layer_surfaces[idx]
            surf.fill((0, 0, 0, 0))
            r = layer["radius"]
            base_alpha = layer["alpha"]
            for x, y, phase in layer["stars"]:
                a = base_alpha + int(40 * math.sin(phase))
                a = max(60, min(255, a))
                pygame.draw.circle(surf, (255, 255, 255, a), (int(x), int(y)), r)

    def render(self, target):
        # лёгкий параллакс — задние слои рисуем первыми
        for surf in self.layer_surfaces:
            target.blit(surf, (0, 0))


# ==============================
#         Интерфейс
# ==============================

def draw_ui(win, player, score, font, powerup_active, enemy_level):
    pygame.draw.rect(win, RED, (10, 10, 200, 20))
    pygame.draw.rect(win, GREEN, (10, 10, 2 * player.health, 20))
    text = font.render(f"HP: {player.health}   SCORE: {score}", True, WHITE)
    win.blit(text, (10, 40))
    if powerup_active:
        p_text = font.render(f"Power-Up: {powerup_active.upper()}", True, (100, 200, 255))
        win.blit(p_text, (10, 70))
    lvl_text = font.render(f"Enemy Level: {enemy_level}", True, (255, 200, 200))
    win.blit(lvl_text, (WIDTH - 230, 10))

def draw_beam_charge(win, progress):
    # progress: 0..1, draw at bottom center, filling bottom->top
    bar_w, bar_h = 28, 80
    x = WIDTH // 2 - bar_w // 2
    y = HEIGHT - bar_h - 12
    # outline
    pygame.draw.rect(win, (220, 220, 220), (x, y, bar_w, bar_h), 2, border_radius=6)
    # fill
    clamped = max(0.0, min(1.0, progress))
    fill_h = int((bar_h - 4) * clamped)
    fill_rect = pygame.Rect(x + 2, y + (bar_h - 2 - fill_h), bar_w - 4, fill_h)
    pygame.draw.rect(win, (0, 255, 140), fill_rect, border_radius=4)


# ==============================
#         Основная игра
# ==============================

def main(fullscreen=False, purchases=None):
    global PLAYER_SPEED
    global PLAYER_ROT_OFFSET
    # Ensure game assets are prepared into ./assets on first run
    Assets.prepare_assets()
    flags = pygame.FULLSCREEN if fullscreen else 0
    win = pygame.display.set_mode((WIDTH, HEIGHT), flags)
    clock = pygame.time.Clock()
    font = FontCompat(24)
    # Background setup
    starfield = None
    # Если пользователь хочет процедурный фон — включаем его.
    if USE_PROCEDURAL_STARFIELD:
        starfield = Starfield(WIDTH, HEIGHT, layers=3, density_per_100px=0.9)
    else:
        # Load background: prefer animated spritesheet if present, otherwise static
        bg_path = Assets.background_image()
        bg_strip_path = Assets.background_strip()
        background = None
        bg_frames = None
        bg_frame_index = 0
        bg_timer = 0
        bg_frame_delay = int(60 / 6)  # ~6 FPS
        try:
            if os.path.exists(bg_strip_path):
                sheet = pygame.image.load(bg_strip_path).convert()
                sw, sh = sheet.get_width(), sheet.get_height()
                # Assume 4 frames horizontally if divisible; otherwise fall back to static
                frames_count = 4 if sw % 4 == 0 else 0
                if frames_count:
                    fw = sw // frames_count
                    bg_frames = []
                    for i in range(frames_count):
                        frame = pygame.Surface((fw, sh)).convert()
                        frame.blit(sheet, (0, 0), (i * fw, 0, fw, sh))
                        bg_frames.append(pygame.transform.smoothscale(frame, (WIDTH, HEIGHT)))
            if bg_frames is None and os.path.exists(bg_path):
                background = pygame.transform.smoothscale(pygame.image.load(bg_path).convert(), (WIDTH, HEIGHT))
        except Exception:
            background = None

    player = Player(WIDTH // 2, HEIGHT // 2)
    all_sprites = pygame.sprite.Group()
    bullets = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    powerups = pygame.sprite.Group()
    flashes = pygame.sprite.Group()
    explosions = pygame.sprite.Group()
    all_sprites.add(player)

    score = 0
    last_spawn = pygame.time.get_ticks()
    last_powerup_spawn = pygame.time.get_ticks()
    last_difficulty_increase = pygame.time.get_ticks()
    powerup_active = None
    powerup_end_time = 0
    autofire = False
    enemy_level = 1

    # Ability flags
    purchases = purchases or {}
    quantum_enabled = purchases.get("quantum_capacitor", False)
    beam_idle_start = None
    beam_ready = False
    BEAM_IDLE_MS = 5000

    running = True
    while running:
        clock.tick(FPS)
        keys = pygame.key.get_pressed()
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"

        # Beam charge while idle (no movement, no shooting)
        if quantum_enabled:
            # Считаем движением только WASD
            is_moving = any((keys[pygame.K_w], keys[pygame.K_a], keys[pygame.K_s], keys[pygame.K_d]))
            if is_moving:
                # движение сбрасывает заряд и таймер
                beam_ready = False
                beam_idle_start = None
            else:
                # стоим — копим заряд, и если заряд уже готов, держим его пока не начнём двигаться
                if not beam_ready:
                    if beam_idle_start is None:
                        beam_idle_start = now
                    elif now - beam_idle_start >= BEAM_IDLE_MS:
                        beam_ready = True
                        flashes.add(Flash(player.rect.center))
                        all_sprites.add(list(flashes)[-1])

        # стрельба
        mouse_pressed = pygame.mouse.get_pressed()[0]
        if mouse_pressed or (autofire and pygame.mouse.get_focused()):
            if now % 200 < 20:
                mx, my = pygame.mouse.get_pos()
                angle = math.degrees(math.atan2(my - player.rect.centery, mx - player.rect.centerx))
                # спавним пулю у "носа" корабля по направлению выстрела (независимо от поворота спрайта)
                ux = math.cos(math.radians(angle))
                uy = math.sin(math.radians(angle))
                spawn_x = player.rect.centerx + ux * PLAYER_MUZZLE_DIST
                spawn_y = player.rect.centery + uy * PLAYER_MUZZLE_DIST
                if quantum_enabled and beam_ready:
                    # Заряженный режим: все выстрелы — луч до начала движения
                    beam = BeamBullet(spawn_x, spawn_y, angle)
                    all_sprites.add(beam)
                    bullets.add(beam)
                else:
                    bullet = Bullet(spawn_x, spawn_y, angle)
                    all_sprites.add(bullet)
                    bullets.add(bullet)

        # спавн врагов
        if now - last_spawn > SPAWN_INTERVAL:
            enemy = Enemy(level=enemy_level)
            all_sprites.add(enemy)
            enemies.add(enemy)
            last_spawn = now

        # рост сложности
        if now - last_difficulty_increase > DIFFICULTY_INTERVAL and enemy_level < MAX_ENEMY_LEVEL:
            enemy_level += 1
            last_difficulty_increase = now

        # спавн бонусов
        if now - last_powerup_spawn > POWERUP_INTERVAL and len(powerups) < 3:
            if random.random() < 0.6:
                pu = PowerUp()
                all_sprites.add(pu)
                powerups.add(pu)
            last_powerup_spawn = now

        # обновления
        player.update(keys)
        bullets.update()
        enemies.update(player)
        flashes.update()
        explosions.update()

        # попадания по врагам
        for bullet in list(bullets):
            hit_list = pygame.sprite.spritecollide(bullet, enemies, False)
            for e in hit_list:
                boom = Explosion(e.rect.center)
                all_sprites.add(boom)
                explosions.add(boom)
                e.kill()
                score += 10 + enemy_level * 5
                if hasattr(bullet, "pierce") and bullet.pierce > 0:
                    bullet.pierce -= 1
                else:
                    bullet.kill()
                    break

        # столкновение с игроком
        hits = pygame.sprite.spritecollide(player, enemies, True)
        for enemy in hits:
            boom = Explosion(enemy.rect.center, size=(40, 40), fps=18)
            all_sprites.add(boom)
            explosions.add(boom)
            player.health -= 10 + enemy_level * 2  # урон растёт с уровнем
            if player.health <= 0:
                running = False

        # подбор бонусов
        got = pygame.sprite.spritecollide(player, powerups, True)
        for p in got:
            powerup_active = p.type
            powerup_end_time = now + POWERUP_DURATION
            flash = Flash(p.rect.center)
            all_sprites.add(flash)
            flashes.add(flash)

            if p.type == "heal":
                player.health = min(100, player.health + 25)
            elif p.type == "speed":
                PLAYER_SPEED = 8
            elif p.type == "autofire":
                autofire = True

        # сброс эффектов
        if powerup_active and now > powerup_end_time:
            powerup_active = None
            PLAYER_SPEED = PLAYER_SPEED_BASE
            autofire = False

        # рендер
        if starfield:
            # обновляем с учётом прошедшего времени
            starfield.update(clock.get_time())
            # очищаем весь кадр перед отрисовкой звёзд, иначе будет "смазывание"
            win.fill((0, 0, 0))
            starfield.render(win)
        elif 'bg_frames' in locals() and bg_frames:
            bg_timer += 1
            if bg_timer >= bg_frame_delay:
                bg_timer = 0
                bg_frame_index = (bg_frame_index + 1) % len(bg_frames)
            win.blit(bg_frames[bg_frame_index], (0, 0))
        elif 'background' in locals() and background:
            win.blit(background, (0, 0))
        else:
            win.fill(GRAY)
        all_sprites.draw(win)
        draw_ui(win, player, score, font, powerup_active, enemy_level)
        # draw charge indicator
        if quantum_enabled:
            if beam_ready:
                draw_beam_charge(win, 1.0)
            else:
                prog = 0.0
                if beam_idle_start is not None:
                    prog = max(0.0, min(1.0, (now - beam_idle_start) / BEAM_IDLE_MS))
                draw_beam_charge(win, prog)
        pygame.display.flip()

    # экран конца игры
    win.fill(BLACK)
    title_font = FontCompat(64, bold=True)
    small_font = FontCompat(32)
    game_over_text = title_font.render("GAME OVER", True, RED)
    score_text = small_font.render(f"Score: {score}", True, WHITE)
    tip_text = small_font.render("Returning to menu...", True, (180, 180, 180))
    win.blit(game_over_text, game_over_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 - 40)))
    win.blit(score_text, score_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 20)))
    win.blit(tip_text, tip_text.get_rect(center=(WIDTH // 2, HEIGHT // 2 + 70)))
    pygame.display.flip()
    pygame.time.wait(2500)

    # сохранение рекорда
    try:
        with open("top_score.txt", "r") as f:
            best = int(f.read().strip() or 0)
    except FileNotFoundError:
        best = 0
    if score > best:
        with open("top_score.txt", "w") as f:
            f.write(str(score))

    return "game_over"