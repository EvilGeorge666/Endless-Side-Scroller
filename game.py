import random
import sys
import time
import tkinter as tk
from dataclasses import dataclass


WIDTH, HEIGHT = 1100, 620
GROUND_Y = HEIGHT - 110
FPS = 60
FRAME_MS = int(1000 / FPS)

PLAYER_X = 200
HORSE_WIDTH = 140
HORSE_HEIGHT = 58
COWBOY_HEIGHT = 86

BULLET_COOLDOWN_MS = 170
ENEMY_SPAWN_MS = 800
ENEMY_MIN_SPEED = 180
ENEMY_MAX_SPEED = 280

SKY = "#ffcf7b"
SAND = "#e6b554"
DUNE = "#d6a24a"
SUN = "#fff4b2"
PLAYER_COLOR = "#3a281b"
HORSE_COLOR = "#76471e"
ENEMY_COLOR = "#286422"
ENEMY_HAT = "#1c4015"
BULLET_COLOR = "#fff9ee"
TEXT_COLOR = "#2b1e14"


@dataclass
class Enemy:
    x: float
    y: float
    speed: float
    width: int = 44
    height: int = 62

    @classmethod
    def spawn(cls):
        return cls(
            x=WIDTH + random.randint(0, 250),
            y=GROUND_Y - 62,
            speed=random.uniform(ENEMY_MIN_SPEED, ENEMY_MAX_SPEED),
        )

    @property
    def center(self):
        return (self.x + self.width / 2, self.y + self.height / 2)


def v_sub(a, b):
    return (a[0] - b[0], a[1] - b[1])


def v_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


def v_mul(a, scalar):
    return (a[0] * scalar, a[1] * scalar)


def v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1]


def v_len_sq(a):
    return a[0] * a[0] + a[1] * a[1]


def v_len(a):
    return v_len_sq(a) ** 0.5


def v_norm(a):
    l = v_len(a)
    if l < 0.0001:
        return (1.0, 0.0)
    return (a[0] / l, a[1] / l)


def distance_point_to_segment(p, a, b):
    ap = v_sub(p, a)
    ab = v_sub(b, a)
    ab_len_sq = v_len_sq(ab)
    if ab_len_sq == 0:
        return v_len(ap)
    t = max(0.0, min(1.0, v_dot(ap, ab) / ab_len_sq))
    closest = v_add(a, v_mul(ab, t))
    return v_len(v_sub(p, closest))


