from __future__ import annotations

import json
import random
import shutil
import time
from dataclasses import dataclass, field
from pathlib import Path


SAVE_PATH = Path(__file__).with_name("garden_save.json")
ASCII_PATH = Path(__file__).with_name("ASCII.txt")


RESET = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"


SPECIES_DATA = {
    "Tulip": {"seed_price": 12, "sell_price": 30, "water_need": 5},
    "Sunflower": {"seed_price": 15, "sell_price": 36, "water_need": 6},
    "Lily": {"seed_price": 18, "sell_price": 42, "water_need": 4},
    "Rose": {"seed_price": 20, "sell_price": 48, "water_need": 5},
    "Daisy": {"seed_price": 10, "sell_price": 24, "water_need": 5},
    "Orchid": {"seed_price": 22, "sell_price": 55, "water_need": 4},
}

COLOR_VARIANTS = {
    "Tulip": [("Ivory", WHITE), ("Blush", MAGENTA), ("Amber", YELLOW), ("Azure", CYAN)],
    "Sunflower": [("Gold", YELLOW), ("Sunset", RED), ("Pearl", WHITE), ("Solar", CYAN)],
    "Lily": [("Moon", WHITE), ("Lavender", MAGENTA), ("Mint", GREEN), ("Aurora", CYAN)],
    "Rose": [("Crimson", RED), ("Snow", WHITE), ("Coral", YELLOW), ("Nebula", MAGENTA)],
    "Daisy": [("Classic", WHITE), ("Honey", YELLOW), ("Frost", CYAN), ("Candy", MAGENTA)],
    "Orchid": [("Velvet", MAGENTA), ("Pearl", WHITE), ("Tide", CYAN), ("Ember", RED)],
}

STAGE_NAMES = ["Seed", "Sprout", "Growing", "Bloom"]
# Stage 1 -> 2: 1 day, 2 -> 3: 1 day, 3 -> 4: 2 days.
# (Indexed from 0: Seed, 1: Sprout, 2: Growing, 3: Bloom)
STAGE_DURATIONS = [0, 1, 2, 4]

ACHIEVEMENT_REWARDS = {
    "First Bloom": 25,
    "Rain Lover": 30,
    "Plant Doctor": 40,
    "Collector I": 50,
}


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def safe_input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return "7"


def color_text(text: str, colour: str) -> str:
    return f"{colour}{text}{RESET}"


def boxed_message(title: str, body: str) -> str:
    lines = [title, body]
    width = max(len(line) for line in lines) + 4
    top = "+" + "-" * (width - 2) + "+"
    middle = "\n".join(f"| {line.ljust(width - 4)} |" for line in lines)
    return f"{top}\n{middle}\n{top}"


def terminal_width() -> int:
    return shutil.get_terminal_size((90, 24)).columns


