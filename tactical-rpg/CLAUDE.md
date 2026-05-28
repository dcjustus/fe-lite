# CLAUDE.md — Tactical RPG Developer Notes

Complete record of design decisions, architecture, and implementation history.

---

## Project Overview

A browser-compatible Tactical RPG tech demo written in **Python 3.14 + pygame-ce 2.5.7**.  
Target: Fire Emblem-style turn-based combat, but using **free 2D movement** (range circles)  
instead of a tile grid. Packaged for the browser via **Pygbag** (Python → WebAssembly).

```
python main.py              # run locally
python -m pygbag --build .  # build for browser
```

---

## File Structure

```
tactical-rpg/
├── main.py                      # async entry point (Pygbag-compatible)
├── requirements.txt             # pygame-ce, pygbag
├── core/
│   ├── constants.py             # all tuneable values, font loading
│   └── game.py                  # state machine, input routing, render orchestration
├── entities/
│   ├── names.py                 # random name pools + reset between battles
│   ├── unit.py                  # Unit class — stats, drawing, flash timer
│   └── unit_classes.py          # base stat definitions for each class
├── systems/
│   ├── items.py                 # Item class, weapon constants, GroundItem
│   ├── combat.py                # damage formula, accuracy, double-attack
│   ├── movement.py              # radius clamping + point-in-circle helpers
│   ├── ai.py                    # greedy enemy AI, returns (log, attacked_target)
│   ├── effects.py               # visual-only combat animations
│   ├── sound.py                 # sound effect loader + player (pygame.mixer)
│   └── sprites.py               # PNG idle-sprite loader, tinting, 3-frame animation cache
├── assets/
│   ├── sprites/                 # 31×31 PNG idle frames — [class]_idle1/2/3.png (5 classes × 3 = 15 files)
│   └── sounds/                  # MP3 audio files (replace placeholders with real files)
│       ├── menu_music.mp3       # title screen background music (loops)
│       ├── battle_music.mp3     # in-battle background music (loops)
│       ├── victory.mp3          # victory screen jingle (plays once)
│       ├── defeat.mp3           # defeat screen jingle (plays once)
│       ├── slash.mp3            # sword attack SFX
│       ├── swing.mp3            # axe attack SFX
│       ├── strike.mp3           # lance attack SFX
│       ├── arrow.mp3            # bow attack SFX
│       ├── magic.mp3            # magic attack SFX
│       ├── movement.mp3         # unit movement SFX (looped, stopped on arrival)
│       └── death.mp3            # unit death SFX
├── battlefield/
│   └── battlefield.py           # unit placement, terrain, TreasureChest
└── ui/
    ├── hud.py                   # top phase banner + bottom log strip
    ├── panel.py                 # right-side unit stat panel
    └── action_menu.py           # post-move action menu + item sub-menu
```

---

## Architecture

### Game state machine (`core/game.py`)

```
"title"  →  "battle"  →  "victory"
                      →  "defeat"
```

Inside "battle", player turns use a **sub-state machine**:

```
S_SELECT → S_MOVE → S_MOVING → S_ACTION → S_ATTACK
                    (anim)               → S_ITEM_MENU
                                         → (Back → S_MOVE)
                                         → (Wait/Open Chest → S_SELECT)
```

`S_MOVING` is a transient state where the unit is animating to its destination.  
All player input is blocked during this state. The transition to `S_ACTION` fires  
automatically once `unit.is_moving` becomes False.

### Turn flow

1. **Player Phase** — player activates each ally: select → move (with animation) → act.  
   All allies exhausted → Enemy Phase begins.
2. **Enemy Phase** — two-phase per enemy, driven by `_ai_delay` (0.5 s) and animation:
   - **Phase 1** (timer fires): `ai_move` runs — heals or repositions the unit. If an attack  
     target was found, `_ai_pending_attack` stores `(enemy, target)` and the timer pauses.
   - **Phase 2** (each frame): waits for `enemy.is_moving` to become False, then resolves  
     combat, spawns effects, and drops items. The 0.5 s delay then begins before the next enemy.  
   When the queue is empty a new Player Phase begins and `turn_num` increments.

### Undo move

`_pre_move_pos` stores `(unit.x, unit.y)` before movement. Choosing **Back** in the action  
menu calls `unit.teleport_to(*_pre_move_pos)` — an instant snap-back with no reverse  
animation — then returns to `S_MOVE`. Pre-move position is cleared on any committed action.

