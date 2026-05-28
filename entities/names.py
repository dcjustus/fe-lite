"""
Random name pools for units. Call reset() at the start of each battle.
"""
import random

ALLY_NAMES = [
    "Arden", "Lyra", "Cael", "Mira", "Theron", "Sable", "Kiran", "Oryn",
    "Faye", "Soren", "Wren", "Ember", "Fenn", "Gale", "Iris", "Jasper",
    "Lark", "Nova", "Pyre", "Quinn", "Rook", "Sage", "Thorn", "Blaze",
    "Dune", "Haze", "Koda", "Moss", "Zara", "Elys",
]

ENEMY_NAMES = [
    "Morg", "Drak", "Skorn", "Vael", "Greth", "Tyde", "Nox", "Rath",
    "Bane", "Crux", "Krag", "Murk", "Naeg", "Orn", "Quell", "Rive",
    "Slag", "Torx", "Ulk", "Wrath", "Xar", "Yog", "Zek", "Brax",
    "Cinder", "Dire", "Fell", "Grim", "Hex", "Iron",
]

_used: set = set()


def reset():
    _used.clear()


def get_name(team: str) -> str:
    pool = ALLY_NAMES if team == "ally" else ENEMY_NAMES
    available = [n for n in pool if n not in _used]
    if not available:
        available = pool   # recycle if exhausted
    name = random.choice(available)
    _used.add(name)
    return name
