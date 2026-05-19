from __future__ import annotations

from garden import BLUE, GREEN, RED, Plant, SPECIES_DATA, boxed_message, canonical_species, center_block, center_line, color_text, display_species_name, safe_input


class ShopMixin:
    def shop_menu(self) -> None:
        print(center_line(color_text("Seed Shop", BLUE)))
        rows: list[tuple[str, str]] = []
        for species in SPECIES_DATA:
            rows.append((display_species_name(species), f"{self.player.market_seed_prices[species]} coins"))
        left_width = max(len(left) for left, _ in rows) if rows else 0
        right_width = max(len(right) for _, right in rows) if rows else 0
        for left, right in rows:
            print(center_line(f"{left.rjust(left_width)} | {right.ljust(right_width)}"))
        choice = safe_input("Type species name to buy, or press Enter to go back: ")
        if not choice:
            return
        species = canonical_species(choice)
        if species not in SPECIES_DATA:
            print(color_text("Unknown seed type.", RED))
            return
        price = self.player.market_seed_prices[species]
        if self.player.coins < price:
            print(color_text("Not enough coins.", RED))
            return
        self.player.coins -= price
        self.player.plants.append(Plant(species=species, pot_id=self.player.next_pot_id))
        self.reindex_garden_pots()
        message = boxed_message("Seed Purchased", f"You successfully bought a {display_species_name(species)} seed!")
        print(color_text(center_block(message), GREEN))
        safe_input("\nPress Enter to continue...")
