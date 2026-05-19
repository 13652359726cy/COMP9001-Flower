from unittest.mock import patch

from garden_game import GardenGame, HarvestedFlower, MAGENTA, Plant, bloom_colour_code


def test_bloom_colour_code_handles_rare_prefix() -> None:
    assert bloom_colour_code("Pink") == MAGENTA
    assert bloom_colour_code("Rare Pink") == MAGENTA


def test_use_fertiliser_shows_cost_prompt() -> None:
    game = GardenGame()
    game.player.coins = 100
    game.player.plants = [Plant(species="Tulip", pot_id=1)]

    with patch("garden_game.safe_input", side_effect=["1"]) as mock_input:
        with patch("builtins.print"):
            game.use_fertiliser()

    assert mock_input.call_args_list[0].args[0] == "Choose pot id (Cost: 20, press Enter to cancel): "


def test_use_fertiliser_costs_20_coins() -> None:
    game = GardenGame()
    game.player.coins = 25
    game.player.plants = [Plant(species="Tulip", pot_id=1)]

    with patch("garden_game.safe_input", side_effect=["1"]):
        with patch("builtins.print"):
            game.use_fertiliser()

    assert game.player.coins == 5


def test_harvest_removes_plant_and_allows_repeat_same_species() -> None:
    game = GardenGame()
    game.player.plants = [
        Plant(species="Tulip", pot_id=4, stage=3),
        Plant(species="Tulip", pot_id=9, stage=3),
    ]
    game.player.owned_flowers = []
    game.player.encyclopedia = []
    game.player.harvested_flowers = []

    with patch("garden_game.safe_input", side_effect=["1", "1"]):
        with patch("builtins.print"):
            game.reindex_garden_pots()
            game.harvest_flower()
            game.harvest_flower()

    assert [plant.pot_id for plant in game.player.plants] == []
    assert game.player.owned_flowers == ["Tulip", "Tulip"]
    assert game.player.encyclopedia == ["Tulip"]
    assert [flower.item_id for flower in game.player.harvested_flowers] == [1, 2]
    assert [flower.species for flower in game.player.harvested_flowers] == ["Tulip", "Tulip"]


def test_market_menu_waits_when_no_blooming_plants() -> None:
    game = GardenGame()
    game.player.harvested_flowers = []

    with patch("garden_game.safe_input", return_value="") as mock_input:
        with patch("builtins.print"):
            game.market_menu()

    assert mock_input.call_args_list[0].args[0] == "\nPress Enter to go back..."


def test_market_sells_harvested_flowers_instead_of_garden_plants() -> None:
    game = GardenGame()
    game.player.coins = 0
    game.player.harvested_flowers = [
        HarvestedFlower(item_id=1, species="Rose", bloom_color="Pink", rare_bloom=False),
        HarvestedFlower(item_id=2, species="Tulip", rare_bloom=False),
    ]

    with patch("garden_game.safe_input", side_effect=["1", ""]) as mock_input:
        with patch("builtins.print"):
            game.market_menu()

    assert game.player.coins == game.player.market_sell_prices["Rose"] + 5
    assert [flower.item_id for flower in game.player.harvested_flowers] == [1]
    assert game.player.harvested_flowers[0].species == "Tulip"
    assert mock_input.call_args_list[1].args[0] == "\nPress Enter to continue..."


def test_reindex_garden_pots_keeps_ids_starting_from_one() -> None:
    game = GardenGame()
    game.player.plants = [
        Plant(species="Daisy", pot_id=4),
        Plant(species="Rose", pot_id=6),
        Plant(species="Tulip", pot_id=10),
    ]

    game.reindex_garden_pots()

    assert [plant.pot_id for plant in game.player.plants] == [1, 2, 3]
    assert game.player.next_pot_id == 4


if __name__ == "__main__":
    test_bloom_colour_code_handles_rare_prefix()
    test_use_fertiliser_shows_cost_prompt()
    test_use_fertiliser_costs_20_coins()
    test_harvest_removes_plant_and_allows_repeat_same_species()
    test_market_menu_waits_when_no_blooming_plants()
    test_market_sells_harvested_flowers_instead_of_garden_plants()
    test_reindex_garden_pots_keeps_ids_starting_from_one()
    print("ok")
