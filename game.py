import random
import sys

import pygame


WIDTH, HEIGHT = 1100, 620
GROUND_Y = HEIGHT - 110
FPS = 60

PLAYER_X = 200
HORSE_WIDTH = 140
HORSE_HEIGHT = 58
COWBOY_HEIGHT = 86

BULLET_COOLDOWN_MS = 170
ENEMY_SPAWN_MS = 800
ENEMY_MIN_SPEED = 180
ENEMY_MAX_SPEED = 280

SKY = (255, 207, 123)
SAND = (230, 181, 84)
DUNE = (214, 162, 74)
SUN = (255, 244, 178)
PLAYER_COLOR = (58, 40, 27)
HORSE_COLOR = (118, 71, 30)
ENEMY_COLOR = (40, 100, 34)
BULLET_COLOR = (255, 249, 238)
TEXT_COLOR = (43, 30, 20)


class Enemy:
    def __init__(self):
        self.width = 44
        self.height = 62
        self.x = WIDTH + random.randint(0, 250)
        self.y = GROUND_Y - self.height
        self.speed = random.uniform(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED)

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.width, self.height)

    @property
    def center(self):
        r = self.rect
        return pygame.Vector2(r.centerx, r.centery)

    def update(self, dt):
        self.x -= self.speed * dt

    def draw(self, surface):
        body = self.rect
        pygame.draw.rect(surface, ENEMY_COLOR, body, border_radius=8)
        pygame.draw.rect(surface, (28, 64, 21), (body.x, body.y - 10, body.w, 10), border_radius=4)


def draw_desert(surface, t):
    surface.fill(SKY)
    pygame.draw.circle(surface, SUN, (920, 90), 48)

    dune_offset = int((t * 30) % WIDTH)
    for i in range(-1, 3):
        x = i * WIDTH // 2 - dune_offset
        pygame.draw.ellipse(surface, DUNE, (x, GROUND_Y - 90, WIDTH // 2 + 100, 150))

    pygame.draw.rect(surface, SAND, (0, GROUND_Y, WIDTH, HEIGHT - GROUND_Y))


def draw_player(surface, mouse_pos):
    horse_rect = pygame.Rect(PLAYER_X - 50, GROUND_Y - HORSE_HEIGHT + 8, HORSE_WIDTH, HORSE_HEIGHT)
    pygame.draw.ellipse(surface, HORSE_COLOR, horse_rect)

    cowboy_x = PLAYER_X + 10
    cowboy_y = GROUND_Y - HORSE_HEIGHT - COWBOY_HEIGHT + 20

    torso = pygame.Rect(cowboy_x, cowboy_y + 28, 32, 42)
    head = pygame.Rect(cowboy_x + 4, cowboy_y, 24, 24)

    pygame.draw.rect(surface, PLAYER_COLOR, torso, border_radius=6)
    pygame.draw.ellipse(surface, PLAYER_COLOR, head)
    pygame.draw.rect(surface, (40, 24, 17), (cowboy_x - 2, cowboy_y - 4, 38, 6), border_radius=3)

    shoulder = pygame.Vector2(cowboy_x + 28, cowboy_y + 40)
    aim = pygame.Vector2(mouse_pos) - shoulder
    if aim.length_squared() < 0.001:
        aim = pygame.Vector2(1, 0)
    else:
        aim = aim.normalize()

    muzzle = shoulder + aim * 48
    pygame.draw.line(surface, (34, 22, 18), shoulder, muzzle, 6)

    return shoulder, muzzle


def distance_point_to_segment(p, a, b):
    ap = p - a
    ab = b - a
    ab_len_sq = ab.length_squared()
    if ab_len_sq == 0:
        return ap.length()

    t = max(0, min(1, ap.dot(ab) / ab_len_sq))
    closest = a + ab * t
    return (p - closest).length()


def fire_shot(enemies, start, direction):
    end = start + direction * 1500
    target = None
    closest_proj = float("inf")

    for enemy in enemies:
        center = enemy.center
        to_enemy = center - start
        projection = to_enemy.dot(direction)
        if projection < 0:
            continue

        miss_distance = distance_point_to_segment(center, start, end)
        if miss_distance <= enemy.width * 0.5 and projection < closest_proj:
            target = enemy
            closest_proj = projection

    if target is not None:
        enemies.remove(target)
        return True
    return False


def main():
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Cowboy Desert Run")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 28)

    enemies = []
    score = 0

    last_shot_time = 0
    shot_flash_ms = 0
    last_spawn_time = pygame.time.get_ticks()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0
        now = pygame.time.get_ticks()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if now - last_shot_time >= BULLET_COOLDOWN_MS:
                    shoulder = pygame.Vector2(PLAYER_X + 38, GROUND_Y - HORSE_HEIGHT - COWBOY_HEIGHT + 60)
                    mouse = pygame.Vector2(pygame.mouse.get_pos())
                    direction = mouse - shoulder
                    if direction.length_squared() > 0.001:
                        direction = direction.normalize()
                        if fire_shot(enemies, shoulder, direction):
                            score += 1
                        last_shot_time = now
                        shot_flash_ms = 45

        if now - last_spawn_time >= ENEMY_SPAWN_MS:
            enemies.append(Enemy())
            last_spawn_time = now

        for enemy in enemies[:]:
            enemy.update(dt)
            if enemy.x + enemy.width < -40:
                enemies.remove(enemy)

        draw_desert(screen, now / 1000.0)
        shoulder, muzzle = draw_player(screen, pygame.mouse.get_pos())

        for enemy in enemies:
            enemy.draw(screen)

        if shot_flash_ms > 0:
            flash_dir = pygame.Vector2(pygame.mouse.get_pos()) - shoulder
            if flash_dir.length_squared() < 0.001:
                flash_dir = pygame.Vector2(1, 0)
            else:
                flash_dir = flash_dir.normalize()
            flash_end = muzzle + flash_dir * 26
            pygame.draw.line(screen, BULLET_COLOR, muzzle, flash_end, 3)
            shot_flash_ms -= int(dt * 1000)

        score_text = font.render(f"Score: {score}", True, TEXT_COLOR)
        help_text = font.render("Mouse to aim • Left click to shoot", True, TEXT_COLOR)
        screen.blit(score_text, (18, 16))
        screen.blit(help_text, (18, 48))

        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
