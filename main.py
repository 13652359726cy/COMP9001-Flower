from __future__ import annotations

import time

from encyclopedia import EncyclopediaMixin
from garden import CYAN, GREEN, MAGENTA, RED, SAVE_PATH, GardenGameBase, center_block, center_line, clear_terminal, color_text, safe_input
from market import MarketMixin
from shop import ShopMixin


class GardenGame(GardenGameBase, ShopMixin, MarketMixin, EncyclopediaMixin):
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
        if not events and not bloom_happened and not reward:
            print(center_line("It was a quiet night in the garden."))
        safe_input("\nPress Enter to wake up to a new day... ")
        time.sleep(0.2)

    def delete_save(self) -> None:
        print(center_line(color_text("Delete Save", RED)))
        confirm = safe_input("Type DELETE to confirm, or press Enter to cancel: ")
        if confirm.strip().upper() != "DELETE":
            print(color_text("Cancelled.", "\033[33m"))
            return
        try:
            if SAVE_PATH.exists():
                SAVE_PATH.unlink()
        except OSError:
            print(color_text("Could not delete save file.", RED))
            return
        self.player = self.load_or_create_state()
        print(color_text("Save deleted. A new garden has been started.", GREEN))

    def run(self) -> None:
        while self.running:
            clear_terminal()
            print(center_block(self.title_screen()))
            self.print_status()
            choice = safe_input(
                "\nChoose: [1] Garden [2] Shop [3] Market [4] Encyclopedia [5] Sleep [6] Save & Quit [7] Delete Save\n> "
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
                clear_terminal()
                self.end_day()
            elif choice == "6":
                self.save()
                print(color_text("Progress saved. See you in the garden.", CYAN))
                self.running = False
            elif choice == "7":
                self.delete_save()
            else:
                print(color_text("Please choose a valid menu option.", RED))


def main() -> None:
    game = GardenGame()
    game.run()


if __name__ == "__main__":
    main()
