"""
Unit class definitions.
STR = physical attack  |  DEF = physical resistance
INT = magic attack     |  RES = magic resistance
SPD = speed (double hit if ≥ enemy SPD × 1.4)
MOV = movement stat (× MOV_SCALE px per point)

Balance target: ~8-12 neutral damage per hit, ~3-4 hits to kill most units.
Knights are the exception: durable against physical but vulnerable to magic.
"""
from systems.items import SWORD, AXE, LANCE, BOW, MAGIC

CLASS_DEFS = {
    "Fighter": {
        "weapon":      SWORD,
        "max_hp":      32,
        "strength":    17,
        "defense":     7,
        "intelligence":5,
        "resistance":  10,    # raised: Fighters survive magic, Warriors stay vulnerable
        "speed":       7,
        "movement":    5,
        "description": "Balanced warrior. Sword beats Axe.",
    },
    "Warrior": {
        "weapon":      AXE,
        "max_hp":      40,
        "strength":    20,    # high damage
        "defense":     10,
        "intelligence":2,
        "resistance":  3,     # very weak to magic
        "speed":       5,
        "movement":    4,
        "description": "Brawler. High HP/STR but very vulnerable to magic.",
    },
    "Knight": {
        "weapon":      LANCE,
        "max_hp":      26,
        "strength":    19,    # raised: disadvantaged matchups now deal ~6 dmg instead of 1
        "defense":     9,     # durable but not unkillable (down from 18)
        "intelligence":3,
        "resistance":  9,
        "speed":       4,
        "movement":    4,     # raised: same as Warrior — slow but not glacial
        "description": "Armored. Decent DEF/RES but low HP and speed.",
    },
    "Archer": {
        "weapon":      BOW,
        "max_hp":      28,
        "strength":    17,
        "defense":     5,
        "intelligence":5,
        "resistance":  6,
        "speed":       9,
        "movement":    5,
        "description": "Ranged. Cannot target enemies closer than 80 units.",
    },
    "Mage": {
        "weapon":      MAGIC,
        "max_hp":      20,
        "strength":    4,
        "defense":     3,
        "intelligence":20,    # devastating magic
        "resistance":  8,
        "speed":       10,
        "movement":    5,
        "description": "Full-range attacker. Fragile but hits INT vs RES.",
    },
}

ALL_CLASSES = list(CLASS_DEFS.keys())