def center_line(line: str, width: int | None = None) -> str:
    width = width or terminal_width()
    stripped = line.rstrip("\n")
    pad = max(0, (width - len(stripped)) // 2)
    return (" " * pad) + stripped


def center_block(text: str) -> str:
    width = terminal_width()
    return "\n".join(center_line(line, width) for line in text.splitlines())


def clear_terminal() -> None:
    print("\033[2J\033[H", end="")


def pad_lines(lines: list[str], width: int) -> list[str]:
    return [line.ljust(width) for line in lines]


def render_grid(cells: list[list[str]], columns: int = 3, gap: str = "   ") -> str:
    if not cells:
        return ""
    rendered_rows: list[str] = []
    for row_start in range(0, len(cells), columns):
        row_cells = cells[row_start : row_start + columns]
        heights = [len(cell) for cell in row_cells]
        height = max(heights) if heights else 0
        widths = [max((len(line) for line in cell), default=0) for cell in row_cells]
        padded_cells: list[list[str]] = []
        for cell, w in zip(row_cells, widths):
            padded = pad_lines(cell + [""] * (height - len(cell)), w)
            padded_cells.append(padded)
        for line_index in range(height):
            rendered_rows.append(gap.join(cell[line_index] for cell in padded_cells).rstrip())
        rendered_rows.append("")
    return "\n".join(rendered_rows).rstrip("\n")


def sparkles() -> str:
    return color_text("* * * RARE BLOOM * * *", YELLOW)


def load_ascii_art() -> dict[str, str]:
    if not ASCII_PATH.exists():
        return {}
    sections: dict[str, list[str]] = {}
    current = None
    header_map = {
        "花盆": "Pot",
        "种子": "Seed",
        "发芽": "Sprout",
        "生长": "Growing",
        "枯萎": "Withered",
        "郁金香": "Tulip",
        "向日葵": "Sunflower",
        "百合花": "Lily",
        "玫瑰花": "Rose",
        "小雏菊": "Daisy",
        "蝴蝶兰": "Orchid",
        "铃兰花": "Lily",
        "玉兰花": "Orchid",
    }
    for raw_line in ASCII_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.rstrip("\n")
        if line.startswith("#"):
            current_raw = line[1:].strip()
            current = current_raw
            for chinese, english in header_map.items():
                if chinese in current_raw:
                    current = english
                    break
            sections[current] = []
            continue
        if current is not None:
            sections[current].append(line)
    return {name: "\n".join(lines).strip("\n") for name, lines in sections.items()}


ASCII_ART = load_ascii_art()


@dataclass
class Plant:
    species: str
    pot_id: int
    stage: int = 0
    age: int = 0
    water_level: int = 6
    health: int = 10
    is_alive: bool = True
    bloom_color: str | None = None
    rare_bloom: bool = False
    mutation_boost: bool = False
    revived_once: bool = False
    full_water_streak: int = 0
    rescued_from_low_health: bool = False

    def display_name(self) -> str:
        return self.species

    def target_water(self) -> int:
        return SPECIES_DATA[self.species]["water_need"]

    def needs_bloom_roll(self) -> bool:
        return self.stage == 2 and self.age + 1 >= STAGE_DURATIONS[3]

    def apply_new_day(self) -> list[str]:
        events = []
        if not self.is_alive:
            return events
        self.age += 1
        if self.water_level > 10:
            self.health = max(0, self.health - 1)
            events.append(
                f"Pot {self.pot_id}: {self.display_name()} was overwatered and lost a bit of health."
            )
        self.water_level = max(0, self.water_level - 2)
        if self.water_level == 0:
            self.health = max(0, self.health - 3)
            events.append(f"Pot {self.pot_id}: {self.display_name()} dried out and lost health.")
        elif self.water_level <= 2:
            self.health = max(0, self.health - 1)
            events.append(f"Pot {self.pot_id}: {self.display_name()} is thirsty.")
        else:
            self.health = min(10, self.health + 1)

        if self.water_level >= 5:
            self.full_water_streak += 1
        else:
            self.full_water_streak = 0

        if self.health == 0:
            self.is_alive = False
            events.append(f"Pot {self.pot_id}: {self.display_name()} has withered.")
            return events

        new_stage = self.stage
        for stage_index, required_age in enumerate(STAGE_DURATIONS):
            if self.age >= required_age:
                new_stage = stage_index
        if new_stage > self.stage:
            events.append(
                f"Pot {self.pot_id}: {self.display_name()} advanced to {STAGE_NAMES[new_stage]}."
            )
            self.stage = new_stage
        return events

    def to_dict(self) -> dict:
        return {
            "species": self.species,
            "pot_id": self.pot_id,
            "stage": self.stage,
            "age": self.age,
            "water_level": self.water_level,
            "health": self.health,
            "is_alive": self.is_alive,
            "bloom_color": self.bloom_color,
            "rare_bloom": self.rare_bloom,
            "mutation_boost": self.mutation_boost,
            "revived_once": self.revived_once,
            "full_water_streak": self.full_water_streak,
            "rescued_from_low_health": self.rescued_from_low_health,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Plant":
        return cls(**data)


@dataclass
class Quest:
    name: str
    description: str
    reward: int
    quest_type: str
    low: int | None = None
    high: int | None = None

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Quest":
        return cls(**data)


@dataclass
class PlayerState:
    coins: int = 90
    day: int = 1
    plants: list[Plant] = field(default_factory=list)
    encyclopedia: list[str] = field(default_factory=list)
    achievements: list[str] = field(default_factory=list)
    market_seed_prices: dict[str, int] = field(default_factory=dict)
    market_sell_prices: dict[str, int] = field(default_factory=dict)
    sold_today: int = 0
    revived_today: bool = False
    current_quest: Quest | None = None
    next_pot_id: int = 1

    def to_dict(self) -> dict:
        return {
            "coins": self.coins,
            "day": self.day,
            "plants": [plant.to_dict() for plant in self.plants],
            "encyclopedia": self.encyclopedia,
            "achievements": self.achievements,
            "market_seed_prices": self.market_seed_prices,
            "market_sell_prices": self.market_sell_prices,
            "sold_today": self.sold_today,
            "revived_today": self.revived_today,
            "current_quest": self.current_quest.to_dict() if self.current_quest else None,
            "next_pot_id": self.next_pot_id,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "PlayerState":
        state = cls()
        state.coins = data["coins"]
        state.day = data["day"]
        state.plants = [Plant.from_dict(item) for item in data["plants"]]
        state.encyclopedia = data["encyclopedia"]
        state.achievements = data["achievements"]
        state.market_seed_prices = data["market_seed_prices"]
        state.market_sell_prices = data["market_sell_prices"]
        state.sold_today = data["sold_today"]
        state.revived_today = data["revived_today"]
        quest_data = data["current_quest"]
        state.current_quest = Quest.from_dict(quest_data) if quest_data else None
        state.next_pot_id = data["next_pot_id"]
        return state


class GardenGame:
    def __init__(self) -> None:
        self.player = self.load_or_create_state()
        self.running = True

    def load_or_create_state(self) -> PlayerState:
        if SAVE_PATH.exists():
            try:
                data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
                return PlayerState.from_dict(data)
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        state = PlayerState()
        self.refresh_market_prices(state, initial=True)
        state.current_quest = self.generate_quest(state)
        return state

    def save(self) -> None:
        SAVE_PATH.write_text(
            json.dumps(self.player.to_dict(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def run(self) -> None:
        while self.running:
            clear_terminal()
            print(center_block(self.title_screen()))
            self.print_status()
            choice = safe_input(
                "\nChoose: [1] Garden [2] Shop [3] Market [4] Encyclopedia [5] Sleep [6] Save&Quit [7] Quit [8] Delete Save\n> "
            )
            print()
            if choice == "1":
                self.garden_menu()
            elif choice == "2":
                self.shop_menu()
            elif choice == "3":
                self.market_menu()
            elif choice == "4":
                self.show_encyclopedia()
            elif choice == "5":
                self.end_day()
            elif choice == "6":
                self.save()
                print(color_text("Progress saved. See you in the garden.", CYAN))
                self.running = False
            elif choice == "7":
                print(color_text("See you in the garden.", CYAN))
                self.running = False
            elif choice == "8":
                self.delete_save()
            else:
                print(color_text("Please choose a valid menu option.", RED))

    def title_screen(self) -> str:
        pot_art = ASCII_ART.get("Pot", "")
        seed_art = ASCII_ART.get("Seed", "")
        return (
            color_text("Bloom & Bust Garden", GREEN)
            + "\nA terminal flower market game built for COMP9001.\n\n"
            + seed_art
            + "\n"
            + "\n"
            + pot_art
            + "\n"
        )

    def print_status(self) -> None:
        quest = self.player.current_quest.description if self.player.current_quest else "None"
        status = (
            f"{BOLD}Day {self.player.day}{RESET}  "
            f"Coins: {color_text(str(self.player.coins), YELLOW)}  "
            f"Plants: {len(self.player.plants)}  "
            f"Quest: {quest}"
        )
        print(center_line(status))

    def garden_menu(self) -> None:
        while True:
            self.show_garden()
            choice = safe_input(
                "\nGarden: [1] Water [2] Fertiliser [3] Mutation Serum [4] Revival Idol [5] Back\n> "
            )
            if choice == "1":
                self.water_plant()
            elif choice == "2":
                self.use_fertiliser()
            elif choice == "3":
                self.use_mutation_serum()
            elif choice == "4":
                self.use_revival_idol()
            elif choice == "5":
                return
            else:
                print(color_text("That option is not available.", RED))

    def show_garden(self) -> None:
        print(center_line(color_text("Garden Overview", BLUE)))
        if not self.player.plants:
            print(center_line("You do not own any plants yet."))
            return
        pot_art_lines = ASCII_ART.get("Pot", "").splitlines()
        cards: list[list[str]] = []
        for plant in self.player.plants:
            alive_text = color_text("Alive", GREEN) if plant.is_alive else color_text("Withered", RED)
            bloom_text = plant.bloom_color or "-"

            info_line_1 = (
                f"Pot {plant.pot_id} || {plant.display_name()} || Stage: {STAGE_NAMES[plant.stage]}"
            )
            info_line_2 = (
                f"Water: {plant.water_level}/10 || Health: {plant.health}/10 || Bloom: {bloom_text} || {alive_text}"
            )

            flower_art = ""
            if not plant.is_alive:
                flower_art = ASCII_ART.get("Withered", "")
            elif plant.stage == 0:
                flower_art = ASCII_ART.get("Seed", "")
            elif plant.stage == 1:
                flower_art = ASCII_ART.get("Sprout", "")
            elif plant.stage == 2:
                flower_art = ASCII_ART.get("Growing", "")
            elif plant.stage == 3:
                flower_art = ASCII_ART.get(plant.species, "")

            art_lines = flower_art.splitlines() if flower_art else []
            if pot_art_lines:
                art_lines = art_lines + [""] + pot_art_lines

            card_lines = [info_line_1, info_line_2, ""] + art_lines
            cards.append(card_lines)

        grid = render_grid(cards, columns=3)
        print(center_block(grid))

    def select_plant(self, allow_dead: bool = False, prompt: str = "Choose pot id: ") -> Plant | None:
        if not self.player.plants:
            print("You have no plants.")
            return None
        raw = safe_input(prompt)
        if not raw.isdigit():
            print(color_text("Please enter a pot number.", RED))
            return None
        pot_id = int(raw)
        for plant in self.player.plants:
            if plant.pot_id == pot_id:
                if plant.is_alive or allow_dead:
                    return plant
                print(color_text("That plant has withered.", RED))
                return None
        print(color_text("No plant with that pot id.", RED))
        return None

    def water_plant(self) -> None:
        plant = self.select_plant()
        if not plant:
            return
        amount_raw = safe_input("Water amount (1-5): ")
        if not amount_raw.isdigit():
            print(color_text("Please enter a number.", RED))
            return
        amount = clamp(int(amount_raw), 1, 5)
        if plant.health <= 3 and plant.water_level == 0:
            plant.rescued_from_low_health = True
        plant.water_level = max(0, plant.water_level + amount)
        extra = ""
        if plant.water_level > 10:
            extra = color_text(" (over 10: health may drop tomorrow)", YELLOW)
        print(
            color_text(
                f"You watered pot {plant.pot_id}. Water is now {plant.water_level}.",
                GREEN,
            )
            + extra
        )

    def use_fertiliser(self) -> None:
        cost = 24
        if self.player.coins < cost:
            print(color_text("Not enough coins for fertiliser.", RED))
            return
        plant = self.select_plant()
        if not plant:
            return
        if plant.stage >= 3:
            print(color_text("This plant is already blooming.", RED))
            return
        self.player.coins -= cost
        plant.age = min(STAGE_DURATIONS[3], plant.age + 2)
        for stage_index, required_age in enumerate(STAGE_DURATIONS):
            if plant.age >= required_age:
                plant.stage = stage_index
        print(color_text(f"Pot {plant.pot_id} was pushed forward one growth step.", GREEN))

    def use_mutation_serum(self) -> None:
        cost = 28
        if self.player.coins < cost:
            print(color_text("Not enough coins for mutation serum.", RED))
            return
        plant = self.select_plant()
        if not plant:
            return
        if plant.stage >= 3:
            print(color_text("Use mutation serum before the plant blooms.", RED))
            return
        self.player.coins -= cost
        plant.mutation_boost = True
        print(color_text("Mutation serum applied. Rare bloom chance is now much higher.", GREEN))

    def use_revival_idol(self) -> None:
        cost = 40
        if self.player.coins < cost:
            print(color_text("Not enough coins for revival idol.", RED))
            return
        plant = self.select_plant(allow_dead=True)
        if not plant:
            return
        if plant.is_alive:
            print(color_text("That plant is still alive.", RED))
            return
        self.player.coins -= cost
        plant.is_alive = True
        plant.health = 4
        plant.water_level = 4
        plant.revived_once = True
        self.player.revived_today = True
        print(color_text(f"Pot {plant.pot_id} returned from the brink.", GREEN))

    def shop_menu(self) -> None:
        print(center_line(color_text("Seed Shop", BLUE)))
        rows: list[tuple[str, str]] = []
        for species in SPECIES_DATA:
            seed_price = f"{self.player.market_seed_prices[species]} coins"
            sell_price = f"Base sell {self.player.market_sell_prices[species]}"
            rows.append((species, f"{seed_price} | {sell_price}"))
        left_width = max(len(left) for left, _ in rows) if rows else 0
        right_width = max(len(right) for _, right in rows) if rows else 0
        for left, right in rows:
            line = f"{left.rjust(left_width)} | {right.ljust(right_width)}"
            print(center_line(line))
        choice = safe_input("Type species name to buy, or press Enter to go back: ")
        if not choice:
            return
        species = choice.title()
        if species not in SPECIES_DATA:
            print(color_text("Unknown seed type.", RED))
            return
        price = self.player.market_seed_prices[species]
        if self.player.coins < price:
            print(color_text("Not enough coins.", RED))
            return
        self.player.coins -= price
        plant = Plant(species=species, pot_id=self.player.next_pot_id)
        self.player.next_pot_id += 1
        self.player.plants.append(plant)
        print(color_text(f"You bought a {species} seed for pot {plant.pot_id}.", GREEN))

    def market_menu(self) -> None:
        print(center_line(color_text("Flower Market", BLUE)))
        blooming = [plant for plant in self.player.plants if plant.stage == 3 and plant.is_alive]
        if not blooming:
            print(center_line("You have no blooming plants to sell."))
            return
        for plant in blooming:
            price = self.sale_price(plant)
            rarity = "Rare" if plant.rare_bloom else "Standard"
            print(
                center_line(
                    f"Pot {plant.pot_id}: {plant.display_name()} {plant.bloom_color or ''} "
                    f"| {rarity} | Sale price: {price}"
                )
            )
        raw = safe_input("Choose pot id to sell, or press Enter to go back: ")
        if not raw:
            return
        if not raw.isdigit():
            print(color_text("Please enter a pot number.", RED))
            return
        pot_id = int(raw)
        for plant in blooming:
            if plant.pot_id == pot_id:
                price = self.sale_price(plant)
                self.player.coins += price
                self.player.sold_today += 1
                self.player.plants = [p for p in self.player.plants if p.pot_id != pot_id]
                print(color_text(f"Sold pot {pot_id} for {price} coins.", GREEN))
                return
        print(color_text("That plant is not ready to sell.", RED))

    def show_encyclopedia(self) -> None:
        print(center_line(color_text("Encyclopedia & Achievements", BLUE)))
        if self.player.encyclopedia:
            print(center_line("Discovered blooms:"))
            for entry in self.player.encyclopedia:
                print(center_line(f"- {entry}"))
        else:
            print(center_line("No blooms discovered yet."))
        print()
        print(center_line("Achievements:"))
        if self.player.achievements:
            for entry in self.player.achievements:
                print(center_line(f"- {entry}"))
        else:
            print(center_line("No achievements unlocked yet."))

    def refresh_market_prices(self, state: PlayerState, initial: bool = False) -> None:
        for species, info in SPECIES_DATA.items():
            if initial:
                seed = info["seed_price"]
                sell = info["sell_price"]
            else:
                seed = state.market_seed_prices[species] + random.randint(-3, 4)
                sell = state.market_sell_prices[species] + random.randint(-5, 6)
            state.market_seed_prices[species] = clamp(seed, max(6, info["seed_price"] - 5), info["seed_price"] + 10)
            state.market_sell_prices[species] = clamp(
                sell, max(14, info["sell_price"] - 10), info["sell_price"] + 18
            )

    def generate_quest(self, state: PlayerState) -> Quest:
        quests = [
            Quest(
                name="New Roots",
                description="Own at least one plant by the end of the day.",
                reward=15,
                quest_type="own_one",
            )
        ]
        living = [plant for plant in state.plants if plant.is_alive]
        withered = [plant for plant in state.plants if not plant.is_alive]
        blooming = [plant for plant in state.plants if plant.is_alive and plant.stage == 3]
        if living:
            quests.append(
                Quest(
                    name="Steady Hands",
                    description="Keep every living plant between water 4 and 7 by the end of the day.",
                    reward=20,
                    quest_type="water_range",
                    low=4,
                    high=7,
                )
            )
        if blooming:
            quests.append(
                Quest(
                    name="Market Day",
                    description="Sell at least one blooming plant today.",
                    reward=18,
                    quest_type="sell_once",
                )
            )
        if withered:
            quests.append(
                Quest(
                    name="Emergency Care",
                    description="Revive one withered plant today.",
                    reward=30,
                    quest_type="revive_once",
                )
            )
        return random.choice(quests)

    def end_day(self) -> None:
        print(center_line(color_text(f"Night falls on day {self.player.day}...", CYAN)))
        events: list[str] = []
        bloom_happened = False
        for plant in self.player.plants:
            roll_bloom = plant.needs_bloom_roll()
            events.extend(plant.apply_new_day())
            if plant.is_alive and roll_bloom and plant.stage == 3:
                self.resolve_bloom(plant)
                bloom_happened = True
        reward = self.resolve_quest()
        achievement_messages = self.check_achievements()
        self.player.day += 1
        self.player.sold_today = 0
        self.player.revived_today = False
        self.refresh_market_prices(self.player)
        self.player.current_quest = self.generate_quest(self.player)
        self.save()

        if events:
            print(center_block("\n".join(events)))
        if bloom_happened:
            print(center_line(color_text("A new bloom appeared in the garden.", MAGENTA)))
        if reward:
            print(center_line(color_text(f"Quest complete. You earned {reward} coins.", GREEN)))
        for message in achievement_messages:
            print(center_line(message))
        if not events and not bloom_happened and not reward and not achievement_messages:
            print(center_line("It was a quiet night in the garden."))

        safe_input("\nPress Enter to wake up to a new day... ")
        time.sleep(0.2)

    def delete_save(self) -> None:
        print(center_line(color_text("Delete Save", RED)))
        confirm = safe_input("Type DELETE to confirm, or press Enter to cancel: ")
        if confirm != "DELETE":
            print(color_text("Cancelled.", YELLOW))
            return
        try:
            if SAVE_PATH.exists():
                SAVE_PATH.unlink()
        except OSError:
            print(color_text("Could not delete save file.", RED))
            return
        self.player = self.load_or_create_state()
        print(color_text("Save deleted. A new garden has been started.", GREEN))

    def resolve_bloom(self, plant: Plant) -> None:
        rare_chance = 0.60 if plant.mutation_boost else 0.15
        rare = random.random() < rare_chance
        colour_name, colour_code = random.choice(COLOR_VARIANTS[plant.species])
        if rare:
            colour_name = f"Rare {colour_name}"
        plant.rare_bloom = rare
        plant.bloom_color = colour_name
        plant.mutation_boost = False
        art = ASCII_ART.get(plant.species, "")
        if art:
            print(center_block(art))
        if rare:
            print(center_line(sparkles()))
        print(
            center_line(
                color_text(
                    f"Pot {plant.pot_id} bloomed into a {colour_name} {plant.species}.",
                    colour_code,
                )
            )
        )
        entry = f"{colour_name} {plant.species}"
        if entry not in self.player.encyclopedia:
            self.player.encyclopedia.append(entry)

    def resolve_quest(self) -> int:
        quest = self.player.current_quest
        if not quest:
            return 0
        success = False
        if quest.quest_type == "water_range":
            living = [plant for plant in self.player.plants if plant.is_alive]
            success = bool(living) and all(quest.low <= plant.water_level <= quest.high for plant in living)
        elif quest.quest_type == "own_one":
            success = any(plant.is_alive for plant in self.player.plants)
        elif quest.quest_type == "sell_once":
            success = self.player.sold_today >= 1
        elif quest.quest_type == "revive_once":
            success = self.player.revived_today
        if success:
            self.player.coins += quest.reward
            return quest.reward
        return 0

    def check_achievements(self) -> list[str]:
        messages = []
        unlocked = set(self.player.achievements)

        def unlock(name: str) -> None:
            if name in unlocked:
                return
            unlocked.add(name)
            self.player.achievements.append(name)
            reward = ACHIEVEMENT_REWARDS[name]
            self.player.coins += reward
            messages.append(color_text(boxed_message(f"Achievement: {name}", f"+{reward} coins"), YELLOW))

        if any(plant.stage == 3 and plant.is_alive for plant in self.player.plants):
            unlock("First Bloom")
        if any(plant.full_water_streak >= 3 for plant in self.player.plants):
            unlock("Rain Lover")
        if any(plant.revived_once or plant.rescued_from_low_health for plant in self.player.plants):
            unlock("Plant Doctor")
        if len(self.player.encyclopedia) >= 5:
            unlock("Collector I")
        return messages

    def sale_price(self, plant: Plant) -> int:
        base = self.player.market_sell_prices[plant.species]
        if plant.rare_bloom:
            return base * 3
        return base + 5
