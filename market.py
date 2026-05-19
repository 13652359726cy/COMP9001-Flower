from __future__ import annotations

from garden import BLUE, GREEN, RED, boxed_message, center_block, center_line, color_text, safe_input


class MarketMixin:
    def market_menu(self) -> None:
        print(center_line(color_text("Flower Market", BLUE)))
        if not self.player.harvested_flowers:
            print(center_line("You have no harvested flowers to sell."))
            safe_input("\nPress Enter to go back...")
            return
        for flower in self.player.harvested_flowers:
            price = self.sale_price(flower)
            rarity = "Rare" if flower.rare_bloom else "Standard"
            print(center_line(f"Flower {flower.item_id}: {flower.display_name()} | {rarity} | Sale price: {price}"))
        raw = safe_input("Choose flower id to sell, or press Enter to go back: ")
        if not raw:
            return
        if not raw.isdigit():
            print(color_text("Please enter a flower number.", RED))
            return
        item_id = int(raw)
        for flower in self.player.harvested_flowers:
            if flower.item_id == item_id:
                price = self.sale_price(flower)
                sold_name = flower.display_name()
                self.player.coins += price
                self.player.sold_today += 1
                self.player.harvested_flowers = [f for f in self.player.harvested_flowers if f.item_id != item_id]
                self.reindex_harvested_flowers()
                message = boxed_message("Flower Sold", f"You sold {sold_name} for {price} coins!")
                print(color_text(center_block(message), GREEN))
                safe_input("\nPress Enter to continue...")
                return
        print(color_text("That flower is not in your market inventory.", RED))
