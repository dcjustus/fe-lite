"""
Random battlefield generation: unit placement, cosmetic terrain, treasure chests.
"""
import random
import math
import pygame
from core.constants import SCREEN_W, SCREEN_H
from entities.unit import Unit
from entities.unit_classes import ALL_CLASSES
from systems.items import random_chest_item


MIN_UNIT_GAP   = 65
SPAWN_MARGIN   = 60
CHEST_INTERACT = 60    # px — how close a unit must be to open a chest


def generate_battlefield():
    """Return (allies, enemies, terrain, chests)."""
    count   = random.randint(3, 5)
    allies  = _place_units(count, "ally",  left=True)
    enemies = _place_units(count, "enemy", left=False)
    terrain = _generate_terrain()
    chests  = _generate_chests()
    return allies, enemies, terrain, chests


def _place_units(count, team, left):
    units = []
    if left:
        x_lo, x_hi = SPAWN_MARGIN, SCREEN_W // 3
    else:
        x_lo, x_hi = SCREEN_W * 2 // 3, SCREEN_W - SPAWN_MARGIN
    y_lo, y_hi = SPAWN_MARGIN + 40, SCREEN_H - SPAWN_MARGIN - 40

    attempts = 0
    while len(units) < count and attempts < 500:
        attempts += 1
        x   = random.randint(x_lo, x_hi)
        y   = random.randint(y_lo, y_hi)
        cls = random.choice(ALL_CLASSES)
        if any(math.hypot(x - u.x, y - u.y) < MIN_UNIT_GAP for u in units):
            continue
        units.append(Unit(cls, team, x, y))
    return units


# ── Cosmetic terrain ──────────────────────────────────────────────────────────

class TerrainPiece:
    def __init__(self, kind, x, y, size, color):
        self.kind  = kind
        self.x, self.y = x, y
        self.size  = size
        self.color = color

    def draw(self, surface):
        if self.kind == "tree":
            _draw_tree(surface, self.x, self.y, self.size, self.color)
        elif self.kind == "rock":
            _draw_rock(surface, self.x, self.y, self.size, self.color)


def _generate_terrain():
    pieces = []
    cx_lo, cx_hi = SCREEN_W // 3, SCREEN_W * 2 // 3
    for _ in range(random.randint(4, 9)):
        kind  = random.choice(["tree", "tree", "rock"])
        x     = random.randint(cx_lo, cx_hi)
        y     = random.randint(80, SCREEN_H - 80)
        size  = random.randint(18, 32)
        color = ((34, 120, 50) if kind == "tree" else (110, 100, 90))
        pieces.append(TerrainPiece(kind, x, y, size, color))
    return pieces


# ── Treasure chests ───────────────────────────────────────────────────────────

class TreasureChest:
    def __init__(self, x, y):
        self.x      = float(x)
        self.y      = float(y)
        self.opened = False
        self.item   = random_chest_item()

    def in_range(self, unit):
        return math.hypot(unit.x - self.x, unit.y - self.y) <= CHEST_INTERACT

    def draw(self, surface):
        ix, iy = int(self.x), int(self.y)
        w, h   = 22, 16
        if self.opened:
            # Drawn open (flat lid, gray)
            pygame.draw.rect(surface, (90, 70, 40), (ix - w//2, iy - h//2, w, h), border_radius=3)
            pygame.draw.rect(surface, (60, 45, 20), (ix - w//2, iy - h//2, w, h), 1, border_radius=3)
        else:
            # Closed chest (golden)
            pygame.draw.rect(surface, (160, 110, 30), (ix - w//2, iy - h//2, w, h), border_radius=3)
            pygame.draw.rect(surface, (220, 170, 60), (ix - w//2, iy - h//2, w, h//2), border_radius=3)
            pygame.draw.rect(surface, (80,  55,  10), (ix - w//2, iy - h//2, w, h), 1, border_radius=3)
            # Lock dot
            pygame.draw.circle(surface, (80, 55, 10), (ix, iy), 3)
            import core.constants as C
            if C.FONT_SM:
                lbl = C.FONT_SM.render("?", True, (255, 240, 180))
                surface.blit(lbl, lbl.get_rect(center=(ix, iy - h - 4)))


def _generate_chests():
    chests  = []
    cx_lo   = SCREEN_W // 3 + 40
    cx_hi   = SCREEN_W * 2 // 3 - 40
    count   = random.randint(1, 3)
    attempts = 0
    while len(chests) < count and attempts < 200:
        attempts += 1
        x = random.randint(cx_lo, cx_hi)
        y = random.randint(100, SCREEN_H - 100)
        if any(math.hypot(x - c.x, y - c.y) < 80 for c in chests):
            continue
        chests.append(TreasureChest(x, y))
    return chests


# ── Draw helpers ──────────────────────────────────────────────────────────────

def _draw_tree(surface, x, y, size, color):
    pygame.draw.rect(surface, (90, 60, 30), (x - 4, y, 8, size // 2))
    pygame.draw.polygon(surface, color, [
        (x, y - size), (x - size, y + size // 3), (x + size, y + size // 3),
    ])


def _draw_rock(surface, x, y, size, color):
    pygame.draw.ellipse(surface, color, (x - size, y - size // 2, size * 2, size))
    darker = tuple(max(0, c - 30) for c in color)
    pygame.draw.ellipse(surface, darker, (x - size, y - size // 2, size * 2, size), 2)