---

## Rendering Pipeline (per frame)

```
fill background
→ terrain decorations (trees, rocks)
→ treasure chests
→ ground items (dropped loot)
→ movement range overlay  (S_MOVE only)
→ attack range overlay    (whenever any unit is selected or inspected)
→ all alive units (with HP bars, badges, selection/inspect rings, hit-flash overlay)
→ visual combat effects (SlashEffect, ArrowEffect, MagicEffect, ImpactFlash)
→ right-side stat panel  (selected ally, or inspected enemy if nothing selected)
→ HUD (top banner + bottom log + hint line)
→ action menus (if open)
```

---

## Key Constants (`core/constants.py`)

| Constant | Value | Purpose |
|---|---|---|
| `SCREEN_W / SCREEN_H` | 1280 × 720 | Window size |
| `FPS` | 60 | Target frame rate |
| `MOV_SCALE` | 50 | px per 1 point of MOV stat |
| `BASE_HIT_RATE` | 90 | Base accuracy % |
| `WEAPON_TRIANGLE_BONUS` | 3 | Damage ±bonus for triangle advantage |
| `WEAPON_TRIANGLE_HIT_MOD` | 10 | Accuracy ±% for triangle advantage |
| `DOUBLE_ATTACK_THRESHOLD` | 1.4 | attacker.SPD ≥ defender.SPD × this → double hit |
| `BASE_CRIT_CHANCE` | 10 | Base crit % for all classes except Mage (Mage = 0) |
| `CRIT_TRIANGLE_MOD` | 5 | Crit% ±modifier for weapon triangle advantage/disadvantage |
| `UNIT_RADIUS` | 20 | Base sprite radius in pixels |
| `UNIT_ANIM_SPEED` | 500.0 | px/s movement glide speed |
| `HIT_FLASH_DURATION` | 0.28 | Seconds the red hit flash is visible |
| `AI_HEAL_THRESHOLD` | 0.30 | Enemy heals when HP/max\_HP falls below this |
| `AI_ATTACK_MARGIN` | 5 | px inside weapon range the AI targets when repositioning |
| `ITEM_DROP_CHANCE` | 0.30 | Probability each dropped item goes directly to the killer |

### Font system

All UI text uses `pygame.freetype` via `_FTFont`, a thin wrapper that matches the  
`pygame.font.Font.render(text, antialias, color)` interface. Freetype renders against  
a **transparent background** (not baked black), eliminating the dark-halo blurriness  
that `pygame.font.SysFont` produces at small sizes.

```python
FONT_SM = _make_ft(13)             # small UI text
FONT_MD = _make_ft(16)             # menus, labels
FONT_LG = _make_ft(22, bold=True)  # phase banner
FONT_XL = _make_ft(52, bold=True)  # title / victory text
```

Font preference order: `calibri → segoeui → tahoma → arial → built-in fallback`.

**Exception — unit weapon badges:** The single letter drawn inside each unit shape  
(`S`, `A`, `L`, `B`, `M`) uses `pygame.font.SysFont` instead of freetype:

```python
FONT_UNIT_BADGE = pygame.font.SysFont("calibri", 13, bold=True)
```

The surface is rendered with `antialias=False` and `set_colorkey((0,0,0))` so the  
black background is made transparent, giving a crisp pixel-sharp badge with no halo.

---

## Unit System (`entities/unit.py`, `entities/unit_classes.py`)

### Stats

| Stat | Attribute | Notes |
|---|---|---|
| HP | `max_hp` / `hp` | Varies ±15% on spawn |
| Strength | `strength` | Physical attack (Sword/Axe/Lance/Bow) |
| Defense | `defense` | Reduces physical damage |
| Intelligence | `intelligence` | Magic attack |
| Resistance | `resistance` | Reduces magic damage |
| Speed | `speed` | ≥ enemy.speed × 1.4 → double hit |
| Movement | `movement` | × MOV_SCALE = pixel movement radius |

All stats except `movement` have ±15% random variance on spawn.

### Base stats by class (before variance)

