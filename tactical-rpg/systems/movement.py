"""
Movement helpers: clamp a destination to within a unit's movement radius,
and check point-in-circle membership.
"""
import math


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
