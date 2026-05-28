"""
Movement helpers: clamp a destination to within a unit's movement radius,
point-in-circle test, and terrain interaction queries.
"""
import math

from core.constants import TERRAIN_DEFS, MAX_TERRAIN_EVASION
from systems.items import MAGIC


def clamp_to_radius(ux, uy, tx, ty, radius):
    """Return (x, y) clamped so it stays within `radius` pixels of (ux, uy)."""
    dx, dy = tx - ux, ty - uy
    dist = math.hypot(dx, dy)
    if dist <= radius:
        return tx, ty
    scale = radius / dist
    return ux + dx * scale, uy + dy * scale


def point_in_circle(px, py, cx, cy, radius):
    return math.hypot(px - cx, py - cy) <= radius


def move_toward(unit, target, allies, enemies):
    """
    Move `unit` as close as possible toward `target` position (tx, ty),
    staying within unit.mov_radius. Returns new (x, y).
    """
    tx, ty = target
    nx, ny = clamp_to_radius(unit.x, unit.y, tx, ty, unit.mov_radius)
    return nx, ny


# ── Terrain helpers ───────────────────────────────────────────────────────────

def _terrain_radius(piece):
    """Approximate circular gameplay radius for a terrain piece."""
    # Trees span roughly ±size from centre; rocks are a flatter ellipse so 0.7×.
    return piece.size if piece.kind == "tree" else piece.size * 0.7


def _segment_crosses_circle(x1, y1, x2, y2, cx, cy, r):
    """True if segment (x1,y1)→(x2,y2) passes within r pixels of (cx,cy)."""
    dx, dy = x2 - x1, y2 - y1
    len_sq = dx * dx + dy * dy
    if len_sq == 0:
        return math.hypot(x1 - cx, y1 - cy) <= r
    t = max(0.0, min(1.0, ((cx - x1) * dx + (cy - y1) * dy) / len_sq))
    return math.hypot(x1 + t * dx - cx, y1 + t * dy - cy) <= r


def unit_terrain(unit, terrain_pieces):
    """Return list of terrain pieces the unit is currently standing inside."""
    return [
        p for p in terrain_pieces
        if math.hypot(unit.x - p.x, unit.y - p.y) <= _terrain_radius(p)
    ]


def terrain_evasion_bonus(unit, terrain_pieces):
    """
    Return total evasion % granted by terrain the unit is standing in.
    Capped at MAX_TERRAIN_EVASION so stacked terrain can't make a unit unhittable.
    """
    bonus = sum(
        TERRAIN_DEFS.get(p.kind, {}).get("evasion", 0)
        for p in unit_terrain(unit, terrain_pieces)
    )
    return min(bonus, MAX_TERRAIN_EVASION)


def path_terrain_cost(x1, y1, x2, y2, terrain_pieces, weapon):
    """
    Return (extra_pixel_cost, terrain_label_set) for crossing terrain on the
    straight-line path from (x1,y1) to (x2,y2).

    Mages (MAGIC weapon) pay no movement cost — they float over terrain.
    Each terrain piece whose circle the path crosses adds its move_cost once.
    """
    if weapon == MAGIC:
        return 0, set()
    cost   = 0
    labels = set()
    for piece in terrain_pieces:
        r = _terrain_radius(piece)
        if _segment_crosses_circle(x1, y1, x2, y2, piece.x, piece.y, r):
            tdef = TERRAIN_DEFS.get(piece.kind, {})
            cost += tdef.get("move_cost", 0)
            if "label" in tdef:
                labels.add(tdef["label"])
    return cost, labels