| Class | HP | STR | DEF | INT | RES | SPD | MOV |
|---|---|---|---|---|---|---|---|
| Fighter | 32 | 17 | 7 | 5 | 10 | 7 | 5 |
| Warrior | 40 | 20 | 10 | 2 | 3 | 5 | 4 |
| Knight | 26 | 19 | 9 | 3 | 9 | 4 | 4 |
| Archer | 28 | 17 | 5 | 5 | 6 | 9 | 5 |
| Mage | 20 | 4 | 3 | 20 | 8 | 10 | 5 |

**Balance target:** ~8–12 neutral damage per hit, ~3–4 hits to kill.  
- Knight STR raised 16→19 (disadvantaged matchups now deal ~6 dmg instead of 1); MOV raised 3→4.  
- Fighter RES raised 5→10 so Mage deals ~10 dmg vs Fighters (4-hit kill) but still ~17 vs Warriors (3-hit kill).  
- Knight DEF kept at 9 after playtesting showed DEF 18 made Knight vs Knight nearly impossible.

### Movement animation

Each unit holds two positions:

| Attribute | Role |
|---|---|
| `x`, `y` | Logical position — used by all game logic (range checks, AI, combat) |
| `_draw_x`, `_draw_y` | Visual position — what is actually rendered each frame |

When `x`/`y` change (move command or AI reposition), `_draw_x`/`_draw_y` trail  
behind and step toward the logical position at `_anim_speed` **500 px/s** per frame  
via `unit.update_anim(dt)`. The `is_moving` property returns True while the gap  
exceeds 0.5 px.

`unit.teleport_to(x, y)` sets all four values simultaneously — used by undo (Back)  
to snap the unit back with no reverse animation.

### Hit flash

`unit.flash_timer` is set to 0.28 s on any `take_damage()` call. `draw()` overlays a  
semi-transparent red circle while `flash_timer > 0`. The game's `update()` loop decays it each frame.

### Sprite rendering

Units are drawn using 31×31 PNG idle frames loaded from `assets/sprites/`.  
Each class has three frames (`[class]_idle1/2/3.png`) that cycle at **0.25 s per frame**  
(full cycle ≈ 0.75 s) via `_idle_timer` / `_idle_frame` advanced in `update_anim()`.

`systems/sprites.init_sprites()` is called once in `main.py` after `display.set_mode()`.  
It scales each 31×31 frame to **64×64** and pre-bakes four tinted variants per frame:

| Key | Appearance |
|---|---|
| `ally` | Original PNG colours (blue palette) |
| `enemy` | Greyscale + red-orange multiply |
| `ally_ex` | Greyscale + muted blue-grey multiply |
| `enemy_ex` | Greyscale + muted red-grey multiply |

`unit.draw()` calls `get_sprite(class_name, team, exhausted, frame_index)` and blits the  
result centred on the unit's draw position. If sprites fail to load the old primitive  
shapes (circles, rectangles, diamond) are used as a fallback.

---

## Weapon & Combat System

### Weapon ranges (pixels)

| Weapon | Min | Max | Notes |
|---|---|---|---|
| Sword | 0 | 65 | Melee |
| Axe | 0 | 70 | Melee |
| Lance | 0 | 75 | Melee |
| Bow | 80 | 160 | **Dead zone** within 80 px |
| Magic | 0 | 150 | Full range |

The Bow dead zone is drawn as a dark inner ring inside the red attack-range overlay.

### Weapon triangle

```
Sword beats Axe  →  Axe beats Lance  →  Lance beats Sword
```

- Advantage: **+3 ATK**, **+10% hit rate**
- Disadvantage: **−3 ATK**, **−10% hit rate**
- Bow and Magic are **neutral** (no triangle interaction, no bonus or penalty)

### Damage formula

```python
# Physical (Sword, Axe, Lance, Bow)
dmg = max(1, attacker.strength + triangle_bonus - defender.defense)

# Magic (ignores triangle entirely)
dmg = max(1, attacker.intelligence - defender.resistance)
```

### Combat sequence

1. Accuracy roll: `random(1–100) > hit_chance` → MISS, no damage.
2. **Critical hit roll**: on a hit, `random(1–100) <= crit_chance` → deal 2× damage. Logged as `[CRITICAL]`.
3. Defender **counter-attacks** if attacker is within defender's attack range.
4. If `attacker.speed >= defender.speed * 1.4` → **follow-up strike** (checked after counter).

### Critical hit chance

