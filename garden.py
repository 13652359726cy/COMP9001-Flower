from __future__ import annotations

import json
import random
import re
import shutil
from dataclasses import dataclass, field
from pathlib import Path


SAVE_PATH = Path(__file__).with_name("garden_save.json")
ASCII_PATH = Path(__file__).with_name("ASCII.txt")


RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"


SPECIES_DATA = {
    "Tulip": {"seed_price": 12, "sell_price": 30, "water_need": 5},
    "Sunflower": {"seed_price": 15, "sell_price": 36, "water_need": 6},
    "Rose": {"seed_price": 20, "sell_price": 48, "water_need": 5},
    "Daisy": {"seed_price": 10, "sell_price": 24, "water_need": 5},
    "Lily": {"seed_price": 18, "sell_price": 42, "water_need": 4},
    "Valley_Lily": {"seed_price": 16, "sell_price": 38, "water_need": 4},
    "Magnolia": {"seed_price": 19, "sell_price": 46, "water_need": 5},
    "Morning_Glory": {"seed_price": 14, "sell_price": 34, "water_need": 6},
    "Peony": {"seed_price": 21, "sell_price": 52, "water_need": 5},
    "Carnation": {"seed_price": 13, "sell_price": 32, "water_need": 5},
    "Moth_Orchid": {"seed_price": 22, "sell_price": 55, "water_need": 4},
}

COLOR_VARIANTS = [("Pink", MAGENTA), ("Yellow", YELLOW), ("Blue", CYAN), ("Green", GREEN)]
COLOR_VARIANT_CODES = {name: code for name, code in COLOR_VARIANTS}
STAGE_NAMES = ["Seed", "Sprout", "Growing", "Bloom"]
STAGE_DURATIONS = [0, 1, 2, 4]
ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def bloom_colour_code(bloom_color: str | None) -> str | None:
    if not bloom_color:
        return None
    name = bloom_color.removeprefix("Rare ").strip()
    return COLOR_VARIANT_CODES.get(name)


def display_species_name(species: str) -> str:
    return species.replace("_", " ")


def canonical_species(raw: str) -> str:
    cleaned = raw.strip().replace(" ", "_")
    parts = [part for part in cleaned.split("_") if part]
    return "_".join(part[:1].upper() + part[1:].lower() for part in parts)


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def safe_input(prompt: str) -> str:
    try:
        return input(prompt).strip()
    except EOFError:
        return "6"


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


def visible_len(text: str) -> int:
    return len(ANSI_RE.sub("", text))


