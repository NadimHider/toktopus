import time
import random
from typing import List, Dict, Any, Optional
from rich.panel import Panel
from rich.text import Text
from rich.table import Table
from rich import box

OCTO_FRAMES = {
    "idle_1": [
        r"   .---.   ",
        r"  / o o \  ",
        r" (|  v  |) ",
        r"  /~\_/~\  ",
        r" (~)   (~) "
    ],
    "idle_2": [
        r"   .---.   ",
        r"  / - - \  ",
        r" (|  ~  |) ",
        r"  \~_/~_   ",
        r"  (~) (~)  "
    ],
    "coding_1": [
        r"   .---.   ",
        r"  / >O< \  ",
        r" (|  W  |) ",
        r"  \~/~\~/  ",
        r"  /~\ /~\  "
    ],
    "coding_2": [
        r"   .---.   ",
        r"  / @.@ \  ",
        r" (|  O  |) ",
        r"  /~\~/~\  ",
        r"  \~/ \~/  "
    ],
    "cache_high": [
        r"   .---.   ",
        r"  / B ) \  ",
        r" (|  -  |) ",
        r"  /~\_/~\  ",
        r" (~)   (~) "
    ],
    "pet": [
        r"   .---.   ",
        r"  / ^.^ \  ",
        r" (|  3  |) ",
        r"  \~v~/~   ",
        r"  (~) (~)  "
    ],
    "eating": [
        r"   .---.   ",
        r"  / ^w^ \  ",
        r" (|  C  |) ",
        r"  \~/~\~/  ",
        r"  (~) (~)  "
    ],
    "sleeping": [
        r"   .---.   ",
        r"  / - - \  ",
        r" (|  o  |) ",
        r"  \_____/  ",
        r"  (~) (~)  "
    ],
    "hungry": [
        r"   .---.   ",
        r"  / . . \  ",
        r" (|  ~  |) ",
        r"  /~\_/~\  ",
        r"  ( ) ( )  "
    ]
}

AUTONOMOUS_QUIPS = [
    "prompt cache is pure dopamine!",
    "streaming tokens... nom nom!",
    "clean code = happy octo.",
    "2M context window feels like the ocean!",
    "watch your TPM limits, captain.",
    "zero compiler errors today please.",
    "refactoring makes my tentacles tingle.",
    "sub-agents are doing heavy lifting!",
    "i love fast inference.",
    "keep the tokens flowing!",
    "cache hit ratio looking elite today.",
    "more context, more power!"
]

