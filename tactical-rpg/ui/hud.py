"""
HUD: top phase banner + bottom log strip (which also shows the action hint).
"""
import pygame
import core.constants as C
from core.constants import (
    SCREEN_W, SCREEN_H,
    UI_BG, UI_BORDER, UI_TEXT, UI_TEXT_DIM,
    ALLY_COLOR, ENEMY_COLOR, WHITE,
)

LOG_H         = 120
LOG_MAX_LINES = 5
LOG_PAD       = 6
LINE_H        = 17
HINT_H        = 18     # space reserved at top of log box for the hint line


class HUD:
    def __init__(self):
        self._log_lines: list[str] = []

    def push_log(self, lines):
        if isinstance(lines, str):
            lines = [lines]
        self._log_lines.extend(lines)
        # Keep only the last N×3 lines in memory
        if len(self._log_lines) > LOG_MAX_LINES * 4:
            self._log_lines = self._log_lines[-LOG_MAX_LINES * 4:]

    def draw(self, surface, phase, turn_num, allies, enemies, hint: str = ""):
        self._draw_log(surface, hint)
        self._draw_phase_banner(surface, phase, turn_num, allies, enemies)

    # ── Internal ─────────────────────────────────────────────────────────────

    def _draw_log(self, surface, hint: str):
        y0 = SCREEN_H - LOG_H
        pygame.draw.rect(surface, (14, 14, 20), (0, y0, SCREEN_W, LOG_H))
        pygame.draw.line(surface, UI_BORDER, (0, y0), (SCREEN_W, y0), 1)

        # Hint line — dimmed, at top of the box
        if hint:
            ht = C.FONT_SM.render(f"  {hint}", True, (90, 90, 108))
            surface.blit(ht, (LOG_PAD, y0 + 3))

        # Log lines start below the hint
        recent  = self._log_lines[-LOG_MAX_LINES:]
        lines_y = y0 + HINT_H + 2
        for i, line in enumerate(recent):
            col = UI_TEXT if i == len(recent) - 1 else UI_TEXT_DIM
            txt = C.FONT_SM.render(line, True, col)
            surface.blit(txt, (LOG_PAD, lines_y + i * LINE_H))

    def _draw_phase_banner(self, surface, phase, turn_num, allies, enemies):
        alive_a = sum(1 for u in allies  if u.alive)
        alive_e = sum(1 for u in enemies if u.alive)

        bar_h = 34
        pygame.draw.rect(surface, (14, 14, 20), (0, 0, SCREEN_W, bar_h))
        pygame.draw.line(surface, UI_BORDER, (0, bar_h), (SCREEN_W, bar_h), 1)

        if phase == "player":
            label, col = "PLAYER PHASE", ALLY_COLOR
        elif phase == "enemy":
            label, col = "ENEMY PHASE",  ENEMY_COLOR
        else:
            label, col = phase.upper(), WHITE

        txt = C.FONT_LG.render(label, True, col)
        surface.blit(txt, txt.get_rect(centerx=SCREEN_W // 2, centery=bar_h // 2))

        turn_txt = C.FONT_MD.render(f"Turn {turn_num}", True, UI_TEXT_DIM)
        surface.blit(turn_txt, (10, 8))

        at = C.FONT_MD.render(f"Allies: {alive_a}",  True, ALLY_COLOR)
        et = C.FONT_MD.render(f"Enemies: {alive_e}", True, ENEMY_COLOR)
        surface.blit(at, at.get_rect(right=SCREEN_W - 110, centery=bar_h // 2))
        surface.blit(et, et.get_rect(right=SCREEN_W - 8,   centery=bar_h // 2))