- **Mage**: 0% — magic damage is already high enough.
- **All other classes**: 10% base (`BASE_CRIT_CHANCE`), modified by the weapon triangle:
  - Advantage: +5% (`CRIT_TRIANGLE_MOD`)
  - Disadvantage: −5%
  - Bow and Magic are neutral (no triangle crit modifier).

---

## Item System (`systems/items.py`)

### Item class

```python
Item(name, heal_pct=0, buff_stat=None, buff_amount=0, uses=N)
```

`buff_stat` is a string attribute name on Unit (`"strength"`, `"defense"`, `"intelligence"`, `"resistance"`).  
Buffs are applied directly to the stat for the rest of the battle (no expiry).

### Starting inventory pool (0–2 items per unit)

| Item | Effect |
|---|---|
| Heal Potion | Restore 25% max HP, 1 use |
| Elixir | Restore 50% max HP, 1 use |
| Vulnerary | Restore 15% max HP, 2 uses |

### Chest pool (1 item per chest)

| Item | Effect |
|---|---|
| Str / Def / Int / Res Tonic | +4 to stat, permanent |
| Mega Potion | Restore 40% max HP |
| Elixir | Restore 50% max HP |

### Ground items (`GroundItem`)

When a unit dies, each item it carried has a **30% chance to go directly to the killer's inventory**;  
otherwise it falls to the ground. Ground items are stored in `game.ground_items` as `GroundItem(x, y, item)`.  
Any unit that ends a move within 48 px of a ground item **auto-picks it up**.  
Drawn as small golden diamond shapes on the battlefield.

---

## Treasure Chests (`battlefield/battlefield.py`)

`TreasureChest` objects are placed in the centre third of the map (1–3 per battle).  
Interaction radius: **60 px**. When a unit moves within range, **"Open Chest"** appears  
in the action menu. Opening the chest adds its item directly to the unit's inventory  
and exhausts the unit. Opened chests display as grey/flat instead of golden.

---

## Enemy AI (`systems/ai.py`)

Greedy algorithm split into two phases so movement animation plays before combat resolves.

### Phase 1 — `ai_move(enemy, allies)` (called when timer fires)

1. If HP < 30% and usable item available → **use item**, exhaust, return `(log, None)`.
2. Find nearest alive ally by Euclidean distance.
3. If not already in attack range → **set logical position** toward ideal spot:
   - Bow: stand just outside its own dead zone (lo + 5 px) from target.
   - Others: stand at hi − 5 px from target.
   - `_draw_x/_draw_y` stay at old position; animation begins automatically.
4. If now in attack range → return `(log, target)` — **combat NOT yet resolved**.
5. If out of range after moving → exhaust, return `(log, None)`.

### Phase 2 — `_update_ai` in `game.py` (each frame while `_ai_pending_attack` is set)

- Waits for `enemy.is_moving` to become False (animation complete).
- Calls `resolve_combat`, spawns visual effects, handles kills and item drops.
- Exhausts the enemy; the 0.5 s inter-enemy delay then begins.

For enemies already in attack range (no movement), combat fires immediately without  
waiting for an animation.

---

## Visual Effects (`systems/effects.py`)

All effects are **cosmetic only** — combat is already resolved before they play.  
They run concurrently with gameplay (non-blocking).

| Effect | Trigger | Visual |
|---|---|---|
| `SlashEffect` | Melee (Sword/Axe/Lance) | 3 expanding yellow slash lines at impact |
| `ArrowEffect` | Bow | Brown arrow head + shaft traveling to target |
| `MagicEffect` | Magic | Purple orb travels (first 45% of duration), then bursts into ring + particles |
| `ImpactFlash` | All attacks | White burst at defender's position (can have a delay offset) |

Effects tick in `game.update()` and are discarded when `effect.done == True`.

---

## Sound & Music (`systems/sound.py`)

`systems/sound.py` wraps both `pygame.mixer.Sound` (pre-loaded SFX, low latency) and `pygame.mixer.music` (streamed music, one track at a time). Initialised once in `main.py` via `sound.init()` after `pygame.init()`.

### Call sites

