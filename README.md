## Bloom & Bust Garden

Run instructions:
1. Open this folder in a terminal.
2. Run: python3 main.py
3. The game will create garden_save.json automatically when you save or end the day.

Project summary:
Bloom & Bust Garden is a terminal-based flower market simulation game. The player buys seeds, manages
multiple pots, waters plants, uses strategic items, and waits for flowers to bloom. When a plant reaches
the bloom stage, it may mutate into a rare colour variant that can be sold for a much higher price. The
player also completes daily quests and fills an encyclopedia of discovered blooms.

Features implemented:
- Multiple plant pots with water, health, growth stage, and alive/withered status
- ASCII flower art loaded from the provided ASCII asset file
- Dynamic market prices for seeds and flower sales
- Bloom mutation system with rare colour variants
- Daily quests with coin rewards
- Encyclopedia collection system
- Save/load system using JSON
- Modular design using classes, dataclasses, functions, file I/O, and structured data

Advanced topics used:
- Object-oriented programming with multiple classes
- File input/output with JSON persistence
- Dataclasses for structured game state
- Randomised simulation and state-driven gameplay logic

Notes for marking:
- Main entry point: main.py
- Core game logic: garden_game.py
- No external libraries are required
