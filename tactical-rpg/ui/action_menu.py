"""
Post-move action menu: Attack, Item (sub-list), Open Chest, Back, Wait.
"""
import pygame
import core.constants as C
from core.constants import (
    UI_BG, UI_BORDER, UI_TEXT, UI_HIGHLIGHT, UI_TEXT_DIM, WHITE,
)

ITEM_H   = 30
MENU_W   = 160
PADDING  = 6


class ActionMenu:
    """
    Shown after a unit moves.
    Options: Attack | Item (if any) | Open Chest (if nearby) | Back | Wait
    """

    def __init__(self, unit, x, y, extra=None):
        self.unit    = unit
        options      = ["Attack"]
        if unit.usable_items():
            options.append("Item")
        if extra:
            options.extend(extra)
        options.append("Back")   # always — undoes the move
        options.append("Wait")
        self.options = options
        self.hovered = 0

        from core.constants import SCREEN_W, SCREEN_H
        mx = min(x + 30, SCREEN_W - MENU_W - 4)
        my = min(y - ITEM_H, SCREEN_H - len(options) * ITEM_H - 40)
        self.rect = pygame.Rect(mx, my, MENU_W, len(options) * ITEM_H + PADDING)

    def handle_event(self, event):
        """Return chosen option string, 'close' to dismiss, or None."""
        if event.type == pygame.MOUSEMOTION:
            for i in range(len(self.options)):
                if self._row_rect(i).collidepoint(event.pos):
                    self.hovered = i

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, opt in enumerate(self.options):
                if self._row_rect(i).collidepoint(event.pos):
                    return opt
            return "close"

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.hovered = (self.hovered - 1) % len(self.options)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.hovered = (self.hovered + 1) % len(self.options)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.options[self.hovered]
            if event.key == pygame.K_ESCAPE:
                return "Back"

        return None

    def draw(self, surface):
        pygame.draw.rect(surface, UI_BG, self.rect, border_radius=5)
        pygame.draw.rect(surface, UI_BORDER, self.rect, 1, border_radius=5)
        for i, opt in enumerate(self.options):
            r   = self._row_rect(i)
            col = UI_HIGHLIGHT if i == self.hovered else UI_BG
            # Dim Back/Wait slightly
            text_col = UI_TEXT_DIM if opt in ("Back", "Wait") else UI_TEXT
            pygame.draw.rect(surface, col, r, border_radius=3)
            txt = C.FONT_MD.render(opt, True, text_col)
            surface.blit(txt, txt.get_rect(centery=r.centery, x=r.x + 10))

    def _row_rect(self, i):
        return pygame.Rect(
            self.rect.x + PADDING // 2,
            self.rect.y + PADDING // 2 + i * ITEM_H,
            MENU_W - PADDING,
            ITEM_H - 2,
        )


class ItemMenu:
    """Sub-menu listing usable consumables."""

    def __init__(self, unit, x, y):
        self.unit    = unit
        self.items   = unit.usable_items()
        self.hovered = 0

        from core.constants import SCREEN_W, SCREEN_H
        w  = 210
        h  = len(self.items) * ITEM_H + PADDING + 20
        mx = min(x + 30, SCREEN_W - w - 4)
        my = min(y - ITEM_H, SCREEN_H - h - 40)
        self.rect = pygame.Rect(mx, my, w, h)

    def handle_event(self, event):
        if event.type == pygame.MOUSEMOTION:
            for i in range(len(self.items)):
                if self._row_rect(i).collidepoint(event.pos):
                    self.hovered = i

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, it in enumerate(self.items):
                if self._row_rect(i).collidepoint(event.pos):
                    return it
            return "back"

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.hovered = (self.hovered - 1) % len(self.items)
            if event.key in (pygame.K_DOWN, pygame.K_s):
                self.hovered = (self.hovered + 1) % len(self.items)
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                return self.items[self.hovered]
            if event.key == pygame.K_ESCAPE:
                return "back"

        return None

    def draw(self, surface):
        pygame.draw.rect(surface, UI_BG, self.rect, border_radius=5)
        pygame.draw.rect(surface, UI_BORDER, self.rect, 1, border_radius=5)
        hdr = C.FONT_SM.render("Use Item:", True, UI_TEXT_DIM)
        surface.blit(hdr, (self.rect.x + 8, self.rect.y + 4))
        for i, it in enumerate(self.items):
            r     = self._row_rect(i)
            col   = UI_HIGHLIGHT if i == self.hovered else UI_BG
            pygame.draw.rect(surface, col, r, border_radius=3)
            label = f"{it.name}  ({it.uses}x)"
            txt   = C.FONT_MD.render(label, True, UI_TEXT)
            surface.blit(txt, txt.get_rect(centery=r.centery, x=r.x + 8))

    def _row_rect(self, i):
        return pygame.Rect(
            self.rect.x + 4,
            self.rect.y + 22 + i * ITEM_H,
            self.rect.w - 8,
            ITEM_H - 2,
        )