| Site | What it calls |
|---|---|
| `systems/effects.py` → `create_combat_effects()` | `sound.play_for_weapon(weapon)` — fires when combat resolves and visuals begin |
| `systems/effects.py` → `create_combat_effects()` | `sound.play_grunt()` — randomly plays grunt_1 or grunt_2 alongside the weapon SFX (attacker only) |
| `core/game.py` → `_process_action_choice()` | `sound.play('ui_button')` — plays on any committed menu selection (Attack, Item, Wait, etc.) |
| `core/game.py` → `_process_item_choice()` | `sound.play('ui_button')` — plays when an item or Back is chosen in the item sub-menu |
| `core/game.py` → `handle_event()` title/victory/defeat | `sound.play('ui_button')` — plays on any key/click to advance the screen |
| `core/game.py` → `_try_move()` | `sound.play_movement()` — starts movement loop |
| `core/game.py` → `update()` (S_MOVING → S_ACTION) | `sound.stop_movement()` — stops loop on arrival |
| `core/game.py` → `_begin_player_phase()` | `sound.stop_movement()` — safety stop covering the last-enemy edge case |
| `core/game.py` → `_update_ai()` Phase 2 | `sound.stop_movement()` — stops loop when enemy arrives before attacking |
| `core/game.py` → all combat resolution paths | `sound.play('death')` — fires if ≥1 unit dies in the exchange |
| `core/game.py` → `_reset()` | `sound.stop_movement(); sound.play_music('menu_music')` |
| `core/game.py` → `handle_event()` title→battle | `sound.play_music('battle_music')` |
| `core/game.py` → `_check_win_loss()` | `sound.stop_music(); sound.play_music('victory'/'defeat', loops=0)` |

### API

```python
sound.init()                    # call once at startup; safe if mixer unavailable
sound.play('death')             # play SFX by key; no-op if absent or mixer failed
sound.play_for_weapon(weapon)   # maps weapon constant → SFX key, used by effects.py
sound.play_grunt()              # play grunt_1 or grunt_2 at random (attacker hit reaction)
sound.play_movement()           # starts movement SFX looping (loops=-1)
sound.stop_movement()           # stops the movement loop channel
sound.play_music('battle_music')        # load + play music track (loops=-1 default)
sound.play_music('victory', loops=0)    # play once
sound.stop_music()              # stop current music track
```

### SFX files (pre-loaded via `pygame.mixer.Sound`)

| Key | File | Trigger |
|---|---|---|
| `slash` | `slash.mp3` | Sword attacks |
| `swing` | `swing.mp3` | Axe attacks |
| `strike` | `strike.mp3` | Lance attacks |
| `arrow` | `arrow.mp3` | Bow attacks |
| `magic` | `magic.mp3` | Magic attacks |
| `movement` | `movement.mp3` | Unit movement (looped, stopped on arrival) |
| `death` | `death.mp3` | Any unit killed in a combat exchange |
| `grunt_1` | `grunt 1.mp3` | Attacker grunt on combat (randomly chosen with grunt_2) |
| `grunt_2` | `grunt 2.mp3` | Attacker grunt on combat (randomly chosen with grunt_1) |
| `ui_button` | `ui button.mp3` | Menu selection (action menu, item menu, screen transitions) |

### Music files (streamed via `pygame.mixer.music`)

| Name | File | Loops |
|---|---|---|
| `menu_music` | `menu_music.mp3` | Infinite |
| `battle_music` | `battle_music.mp3` | Infinite |
| `victory` | `victory.mp3` | Once |
| `defeat` | `defeat.mp3` | Once |

### Graceful degradation

`init()` wraps `pygame.mixer.init()` in a try/except. If the mixer fails (no audio device, browser sandbox), `_ready` stays `False` and every subsequent call is a no-op. SFX files that are missing or unreadable are skipped silently at load time. Music files are checked with `os.path.isfile` before each load; missing files are silently ignored. All placeholder text files in the repo trigger these silent-skip paths until replaced with real MP3s.

---

## Battlefield Generation (`battlefield/battlefield.py`)

- **Allies** spawn in the left third of the screen; **enemies** in the right third.
- Unit count: `random.randint(3, 5)` — same value used for both sides (balanced).
- Minimum 65 px gap between spawn positions (up to 500 placement attempts).
- **Terrain** (trees, rocks): 4–9 decorative pieces in the centre zone. Cosmetic only — no collision.
- **Chests**: 1–3 placed in the centre zone with minimum 80 px spacing.

---

## HUD & UI (`ui/`)

