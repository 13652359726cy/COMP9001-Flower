from __future__ import annotations

from garden import ASCII_ART, BLUE, CYAN, SPECIES_DATA, center_in_width, center_line, color_text, display_species_name, pad_to_visible_width, safe_input, terminal_width


class EncyclopediaMixin:
    def show_encyclopedia(self) -> None:
        print(center_line(color_text("Encyclopedia", BLUE)))
        width = terminal_width()
        gap = "   "
        columns = 3
        col_width = max(10, (width - (columns - 1) * len(gap)) // columns)
        owned = set(self.player.owned_flowers)
        cards: list[dict[str, list[str]]] = []
        for species in SPECIES_DATA:
            art = ASCII_ART.get(species, "")
            art_lines = art.splitlines() if art else ["(missing ascii)"]
            if art_lines:
                art_lines = art_lines[:-1]
            name_line = display_species_name(species)
            if species in owned:
                name_line = color_text(f"{name_line}  owned", CYAN)
                art_lines = [color_text(line, CYAN) for line in art_lines]
            cards.append({"header": [name_line], "art": art_lines})
        rows: list[str] = []
        for row_start in range(0, len(cards), columns):
            row_cards = cards[row_start : row_start + columns]
            max_art_height = max((len(card["art"]) for card in row_cards), default=0)
            total_height = 2 + max_art_height
            formatted: list[list[str]] = []
            for card in row_cards:
                header = [center_in_width(line, col_width) for line in card["header"]]
                art_pad = [""] * max(0, max_art_height - len(card["art"]))
                art_block = [center_in_width(line, col_width) for line in (card["art"] + art_pad)]
                column_lines = header + [""] + art_block
                column_lines += [""] * max(0, total_height - len(column_lines))
                formatted.append(column_lines)
            for i in range(total_height):
                rows.append(gap.join(pad_to_visible_width(column[i], col_width) for column in formatted).rstrip())
            rows.append("")
        print("\n".join(rows).rstrip())
        safe_input("\nPress Enter to go back...")