class CyberPet:
    def __init__(self, name: str = "Tokto"):
        self.name = name
        self.happiness: int = 85
        self.fuel: int = 75
        self.level: int = 1
        self.xp: int = 0
        self.tokens_digested: int = 0
        self.interactions: int = 0
        self.state: str = "idle"
        self.frame_idx: int = 0
        self.tick_counter: int = 0
        self.action_timer: int = 0
        self.current_quip: str = "ready to monitor tokens!"
        self.quip_timer: int = 40
        self.bubbles: List[Dict[str, Any]] = [
            {"x": random.randint(1, 24), "y": random.randint(1, 4), "char": "."}
            for _ in range(3)
        ]

    def add_xp(self, amount: int):
        self.xp += amount
        needed = self.level * 100
        if self.xp >= needed:
            self.level += 1
            self.xp -= needed
            self.current_quip = f"LEVEL UP! I am now Level {self.level}!"
            self.quip_timer = 50
            self.happiness = min(100, self.happiness + 20)

    def feed(self) -> str:
        self.fuel = min(100, self.fuel + 30)
        self.happiness = min(100, self.happiness + 15)
        self.state = "eating"
        self.action_timer = 12
        self.interactions += 1
        self.add_xp(25)
        self.current_quip = "*nom nom nom* Token treat accepted!"
        self.quip_timer = 30
        return "Fed Tokto a token snack (+30 Fuel, +15 Joy)!"

    def pet(self) -> str:
        self.happiness = min(100, self.happiness + 25)
        self.state = "pet"
        self.action_timer = 12
        self.interactions += 1
        self.add_xp(20)
        self.current_quip = "<3 <3 Tentacles tickled happily!"
        self.quip_timer = 30
        return "Pet Tokto (+25 Joy)!"

    def tick(
        self,
        is_active: bool,
        tokens_per_sec: int,
        cache_eff: float,
        current_ctx: int,
        total_tokens: int
    ):
        self.tick_counter += 1

        # Track tokens digested
        if total_tokens > self.tokens_digested:
            delta = total_tokens - self.tokens_digested
            self.tokens_digested = total_tokens
            # Gain XP from tokens
            if delta > 1000:
                self.add_xp(max(1, delta // 50000))

        # Handle temporary action states (eating, pet)
        if self.action_timer > 0:
            self.action_timer -= 1
        else:
            # Autonomous state decision
            if is_active or tokens_per_sec > 50:
                self.state = "coding"
                self.fuel = max(0, self.fuel - 1 if self.tick_counter % 30 == 0 else self.fuel)
            elif cache_eff >= 80.0 and current_ctx > 10000:
                self.state = "cache_high"
            elif self.fuel <= 20:
                self.state = "hungry"
            elif not is_active and self.tick_counter > 200 and (self.tick_counter % 120 < 60):
                self.state = "sleeping"
            else:
                self.state = "idle"

        # Slow happiness / fuel drift
        if self.tick_counter % 60 == 0:
            if self.fuel > 0:
                self.fuel = max(0, self.fuel - 1)
            else:
                self.happiness = max(10, self.happiness - 2)

        # Autonomous speech bubble updates
        self.quip_timer -= 1
        if self.quip_timer <= 0:
            if self.state == "hungry":
                self.current_quip = "hunger low! press [F] to feed me tokens..."
            elif self.state == "sleeping":
                self.current_quip = "z z Z ... dreaming of clean syntax ... z Z"
            elif self.state == "cache_high":
                self.current_quip = f"cache is {cache_eff:.0f}%! pure elegance."
            elif self.state == "coding":
                self.current_quip = "tokens are flying! keep it up!"
            else:
                self.current_quip = random.choice(AUTONOMOUS_QUIPS)
            self.quip_timer = random.randint(45, 90)

        # Update floating bubbles
        if self.tick_counter % 2 == 0:
            for b in self.bubbles:
                b["y"] -= 1
                if b["y"] <= 0:
                    b["y"] = 4
                    b["x"] = random.randint(1, 24)
                    b["char"] = random.choice([".", "o", "*", "+"])

    def get_current_sprite(self) -> List[str]:
        if self.state == "coding":
            key = "coding_1" if (self.tick_counter // 2) % 2 == 0 else "coding_2"
        elif self.state == "cache_high":
            key = "cache_high"
        elif self.state == "eating":
            key = "eating"
        elif self.state == "pet":
            key = "pet"
        elif self.state == "sleeping":
            key = "sleeping"
        elif self.state == "hungry":
            key = "hungry"
        else:
            key = "idle_1" if (self.tick_counter // 4) % 2 == 0 else "idle_2"
        return OCTO_FRAMES.get(key, OCTO_FRAMES["idle_1"])

    def render_widget(self, width: int = 34) -> Panel:
        sprite = self.get_current_sprite()

        # Mood badge and style
        mood_map = {
            "idle": ("CHILL", "#00f3ff"),
            "coding": ("STREAMING", "#ffe600"),
            "cache_high": ("ELITE CACHE", "#00ff88"),
            "eating": ("FEASTING", "#00ff88"),
            "pet": ("LOVED", "#ff3366"),
            "sleeping": ("SLEEPING", "#b026ff"),
            "hungry": ("HUNGRY", "#ff3366")
        }
        mood_name, mood_color = mood_map.get(self.state, ("HAPPY", "#00f3ff"))

        # Build Mini Bar Gauges
        def _mini_bar(val: int, max_val: int = 100, length: int = 8, color: str = "#00ff88") -> str:
            filled = max(0, min(length, int((val / max_val) * length)))
            empty = length - filled
            return f"[{color}]{'█' * filled}[/{color}][dim]{'░' * empty}[/dim] {val}%"

        fuel_gauge = _mini_bar(self.fuel, 100, length=7, color="#ffe600" if self.fuel < 35 else "#00ff88")
        joy_gauge = _mini_bar(self.happiness, 100, length=7, color="#ff3366" if self.happiness < 35 else "#00f3ff")

        # Layout inside pet box
        content = Table.grid(padding=(0, 1), expand=True)
        content.add_column("pet", justify="left")
        content.add_column("info", justify="left")

        # Format sprite with neon colors
        color_tag = mood_color
        colored_sprite = [f"[{color_tag}]{line}[/{color_tag}]" for line in sprite]

        # Info lines on right side
        quip_text = self.current_quip[:36]
        info_lines = [
            f"[bold white]{self.name}[/bold white] [dim](Lv.{self.level})[/dim] [{mood_color}][{mood_name}][/{mood_color}]",
            f"[dim]Thought:[/dim] [#00ff88]\"{quip_text}\"[/#00ff88]",
            f"[dim]Fuel:[/dim] {fuel_gauge}",
            f"[dim]Joy :[/dim] {joy_gauge}",
            f"[bold #00f3ff][F][/bold #00f3ff][dim] Feed Token  [/dim][bold #ff3366][T][/bold #ff3366][dim] Pet[/dim]"
        ]

        # Combine rows
        for i in range(max(len(colored_sprite), len(info_lines))):
            s_part = colored_sprite[i] if i < len(colored_sprite) else "           "
            i_part = info_lines[i] if i < len(info_lines) else ""
            content.add_row(s_part, i_part)

        title = f"[bold #00f3ff][TOKTO : COMPANION][/bold #00f3ff]"
        return Panel(
            content,
            title=title,
            border_style=mood_color,
            box=box.ROUNDED,
            padding=(0, 1)
        )

# Global pet instance for state persistence across dashboard cycles
_GLOBAL_PET = CyberPet("Tokto")

def get_cyber_pet() -> CyberPet:
    global _GLOBAL_PET
    return _GLOBAL_PET

def run_pet_lounge():
    from rich.console import Console
    from rich.live import Live
    import sys

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
                if ch in (b"\x00", b"\xe0"):
                    ch2 = msvcrt.getch()
                    if ch2 == b"H": return "up"
                    elif ch2 == b"P": return "down"
                    elif ch2 == b"K": return "left"
                    elif ch2 == b"M": return "right"
                    return None
                try:
                    decoded = ch.decode("utf-8", errors="ignore").lower()
                    if decoded == " ": return "space"
                    elif decoded == "\x1b": return "esc"
                    return decoded
                except Exception:
                    return None
            return None
        else:
            dr, _, _ = select.select([sys.stdin], [], [], 0)
            if dr:
                try:
                    ch = sys.stdin.read(1)
                    if ch == "\x1b": return "esc"
                    elif ch == " ": return "space"
                    return ch.lower()
                except Exception:
                    return None
            return None

    console = Console()
    pet = get_cyber_pet()

    tank_w = 64
    tank_h = 14
    pet_x = tank_w // 2 - 5
    pet_y = tank_h // 2 - 2
    snacks = []
    bubbles = [{"x": random.randint(2, tank_w - 3), "y": random.randint(1, tank_h - 2)} for _ in range(8)]
    banner_msg = "Welcome to Tokto's Cyber Habitat! [F] Drop Token Snack  [T] Pet  [W/A/S/D] Swim  [Q] Exit"

    old_term = None
    if not WINDOWS:
        try:
            fd = sys.stdin.fileno()
            old_term = termios.tcgetattr(fd)
            tty.setcbreak(fd)
        except Exception:
            pass

    try:
        with Live(console=console, screen=True, auto_refresh=False) as live:
            while True:
                k = _get_key_nonblocking()
                if k in ("q", "esc"):
                    break
                elif k in ("f", "space"):
                    snacks.append({"x": random.randint(pet_x - 3, pet_x + 8), "y": 1})
                    pet.feed()
                    banner_msg = "You dropped a crunchy token snack! Tokto is overjoyed!"
                elif k == "t":
                    pet.pet()
                    banner_msg = "You gave Tokto gentle scratches! Tokto wiggles with happiness!"
                elif k in ("w", "up"):
                    pet_y = max(1, pet_y - 1)
                elif k in ("s", "down"):
                    pet_y = min(tank_h - 6, pet_y + 1)
                elif k in ("a", "left"):
                    pet_x = max(2, pet_x - 2)
                elif k in ("d", "right"):
                    pet_x = min(tank_w - 14, pet_x + 2)

                # Update simulation
                pet.tick(is_active=False, tokens_per_sec=0, cache_eff=95.0, current_ctx=50000, total_tokens=100000)

                # Move snacks down
                rem_snacks = []
                for sn in snacks:
                    sn["y"] += 1
                    if abs(sn["x"] - (pet_x + 5)) <= 4 and abs(sn["y"] - (pet_y + 2)) <= 2:
                        pet.feed()
                    elif sn["y"] < tank_h - 1:
                        rem_snacks.append(sn)
                snacks = rem_snacks

                # Move bubbles up
                for b in bubbles:
                    b["y"] -= 1
                    if b["y"] <= 0:
                        b["y"] = tank_h - 2
                        b["x"] = random.randint(2, tank_w - 3)

                # Render 2D aquarium
                grid = [[" " for _ in range(tank_w)] for _ in range(tank_h)]
                for x in range(tank_w):
                    grid[0][x] = "="
                    grid[tank_h - 1][x] = "="
                for y in range(tank_h):
                    grid[y][0] = "|"
                    grid[y][tank_w - 1] = "|"
                grid[0][0] = "+"
                grid[0][tank_w - 1] = "+"
                grid[tank_h - 1][0] = "+"
                grid[tank_h - 1][tank_w - 1] = "+"

                # Sea floor plants
                for px in range(2, tank_w - 2, 7):
                    grid[tank_h - 2][px] = "§"
                    grid[tank_h - 3][px] = "~"

                # Bubbles
                for b in bubbles:
                    if 0 < b["y"] < tank_h - 1 and 0 < b["x"] < tank_w - 1:
                        grid[b["y"]][b["x"]] = "o"

                # Snacks
                for sn in snacks:
                    if 0 < sn["y"] < tank_h - 1 and 0 < sn["x"] < tank_w - 1:
                        grid[sn["y"]][sn["x"]] = "*"

                # Draw Pet
                sprite = pet.get_current_sprite()
                for sy, s_line in enumerate(sprite):
                    gy = pet_y + sy
                    if 0 < gy < tank_h - 1:
                        for sx, ch in enumerate(s_line):
                            gx = pet_x + sx
                            if 0 < gx < tank_w - 1 and ch != " ":
                                grid[gy][gx] = ch

                lines = ["".join(row) for row in grid]
                hud = (
                    f" :: TOKTO PET LOUNGE :: Level {pet.level} | Fuel: {pet.fuel}% | Joy: {pet.happiness}% | "
                    f"Tokens Digested: {pet.tokens_digested:,} ::\n"
                    f" Mood: [{pet.state.upper()}]  \"{pet.current_quip}\"\n"
                )
                controls = f"\n {banner_msg}"
                live.update(hud + "\n".join(lines) + controls, refresh=True)
                time.sleep(0.08)
    except KeyboardInterrupt:
        pass
    finally:
        if not WINDOWS and old_term:
            try:
                termios.tcsetattr(sys.stdin.fileno(), termios.TCSADRAIN, old_term)
            except Exception:
                pass
        console.clear()
        console.print(f"[bold #00f3ff]:: Returning from Tokto Pet Lounge ::[/bold #00f3ff]")