### Layout (1280 × 720)

```
y=0–34      Top banner: phase label, turn counter, unit counts
y=34–610    Gameplay area
y=610–720   Bottom log strip (LOG_H = 120):
              line 0: action hint (dimmed)
              lines 1–5: last 5 combat log entries
x=1032–1272 Right panel (PANEL_W = 240, PANEL_H = 330):
              unit name, class, weapon range description,
              HP bar, stat block (physical/magical columns),
              inventory (max 4 shown + "+N more")
```

The panel shows `game.selected` (the ally being controlled) when one is active,  
otherwise falls back to `game.inspected` (an enemy being viewed). `panel.py` already  
handles enemy units correctly — name is tinted red, all stats are displayed.

### Enemy inspection

During S_SELECT, left-clicking an alive enemy sets `game.inspected` (no sub-state  
change). Effects:
- A **gold ring** is drawn around the inspected unit (handled in `unit.draw(inspected=True)`).
- The enemy's **attack range overlay** is rendered so the player can see their reach.
- The **right panel** shows the enemy's full stat block.
- Clicking an ally clears `inspected` and begins the normal turn flow.
- Clicking empty space clears `inspected` with no other effect.

### Hint line

The action hint (e.g. "Click an ally to select") lives inside the log box, not floating  
over the gameplay area. It is passed as `hint=` to `HUD.draw()` from `game.draw()`.

### Action menu options

```
Attack
Item        (only shown if unit has usable items)
Open Chest  (only shown if an unopened chest is within 60 px)
Back        (always present — undoes the current move)
Wait        (always present)
```

---

## Name System (`entities/names.py`)

Two separate pools:
- **Allies** (`ALLY_NAMES`): heroic fantasy names (Arden, Lyra, Cael, …)
- **Enemies** (`ENEMY_NAMES`): darker names (Morg, Drak, Skorn, …)

`_used: set` tracks names assigned in the current battle. `reset()` clears it.  
`get_name(team)` picks a random unused name; falls back to the full pool if exhausted.  
`reset()` is called in `Game._reset()` at the start of every new battle.

---

## Pygbag Compatibility (`main.py`)

```python
async def main():
    ...
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get(): ...
        game.update(dt)
        game.draw()
        pygame.display.flip()
        await asyncio.sleep(0)   # yield to browser event loop

asyncio.run(main())
```

The `await asyncio.sleep(0)` is required for Pygbag to process browser events.  
No platform-specific code exists; the game runs identically locally and in the browser.

---

## Known Limitations / Future Work

- Sprite assets are static idle frames only — no walk or attack animation on the map yet.
- Terrain is purely decorative — no collision, line-of-sight, or terrain bonuses.
- Enemy AI is fully greedy with no look-ahead. A priority-scoring system or simple A\*  
  for pathfinding would improve it.
- No save system; each session is independent.
- Item inventory has no size cap; units can accumulate unlimited items from pickups.
- The weapon triangle hit modifier and damage bonus are separate constants  
  (`WEAPON_TRIANGLE_HIT_MOD`, `WEAPON_TRIANGLE_BONUS`) in `core/constants.py`  
  and can be tuned independently without touching game logic.
- All audio files in `assets/sounds/` are plain-text placeholders; both
  `pygame.mixer.Sound` and `pygame.mixer.music` silently skip them. Replace
  with real MP3s — no code changes needed.

---

## Development History (chronological)

