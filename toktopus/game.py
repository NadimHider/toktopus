import sys
import time
import random
from typing import List, Dict, Any, Optional

try:
    import msvcrt
    WINDOWS = True
except ImportError:
    WINDOWS = False
    import select
    import termios
    import tty

def _get_key_nonblocking() -> Optional[str]:
    if WINDOWS:
        if msvcrt.kbhit():
            ch = msvcrt.getch()
            # Handle special keys (arrows, function keys)
            if ch in (b"\x00", b"\xe0"):
                ch2 = msvcrt.getch()
                if ch2 == b"H":
                    return "up"
                elif ch2 == b"P":
                    return "down"
                elif ch2 == b"K":
                    return "left"
                elif ch2 == b"M":
                    return "right"
                return None
            try:
                decoded = ch.decode("utf-8", errors="ignore").lower()
                if decoded == " ":
                    return "space"
                elif decoded == "\x1b":
                    return "esc"
                return decoded
            except Exception:
                return None
        return None
    else:
        # POSIX non-blocking key read
        dr, _, _ = select.select([sys.stdin], [], [], 0)
        if dr:
            try:
                ch = sys.stdin.read(1)
                if ch == "\x1b":
                    # Check for arrow sequence
                    dr2, _, _ = select.select([sys.stdin], [], [], 0.01)
                    if dr2:
                        seq = sys.stdin.read(2)
                        if seq == "[A":
                            return "up"
                        elif seq == "[B":
                            return "down"
                        elif seq == "[D":
                            return "left"
                        elif seq == "[C":
                            return "right"
                    return "esc"
                elif ch == " ":
                    return "space"
                return ch.lower()
            except Exception:
                return None
        return None