def center_line(line: str, width: int | None = None) -> str:
    width = width or terminal_width()
    stripped = line.rstrip("\n")
    pad = max(0, (width - visible_len(stripped)) // 2)
    return (" " * pad) + stripped


def center_in_width(text: str, width: int) -> str:
    stripped = text.rstrip("\n")
    padding = max(0, (width - visible_len(stripped)) // 2)
    return (" " * padding) + stripped


def pad_to_visible_width(text: str, width: int) -> str:
    padding = max(0, width - visible_len(text))
    return text + (" " * padding)


def center_block(text: str) -> str:
    width = terminal_width()
    return "\n".join(center_line(line, width) for line in text.splitlines())


def clear_terminal() -> None:
    print("\033[2J\033[H", end="")


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
            if "(bloom" in current:
                current = current.split("(bloom", 1)[0].strip()
            current = current.replace(" ", "_")
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
    revived_once: bool = False
    full_water_streak: int = 0
    rescued_from_low_health: bool = False

    def display_name(self) -> str:
        return display_species_name(self.species)

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
            events.append(f"Pot {self.pot_id}: {self.display_name()} was overwatered and lost a bit of health.")
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
            events.append(f"Pot {self.pot_id}: {self.display_name()} advanced to {STAGE_NAMES[new_stage]}.")
            self.stage = new_stage
        return events

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "Plant":
        payload = dict(data)
        payload.pop("mutation_boost", None)
        if "species" in payload:
            payload["species"] = payload["species"].replace(" ", "_")
        return cls(**payload)


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
class HarvestedFlower:
    item_id: int
    species: str
    bloom_color: str | None = None
    rare_bloom: bool = False

    def display_name(self) -> str:
        if self.bloom_color:
            return f"{self.bloom_color} {display_species_name(self.species)}"
        return display_species_name(self.species)

    def to_dict(self) -> dict:
        return self.__dict__.copy()

    @classmethod
    def from_dict(cls, data: dict) -> "HarvestedFlower":
        payload = dict(data)
        if "species" in payload:
            payload["species"] = payload["species"].replace(" ", "_")
        return cls(**payload)


@dataclass
class PlayerState:
    coins: int = 90
    day: int = 1
    plants: list[Plant] = field(default_factory=list)
    encyclopedia: list[str] = field(default_factory=list)
    owned_flowers: list[str] = field(default_factory=list)
    harvested_flowers: list[HarvestedFlower] = field(default_factory=list)
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
            "owned_flowers": self.owned_flowers,
            "harvested_flowers": [flower.to_dict() for flower in self.harvested_flowers],
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
        state.owned_flowers = data.get("owned_flowers", [])
        state.harvested_flowers = [HarvestedFlower.from_dict(item) for item in data.get("harvested_flowers", [])]
        state.market_seed_prices = data["market_seed_prices"]
        state.market_sell_prices = data["market_sell_prices"]
        state.sold_today = data["sold_today"]
        state.revived_today = data["revived_today"]
        quest_data = data["current_quest"]
        state.current_quest = Quest.from_dict(quest_data) if quest_data else None
        state.next_pot_id = data["next_pot_id"]
        return state


class GardenGameBase:
    def __init__(self) -> None:
        self.player = self.load_or_create_state()
        self.running = True

    def reindex_garden_pots(self) -> None:
        for index, plant in enumerate(self.player.plants, start=1):
            plant.pot_id = index
        self.player.next_pot_id = len(self.player.plants) + 1

    def reindex_harvested_flowers(self) -> None:
        for index, flower in enumerate(self.player.harvested_flowers, start=1):
            flower.item_id = index

    def refresh_market_prices(self, state: PlayerState, initial: bool = False) -> None:
        for species, info in SPECIES_DATA.items():
            if initial:
                seed = info["seed_price"]
                sell = info["sell_price"]
            else:
                seed = state.market_seed_prices.get(species, info["seed_price"]) + random.randint(-3, 4)
                sell = state.market_sell_prices.get(species, info["sell_price"]) + random.randint(-5, 6)
            state.market_seed_prices[species] = clamp(seed, max(6, info["seed_price"] - 5), info["seed_price"] + 10)
            state.market_sell_prices[species] = clamp(sell, max(14, info["sell_price"] - 10), info["sell_price"] + 18)

    def load_or_create_state(self) -> PlayerState:
        if SAVE_PATH.exists():
            try:
                data = json.loads(SAVE_PATH.read_text(encoding="utf-8"))
                state = PlayerState.from_dict(data)
                self.refresh_market_prices(state, initial=False)
                for plant in state.plants:
                    plant.species = plant.species.replace(" ", "_")
                    if plant.species == "Orchid":
                        plant.species = "Moth_Orchid"
                self.player = state
                self.reindex_garden_pots()
                self.reindex_harvested_flowers()
                return state
            except (json.JSONDecodeError, KeyError, TypeError):
                pass
        state = PlayerState()
        self.refresh_market_prices(state, initial=True)
        state.current_quest = self.generate_quest(state)
        self.player = state
        self.reindex_garden_pots()
        return state

    def save(self) -> None:
        SAVE_PATH.write_text(json.dumps(self.player.to_dict(), ensure_ascii=False, indent=2), encoding="utf-8")

    def title_screen(self) -> str:
        pot_art = ASCII_ART.get("Pot", "")
        seed_art = ASCII_ART.get("Seed", "")
        return color_text("Bloom & Bust Garden", GREEN) + "\nA terminal flower market game built for COMP9001.\n" + seed_art + "\n" + pot_art + "\n"

    def print_status(self) -> None:
        quest = self.player.current_quest.description if self.player.current_quest else "None"
        status = (
            f"{BOLD}Day {self.player.day}{RESET}  "
            f"Coins: {color_text(str(self.player.coins), YELLOW)}  "
            f"Plants: {len(self.player.plants)}  "
            f"Quest: {quest}"
        )
        print(center_line(status))

    def generate_quest(self, state: PlayerState) -> Quest:
        quests = [Quest(name="New Roots", description="Own at least one plant by the end of the day.", reward=15, quest_type="own_one")]
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
            quests.append(Quest(name="Market Day", description="Sell at least one blooming plant today.", reward=18, quest_type="sell_once"))
        if withered:
            quests.append(Quest(name="Emergency Care", description="Revive one withered plant today.", reward=30, quest_type="revive_once"))
        return random.choice(quests)

    def resolve_bloom(self, plant: Plant) -> None:
        mutated = random.random() < 1
        plant.rare_bloom = mutated
        if mutated:
            colour_name, colour_code = random.choice(COLOR_VARIANTS)
            plant.bloom_color = colour_name
        else:
            colour_name, colour_code = None, None
            plant.bloom_color = None
        art = ASCII_ART.get(plant.species, "")
        if art:
            print(center_block(art))
        if mutated:
            print(center_line(sparkles()))
        print(center_line(color_text(f"Pot {plant.pot_id} bloomed into a {colour_name} {plant.species}.", colour_code) if mutated and colour_name and colour_code else f"Pot {plant.pot_id} bloomed into a {plant.species}."))
        if mutated and colour_name:
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

    def sale_price(self, item: Plant | HarvestedFlower) -> int:
        base = self.player.market_sell_prices[item.species]
        if item.rare_bloom:
            return base * 3
        return base + 5

    def garden_menu(self) -> None:
        while True:
            self.show_garden()
            choice = safe_input("\nGarden: [1] Water [2] Fertiliser [3] Revival Idol [4] Harvest (press Enter to go back)\n> ")
            if choice == "":
                return
            if choice == "1":
                self.water_plant()
            elif choice == "2":
                self.use_fertiliser()
            elif choice == "3":
                self.use_revival_idol()
            elif choice == "4":
                self.harvest_flower()
            else:
                print(color_text("That option is not available.", RED))

    def harvest_flower(self) -> None:
        plant = self.select_plant()
        if not plant:
            return
        if not plant.is_alive:
            print(color_text("You cannot harvest a withered plant.", RED))
            return
        if plant.stage != 3:
            print(color_text("You can only harvest flowers at the Bloom stage.", RED))
            return
        harvested_name = plant.display_name()
        harvested_pot_id = plant.pot_id
        self.player.owned_flowers.append(plant.species)
        if plant.species not in self.player.encyclopedia:
            self.player.encyclopedia.append(plant.species)
        self.player.harvested_flowers.append(
            HarvestedFlower(
                item_id=len(self.player.harvested_flowers) + 1,
                species=plant.species,
                bloom_color=plant.bloom_color,
                rare_bloom=plant.rare_bloom,
            )
        )
        self.player.plants = [p for p in self.player.plants if p.pot_id != harvested_pot_id]
        self.reindex_garden_pots()
        self.reindex_harvested_flowers()
        print(color_text(f"Harvested: {harvested_name} from pot {harvested_pot_id}.", CYAN))

    def show_garden(self) -> None:
        print(center_line(color_text("Garden Overview", BLUE)))
        if not self.player.plants:
            print(center_line("You do not own any plants yet."))
            return
        pot_art_lines = ASCII_ART.get("Pot", "").splitlines()
        if pot_art_lines:
            pot_art_lines = pot_art_lines[1:]
        cards: list[dict[str, list[str]]] = []
        for plant in self.player.plants:
            alive_text = color_text("Alive", GREEN) if plant.is_alive else color_text("Withered", RED)
            bloom_text = plant.bloom_color or "-"
            info_line_1 = f"Pot {plant.pot_id}||{plant.display_name()}||Stage:{STAGE_NAMES[plant.stage]}"
            info_line_2 = f"Water:{plant.water_level}/10||Health:{plant.health}/10"
            info_line_3 = f"Bloom:{bloom_text}||{alive_text}"
            if not plant.is_alive:
                flower_art = ASCII_ART.get("Withered", "")
            elif plant.stage == 0:
                flower_art = ASCII_ART.get("Seed", "")
            elif plant.stage == 1:
                flower_art = ASCII_ART.get("Sprout", "")
            elif plant.stage == 2:
                flower_art = ASCII_ART.get("Growing", "")
            else:
                flower_art = ASCII_ART.get(plant.species, "")
            flower_lines = flower_art.splitlines() if flower_art else []
            if plant.is_alive and plant.stage == 3 and flower_lines:
                flower_lines = flower_lines[:-1]
            colour_code = bloom_colour_code(plant.bloom_color) if plant.is_alive and plant.stage == 3 else None
            if colour_code:
                flower_lines = [color_text(line, colour_code) for line in flower_lines]
            cards.append({"header": [info_line_1, info_line_2, info_line_3], "flower": flower_lines, "pot": pot_art_lines})
        width = terminal_width()
        gap = "   "
        columns = 3
        col_width = max(10, (width - (columns - 1) * len(gap)) // columns)
        rows: list[str] = []
        for row_start in range(0, len(cards), columns):
            row_cards = cards[row_start : row_start + columns]
            max_flower_height = max((len(card["flower"]) for card in row_cards), default=0)
            pot_height = max((len(card["pot"]) for card in row_cards), default=0)
            total_height = 4 + max_flower_height + pot_height
            formatted: list[list[str]] = []
            for card in row_cards:
                header = [center_in_width(line, col_width) for line in card["header"]]
                flower_pad = [""] * max(0, max_flower_height - len(card["flower"]))
                flower_block = [center_in_width(line, col_width) for line in (flower_pad + card["flower"])]
                pot_block = [center_in_width(line, col_width) for line in card["pot"]]
                pot_block += [""] * max(0, pot_height - len(pot_block))
                column_lines = header + [""] + flower_block + pot_block
                column_lines += [""] * max(0, total_height - len(column_lines))
                formatted.append(column_lines)
            for i in range(total_height):
                parts = [pad_to_visible_width(column[i], col_width) for column in formatted]
                rows.append(gap.join(parts).rstrip())
            rows.append("")
        print("\n".join(rows).rstrip())

    def select_plant(self, allow_dead: bool = False, prompt: str = "Choose pot id: ") -> Plant | None:
        if not self.player.plants:
            print("You have no plants.")
            return None
        raw = safe_input(prompt)
        if raw == "":
            return None
        if not raw.isdigit():
            print(color_text("Please enter a pot number.", RED))
            return None
        pot_id = int(raw)
        for plant in self.player.plants:
            if plant.pot_id == pot_id:
                if plant.is_alive or allow_dead:
                    return plant
                print(color_text("That plant has withered. Use Revival Idol to bring it back.", RED))
                safe_input("\nPress Enter to continue...")
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
        print(color_text(f"You watered pot {plant.pot_id}. Water is now {plant.water_level}.", GREEN) + extra)

    def use_fertiliser(self) -> None:
        cost = 20
        if self.player.coins < cost:
            print(color_text("Not enough coins for fertiliser.", RED))
            return
        plant = self.select_plant(prompt="Choose pot id (Cost: 20, press Enter to cancel): ")
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

    def use_revival_idol(self) -> None:
        cost = 40
        if self.player.coins < cost:
            print(color_text("Not enough coins for revival idol.", RED))
            return
        plant = self.select_plant(allow_dead=True, prompt="Choose pot id (Cost: 40, press Enter to cancel): ")
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
