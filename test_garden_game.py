from garden_game import MAGENTA, bloom_colour_code


def test_bloom_colour_code_handles_rare_prefix() -> None:
    assert bloom_colour_code("Pink") == MAGENTA
    assert bloom_colour_code("Rare Pink") == MAGENTA


if __name__ == "__main__":
    test_bloom_colour_code_handles_rare_prefix()
    print("ok")