class SpaceImpactGame:
    def __init__(self, width: int = 68, height: int = 16):
        self.width = max(40, width)
        self.height = max(10, height)
        self.reset()
        self.high_score = 0

    def reset(self):
        self.player_x = 3
        self.player_y = self.height // 2
        self.player_lives = 3
        self.player_hp = 100
        self.score = 0
        self.wave = 1
        self.game_over = False
        self.paused = False
        self.lasers: List[Dict[str, Any]] = []
        self.enemies: List[Dict[str, Any]] = []
        self.enemy_bullets: List[Dict[str, Any]] = []
        self.particles: List[Dict[str, Any]] = []
        self.tick_count = 0
        self.boss_active = False

    def spawn_entities(self):
        self.tick_count += 1

        # Periodic enemy spawns
        spawn_rate = max(6, 18 - (self.wave * 2))
        if self.tick_count % spawn_rate == 0 and not self.boss_active:
            ey = random.randint(1, self.height - 2)
            roll = random.random()

            if roll < 0.50:
                # Scout alien (1 HP, fast)
                self.enemies.append({
                    "x": self.width - 4,
                    "y": ey,
                    "type": "scout",
                    "sprite": "<x>",
                    "hp": 1,
                    "max_hp": 1,
                    "speed": 1,
                    "points": 15,
                    "color": "#00ff88"
                })
            elif roll < 0.80:
                # Interceptor alien (2 HP, diagonal motion)
                self.enemies.append({
                    "x": self.width - 4,
                    "y": ey,
                    "type": "interceptor",
                    "sprite": "<#>",
                    "hp": 2,
                    "max_hp": 2,
                    "speed": 1,
                    "points": 25,
                    "dir_y": random.choice([-1, 1]),
                    "color": "#ffe600"
                })
            elif roll < 0.92:
                # Heavy Fighter (3 HP, shoots bullets)
                self.enemies.append({
                    "x": self.width - 5,
                    "y": ey,
                    "type": "heavy",
                    "sprite": "[=X=]",
                    "hp": 3,
                    "max_hp": 3,
                    "speed": 1,
                    "points": 45,
                    "shoot_cd": random.randint(6, 16),
                    "color": "#ff3366"
                })
            else:
                # Asteroid obstacle (blocks lasers)
                self.enemies.append({
                    "x": self.width - 4,
                    "y": ey,
                    "type": "asteroid",
                    "sprite": "(O)",
                    "hp": 3,
                    "max_hp": 3,
                    "speed": 1,
                    "points": 20,
                    "color": "dim"
                })

        # Spawn boss every 400 points if none currently active
        if self.score > 0 and (self.score % 400 < 50) and not self.boss_active and self.tick_count > 100:
            self.boss_active = True
            self.enemies.append({
                "x": self.width - 12,
                "y": self.height // 2,
                "type": "boss",
                "sprite": "<{[[TITAN]]}>",
                "hp": 15 + (self.wave * 5),
                "max_hp": 15 + (self.wave * 5),
                "speed": 1,
                "points": 200,
                "dir_y": 1,
                "shoot_cd": 5,
                "color": "#b026ff"
            })

    def handle_input(self, key: Optional[str]):
        if not key:
            return

        if key in ("q", "esc"):
            self.game_over = True
            return

        if key == "p":
            self.paused = not self.paused
            return

        if self.game_over:
            if key == "r":
                self.reset()
            return

        if self.paused:
            return

        # Player Movement
        if key in ("w", "up"):
            if self.player_y > 1:
                self.player_y -= 1
        elif key in ("s", "down"):
            if self.player_y < self.height - 2:
                self.player_y += 1
        elif key in ("a", "left"):
            if self.player_x > 2:
                self.player_x -= 1
        elif key in ("d", "right"):
            if self.player_x < self.width // 2:
                self.player_x += 1
        elif key == "space":
            self.fire_laser()

    def fire_laser(self):
        # Limit max active lasers
        if len(self.lasers) < 8:
            self.lasers.append({
                "x": self.player_x + 2,
                "y": self.player_y,
                "sprite": "=",
                "speed": 2
            })

    def update(self):
        if self.game_over or self.paused:
            return

        # 1. Update lasers
        remaining_lasers = []
        for l in self.lasers:
            l["x"] += l["speed"]
            if l["x"] < self.width - 2:
                remaining_lasers.append(l)
        self.lasers = remaining_lasers

        # 2. Update enemy bullets
        remaining_eb = []
        for eb in self.enemy_bullets:
            eb["x"] -= eb.get("speed", 1)
            if eb["x"] > 1:
                remaining_eb.append(eb)
        self.enemy_bullets = remaining_eb

        # 3. Update enemies
        remaining_enemies = []
        for e in self.enemies:
            # Horizontal motion
            if self.tick_count % 2 == 0:
                e["x"] -= e.get("speed", 1)

            # Vertical behavior
            if e["type"] == "interceptor":
                if self.tick_count % 3 == 0:
                    e["y"] += e.get("dir_y", 1)
                    if e["y"] <= 1:
                        e["y"] = 1
                        e["dir_y"] = 1
                    elif e["y"] >= self.height - 2:
                        e["y"] = self.height - 2
                        e["dir_y"] = -1
            elif e["type"] == "boss":
                if self.tick_count % 3 == 0:
                    e["y"] += e.get("dir_y", 1)
                    if e["y"] <= 2:
                        e["y"] = 2
                        e["dir_y"] = 1
                    elif e["y"] >= self.height - 3:
                        e["y"] = self.height - 3
                        e["dir_y"] = -1

            # Enemy firing
            if e["type"] in ("heavy", "boss"):
                cd = e.get("shoot_cd", 10) - 1
                if cd <= 0:
                    self.enemy_bullets.append({
                        "x": e["x"] - 1,
                        "y": e["y"],
                        "sprite": "<" if e["type"] == "heavy" else "*",
                        "speed": 1
                    })
                    e["shoot_cd"] = random.randint(8, 18) if e["type"] == "heavy" else 6
                else:
                    e["shoot_cd"] = cd

            # Keep enemy if still on playfield
            if e["x"] > 1:
                remaining_enemies.append(e)
            else:
                if e["type"] == "boss":
                    self.boss_active = False

        self.enemies = remaining_enemies

        # 4. Check collisions: Lasers vs Enemies
        active_lasers = []
        for l in self.lasers:
            hit = False
            lx, ly = l["x"], l["y"]
            for e in self.enemies:
                ex, ey = e["x"], e["y"]
                e_len = len(e["sprite"])
                if ey == ly and (ex <= lx <= ex + e_len):
                    hit = True
                    e["hp"] -= 1
                    self.particles.append({"x": lx, "y": ly, "ttl": 2, "char": "*"})
                    if e["hp"] <= 0:
                        self.score += e["points"]
                        if self.score > self.high_score:
                            self.high_score = self.score
                        if e["type"] == "boss":
                            self.boss_active = False
                            self.wave += 1
                        self.particles.append({"x": ex, "y": ey, "ttl": 3, "char": "X"})
                    break
            if not hit:
                active_lasers.append(l)
        self.lasers = active_lasers

        # Clean up dead enemies
        self.enemies = [e for e in self.enemies if e["hp"] > 0]

        # 5. Check collisions: Enemy Bullets vs Player
        active_eb = []
        for eb in self.enemy_bullets:
            bx, by = eb["x"], eb["y"]
            if by == self.player_y and (self.player_x <= bx <= self.player_x + 1):
                self.take_player_damage(25)
                self.particles.append({"x": self.player_x, "y": self.player_y, "ttl": 3, "char": "!"})
            else:
                active_eb.append(eb)
        self.enemy_bullets = active_eb

        # 6. Check collisions: Enemies vs Player
        for e in self.enemies:
            ex, ey = e["x"], e["y"]
            e_len = len(e["sprite"])
            if ey == self.player_y and (ex <= self.player_x + 1 and self.player_x <= ex + e_len):
                self.take_player_damage(40)
                e["hp"] = 0
                self.particles.append({"x": self.player_x, "y": self.player_y, "ttl": 3, "char": "!"})

        self.enemies = [e for e in self.enemies if e["hp"] > 0]

        # 7. Update particles
        remaining_particles = []
        for p in self.particles:
            p["ttl"] -= 1
            if p["ttl"] > 0:
                remaining_particles.append(p)
        self.particles = remaining_particles

    def take_player_damage(self, amount: int):
        self.player_hp -= amount
        if self.player_hp <= 0:
            self.player_lives -= 1
            if self.player_lives > 0:
                self.player_hp = 100
                self.player_x = 3
                self.player_y = self.height // 2
            else:
                self.game_over = True

    def render_frame(self) -> str:
        # Build 2D buffer
        grid = [[" " for _ in range(self.width)] for _ in range(self.height)]

        # Draw borders
        for x in range(self.width):
            grid[0][x] = "="
            grid[self.height - 1][x] = "="
        for y in range(self.height):
            grid[y][0] = "|"
            grid[y][self.width - 1] = "|"
        grid[0][0] = "+"
        grid[0][self.width - 1] = "+"
        grid[self.height - 1][0] = "+"
        grid[self.height - 1][self.width - 1] = "+"

        # Draw particles
        for p in self.particles:
            px, py = p["x"], p["y"]
            if 0 < px < self.width - 1 and 0 < py < self.height - 1:
                grid[py][px] = p["char"]

        # Draw enemies
        for e in self.enemies:
            ex, ey = e["x"], e["y"]
            if 0 < ey < self.height - 1:
                sp = e["sprite"]
                for i, ch in enumerate(sp):
                    pos_x = ex + i
                    if 0 < pos_x < self.width - 1:
                        grid[ey][pos_x] = ch

        # Draw lasers
        for l in self.lasers:
            lx, ly = l["x"], l["y"]
            if 0 < lx < self.width - 1 and 0 < ly < self.height - 1:
                grid[ly][lx] = l["sprite"]

        # Draw enemy bullets
        for eb in self.enemy_bullets:
            bx, by = eb["x"], eb["y"]
            if 0 < bx < self.width - 1 and 0 < by < self.height - 1:
                grid[by][bx] = eb["sprite"]

        # Draw player ship (if not game over)
        if not self.game_over:
            px, py = self.player_x, self.player_y
            if 0 < py < self.height - 1:
                if 0 < px < self.width - 1:
                    grid[py][px] = "}"
                if 0 < px + 1 < self.width - 1:
                    grid[py][px + 1] = ">"

        lines = ["".join(row) for row in grid]

        # Draw HUD header
        hp_bar_len = 10
        filled_hp = max(0, min(hp_bar_len, int((self.player_hp / 100.0) * hp_bar_len)))
        empty_hp = hp_bar_len - filled_hp
        hp_bar = "[" + "#" * filled_hp + "." * empty_hp + "]"

        lives_str = "[P]" * self.player_lives + "[ ]" * max(0, 3 - self.player_lives)
        hud = (
            f" SCORE: {self.score:05d} | HIGH: {self.high_score:05d} | "
            f"LIVES: {lives_str} | HP: {hp_bar} {self.player_hp}% | WAVE: {self.wave}"
        )

        controls = " [W/A/S/D or Arrows] Move  [Space] Fire  [P] Pause  [Q] Exit to Monitor"

        if self.game_over:
            over_box = [
                "+-----------------------------------------+",
                "|               GAME OVER                 |",
                f"|            FINAL SCORE: {self.score:05d}           |",
                f"|            HIGH SCORE:  {self.high_score:05d}           |",
                "|       [R] Play Again   [Q] Exit         |",
                "+-----------------------------------------+"
            ]
            start_y = (self.height // 2) - 3
            start_x = (self.width // 2) - 21
            for idx, r in enumerate(over_box):
                y_idx = start_y + idx
                if 0 <= y_idx < len(lines):
                    line_chars = list(lines[y_idx])
                    for ci, c in enumerate(r):
                        xi = start_x + ci
                        if 0 <= xi < len(line_chars):
                            line_chars[xi] = c
                    lines[y_idx] = "".join(line_chars)
        elif self.paused:
            pause_msg = " == GAME PAUSED : PRESS [P] TO RESUME == "
            mid_y = self.height // 2
            start_x = max(2, (self.width - len(pause_msg)) // 2)
            line_chars = list(lines[mid_y])
            for ci, c in enumerate(pause_msg):
                xi = start_x + ci
                if 0 <= xi < len(line_chars):
                    line_chars[xi] = c
            lines[mid_y] = "".join(line_chars)

        return hud + "\n" + "\n".join(lines) + "\n" + controls

def run_space_impact(standalone: bool = True):
    from rich.console import Console
    from rich.live import Live

    console = Console()
    game = SpaceImpactGame(width=68, height=16)

    # In POSIX terminal, enable cbreak mode for single keystrokes
    old_term_settings = None
    if not WINDOWS:
        try:
            fd = sys.stdin.fileno()
            old_term_settings = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            pass

    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while True:
                key = _get_key_nonblocking()
                if key in ("q", "esc"):
                    break

                game.handle_input(key)
                if not game.paused and not game.game_over:
                    game.spawn_entities()
                    game.update()

                frame_text = game.render_frame()
                live.update(frame_text, refresh=True)
                time.sleep(0.04)
    except KeyboardInterrupt:
        pass
    finally:
        if not WINDOWS and old_term_settings:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_term_settings)
            except Exception:
                pass
        console.clear()
        console.print(f"[bold #00f3ff]:: Space Impact finished. Final Score: {game.score} ::[/bold #00f3ff]")