1. Initial scaffold: folder structure, constants, blank stubs.
2. Unit class + primitive rendering, HP bars, selection ring.
3. Movement system: range-circle display, click-to-move, clamping.
4. Post-move action menu (Attack / Item / Wait).
5. Combat system: damage formula, weapon triangle, counter-attack.
6. Item system: inventory panel, consumable use.
7. Enemy AI: greedy move + attack with delay.
8. Battlefield generator: random unit placement, decorative terrain.
9. Game states: Title, Victory, Defeat screens; state machine wiring.
10. **Magic class** added (INT vs RES, full range, neutral triangle).
11. **Bow dead zone** added (annular attack ring, can't attack close-range).
12. **Full stat system** (STR/DEF/INT/RES/SPD/MOV) replacing flat ATK/DEF.
13. **Accuracy system** (90% base, ±10% triangle modifier, MISS log entries).
14. **Item/loot overhaul**: stat-buffing Tonics, treasure chests, item drops on kill, ground pickup.
15. **Movement range increased** (MOV_SCALE 50, up from implied ~25).
16. **Undo move** ("Back" in action menu, restores pre-move position).
17. **Random unit names** (separate ally/enemy pools, reset per battle).
18. **Visual combat effects** (SlashEffect, ArrowEffect, MagicEffect, ImpactFlash).
19. **Antialiased unit shapes** (pygame.draw.aacircle, aalines).
20. **Hit flash** on units when taking damage (flash_timer decay in update loop).
21. **Freetype fonts** (_FTFont wrapper) for sharper text at small sizes.
22. **UI layout fixes**: hint line moved into log box, font sizes tightened.
23. **Balance pass**: Knight DEF 18→9, all STR/INT raised ~25–30%.
24. **Bug fixes**: AI effect detection (flash_timer → return value), side-effect list  
    comprehensions replaced with explicit loops, dead code removed from panel.py.
25. **Movement animation**: units glide at 500 px/s via `_draw_x/_draw_y` trailing  
    `x/y`; S_MOVING sub-state blocks input until animation completes; undo snaps  
    back instantly via `teleport_to()`.
26. **SysFont unit badges**: weapon letter inside each unit shape switched from  
    freetype to `pygame.font.SysFont` + `set_colorkey` for cleaner rendering.
27. **Attack range always visible**: red range overlay shown whenever a unit is  
    selected (not just during S_ATTACK), and for inspected enemies in S_SELECT.
28. **Enemy inspection**: clicking a red unit in S_SELECT shows their stats and  
    attack range in view-only mode (gold ring, no control).
29. **Two-phase AI**: `ai_act` replaced with `ai_move`; combat deferred until  
    movement animation finishes via `_ai_pending_attack` in game.py.
30. **Bug fix**: allies killed by counter-attack during player turn now correctly  
    drop items immediately (previously items were lost until the enemy phase ran).
31. **Sound & music system**: `systems/sound.py` wraps `pygame.mixer.Sound` for SFX
    (slash, swing, strike, arrow, magic, movement, death) and `pygame.mixer.music`
    for four streamed tracks (menu_music, battle_music, victory, defeat). Movement
    sound loops while animating and stops on arrival; death SFX fires on any kill;
    music transitions on state changes (title↔battle, battle→victory/defeat).
    Bug fix included: `_begin_player_phase()` always calls `stop_movement()` so the
    final enemy's movement sound cannot loop past the end of the enemy phase.
32. **PNG sprite system**: replaced GIF sprite sheets with 31×31 PNG idle frames
    (`[class]_idle1/2/3.png`). `systems/sprites.py` loads, scales to 64×64, and
    pre-bakes ally/enemy/exhausted tinted variants. Units cycle the 3 frames at
    0.25 s each via `_idle_timer`/`_idle_frame` in `update_anim()`. Weapon letter
    badges removed. Primitive shapes remain as fallback.
35. **Grunt and UI button SFX**: `play_grunt()` added to `systems/sound.py` — randomly
    plays `grunt 1.mp3` or `grunt 2.mp3` alongside the weapon SFX in
    `create_combat_effects()` (attacker only, defender is silent). `ui button.mp3` plays
    via `sound.play('ui_button')` on every committed menu selection in
    `_process_action_choice` / `_process_item_choice`, and on title/victory/defeat
    screen transitions in `handle_event()`.
36. **Critical hit system**: on any successful hit, non-Mage units have a 10% base crit
    chance that deals 2× damage. The weapon triangle applies a ±5% modifier (advantage
    +5%, disadvantage −5%). Mages have 0% crit. Crits are logged as `[CRITICAL]`.
    Constants `BASE_CRIT_CHANCE` and `CRIT_TRIANGLE_MOD` in `core/constants.py`;
    `weapon_triangle_crit_mod()` in `systems/items.py`; applied in `systems/combat.py`.
35. **Item-menu bug fixes**: (a) `if` → `elif` in `_handle_player_input` keyboard
    block — the same keypress was processed by both action menu and the freshly-opened
    item menu, silently consuming an item; (b) `_process_item_choice(None)` now
    returns early instead of destroying `item_menu`, preventing a soft-lock when any
    unhandled key was pressed while the item menu was open.