class Game:
    def __init__(self, root):
        self.root = root
        self.root.title("Cowboy Desert Run")
        self.canvas = tk.Canvas(root, width=WIDTH, height=HEIGHT, bg=SKY, highlightthickness=0)
        self.canvas.pack()

        self.enemies = []
        self.score = 0

        self.last_shot_time = 0
        self.shot_flash_ms = 0
        self.last_spawn_time = 0

        self.mouse_pos = (WIDTH // 2, HEIGHT // 2)
        self.running = True
        self.last_frame_time = time.perf_counter()

        self.canvas.bind("<Motion>", self.on_mouse_move)
        self.canvas.bind("<Button-1>", self.on_click)
        self.root.bind("<Escape>", lambda _e: self.close())
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.canvas.focus_set()

    def now_ms(self):
        return int(time.perf_counter() * 1000)

    def on_mouse_move(self, event):
        self.mouse_pos = (event.x, event.y)

    def on_click(self, _event):
        now = self.now_ms()
        if now - self.last_shot_time < BULLET_COOLDOWN_MS:
            return

        shoulder = (PLAYER_X + 38, GROUND_Y - HORSE_HEIGHT - COWBOY_HEIGHT + 60)
        direction = v_norm(v_sub(self.mouse_pos, shoulder))

        if self.fire_shot(shoulder, direction):
            self.score += 1
        self.last_shot_time = now
        self.shot_flash_ms = 45

    def fire_shot(self, start, direction):
        end = v_add(start, v_mul(direction, 1500))
        target_index = -1
        closest_proj = float("inf")

        for i, enemy in enumerate(self.enemies):
            center = enemy.center
            to_enemy = v_sub(center, start)
            projection = v_dot(to_enemy, direction)
            if projection < 0:
                continue

            miss_distance = distance_point_to_segment(center, start, end)
            if miss_distance <= enemy.width * 0.5 and projection < closest_proj:
                target_index = i
                closest_proj = projection

        if target_index >= 0:
            self.enemies.pop(target_index)
            return True
        return False

    def update(self, dt):
        now = self.now_ms()
        if now - self.last_spawn_time >= ENEMY_SPAWN_MS:
            self.enemies.append(Enemy.spawn())
            self.last_spawn_time = now

        survivors = []
        for enemy in self.enemies:
            enemy.x -= enemy.speed * dt
            if enemy.x + enemy.width >= -40:
                survivors.append(enemy)
        self.enemies = survivors

        if self.shot_flash_ms > 0:
            self.shot_flash_ms -= int(dt * 1000)

    def draw(self):
        c = self.canvas
        c.delete("all")

        c.create_rectangle(0, 0, WIDTH, HEIGHT, fill=SKY, outline="")
        c.create_oval(920 - 48, 90 - 48, 920 + 48, 90 + 48, fill=SUN, outline="")

        dune_offset = int((time.perf_counter() * 30) % WIDTH)
        for i in range(-1, 3):
            x = i * WIDTH // 2 - dune_offset
            c.create_oval(x, GROUND_Y - 90, x + WIDTH // 2 + 100, GROUND_Y + 60, fill=DUNE, outline="")

        c.create_rectangle(0, GROUND_Y, WIDTH, HEIGHT, fill=SAND, outline="")

        shoulder, muzzle = self.draw_player()
        for enemy in self.enemies:
            c.create_rectangle(enemy.x, enemy.y, enemy.x + enemy.width, enemy.y + enemy.height, fill=ENEMY_COLOR, outline="", width=0)
            c.create_rectangle(enemy.x, enemy.y - 10, enemy.x + enemy.width, enemy.y, fill=ENEMY_HAT, outline="")

        if self.shot_flash_ms > 0:
            flash_dir = v_norm(v_sub(self.mouse_pos, shoulder))
            flash_end = v_add(muzzle, v_mul(flash_dir, 26))
            c.create_line(muzzle[0], muzzle[1], flash_end[0], flash_end[1], fill=BULLET_COLOR, width=3)

        c.create_text(18, 16, anchor="nw", fill=TEXT_COLOR, font=("Arial", 22, "bold"), text=f"Score: {self.score}")
        c.create_text(18, 48, anchor="nw", fill=TEXT_COLOR, font=("Arial", 18), text="Mouse to aim • Left click to shoot")

    def draw_player(self):
        c = self.canvas
        horse_left = PLAYER_X - 50
        horse_top = GROUND_Y - HORSE_HEIGHT + 8
        c.create_oval(horse_left, horse_top, horse_left + HORSE_WIDTH, horse_top + HORSE_HEIGHT, fill=HORSE_COLOR, outline="")

        cowboy_x = PLAYER_X + 10
        cowboy_y = GROUND_Y - HORSE_HEIGHT - COWBOY_HEIGHT + 20

        c.create_rectangle(cowboy_x, cowboy_y + 28, cowboy_x + 32, cowboy_y + 70, fill=PLAYER_COLOR, outline="")
        c.create_oval(cowboy_x + 4, cowboy_y, cowboy_x + 28, cowboy_y + 24, fill=PLAYER_COLOR, outline="")
        c.create_rectangle(cowboy_x - 2, cowboy_y - 4, cowboy_x + 36, cowboy_y + 2, fill="#281811", outline="")

        shoulder = (cowboy_x + 28, cowboy_y + 40)
        aim = v_norm(v_sub(self.mouse_pos, shoulder))
        muzzle = v_add(shoulder, v_mul(aim, 48))
        c.create_line(shoulder[0], shoulder[1], muzzle[0], muzzle[1], fill="#221612", width=6)
        return shoulder, muzzle

    def game_loop(self):
        if not self.running:
            return

        now = time.perf_counter()
        dt = now - self.last_frame_time
        self.last_frame_time = now

        self.update(dt)
        self.draw()
        self.root.after(FRAME_MS, self.game_loop)

    def close(self):
        self.running = False
        self.root.destroy()


def main():
    root = tk.Tk()
    root.resizable(False, False)
    game = Game(root)
    game.game_loop()
    root.mainloop()
    sys.exit()


if __name__ == "__main__":
    main()
