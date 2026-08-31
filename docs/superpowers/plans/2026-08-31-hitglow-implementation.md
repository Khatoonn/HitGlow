# HitGlow Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build HitGlow, a Windows overlay that shows a leverless controller's inputs (directions + 6 action buttons) as glowing circles, with true per-pixel window transparency, a calibration mode, and a complete, publishable GitHub repo.

**Architecture:** A small `hitglow` package under `src/`. Pure, testable logic (input-to-boolean mapping, color fade math, frame rendering onto an off-screen `pygame.Surface`, calibration text formatting) is isolated from the two pieces that need real hardware/OS resources and can only be verified manually: joystick polling (`pygame.joystick`) and the Win32 layered-window plumbing (`ctypes`). `main.py` wires everything together in a single event loop.

**Tech Stack:** Python 3.11+, pygame (joystick input, Surface rendering, fonts), `ctypes` (stdlib) for `WS_EX_LAYERED` / `UpdateLayeredWindow`, pytest for the pure-logic test suite (dev-only dependency), PyInstaller for packaging.

**Spec:** [docs/superpowers/specs/2026-08-31-hitglow-design.md](../specs/2026-08-31-hitglow-design.md)

## Global Constraints

- Runtime dependency footprint: `pygame` only. No `numpy`, no `pywin32` — keep PyInstaller packaging simple (per spec "Stack").
- All colors drawn onto the overlay surface must use alpha 0 or 255 only — never a fractional alpha — because the layered-window path skips premultiplication as a deliberate perf/simplicity trade-off (see Task 4). The button "fade" is implemented as an RGB color interpolation toward `COLOR_OFF`, never as an alpha fade.
- No index in `config.py` is ever hard-coded to a guessed value — every mapping default is `None` until the user calibrates (per spec "Lecture manette").
- `TRANSPARENT_BACKGROUND` in `config.py` must always have a working, fully-functional fallback path (solid chroma-key fill) — the layered-window path is unverifiable by automated tests, so the fallback is the safety net (per spec "Transparence de fenêtre").
- No automated tests for GUI/hardware code (window creation, win32 calls, live joystick polling) — per spec "Tests", these are verified manually. Pure logic (mapping resolution, color math, frame rendering onto an in-memory Surface, calibration text formatting) IS unit tested.
- Git: local `git init` + commits happen throughout; the push to `https://github.com/Khatoonn/HitGlow` only happens in the final task, after the repo is complete.

---

## Task 1: Project scaffolding

**Files:**
- Create: `E:\HitGlow\src\hitglow\__init__.py`
- Create: `E:\HitGlow\pyproject.toml`
- Create: `E:\HitGlow\requirements.txt`
- Create: `E:\HitGlow\requirements-dev.txt`
- Create: `E:\HitGlow\.gitignore`
- Create: `E:\HitGlow\LICENSE`
- Create: `E:\HitGlow\tests\__init__.py`
- Create: `E:\HitGlow\tests\conftest.py`
- Test: `E:\HitGlow\tests\test_package.py`

**Interfaces:**
- Produces: `hitglow.__version__` (str) — consumed by nothing yet, just a package smoke test.
- Produces: `tests/conftest.py` sets `SDL_VIDEODRIVER=dummy` before pygame is imported anywhere in the test suite — every later test task relies on this for headless pygame.

- [ ] **Step 1: Create the package skeleton**

`src/hitglow/__init__.py`:
```python
"""HitGlow — overlay d'inputs manette leverless pour stream Tekken 8."""

__version__ = "0.1.0"
```

- [ ] **Step 2: Configure pytest to find the `src` layout**

`pyproject.toml`:
```toml
[project]
name = "hitglow"
version = "0.1.0"
description = "Overlay d'inputs manette leverless pour stream Tekken 8"
requires-python = ">=3.11"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
```

- [ ] **Step 3: Pin runtime and dev dependencies**

`requirements.txt`:
```
pygame>=2.5
```

`requirements-dev.txt`:
```
-r requirements.txt
pytest>=8.0
```

- [ ] **Step 4: Add .gitignore**

`.gitignore`:
```
__pycache__/
*.pyc
.venv/
venv/
build/
dist/
*.spec
.pytest_cache/
*.egg-info/
```

- [ ] **Step 5: Add MIT LICENSE**

`LICENSE`:
```
MIT License

Copyright (c) 2026 Khatoonn

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
```

- [ ] **Step 6: Add the headless-pygame test fixture**

`tests/__init__.py`: empty file.

`tests/conftest.py`:
```python
import os

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")
```

- [ ] **Step 7: Write the package smoke test**

`tests/test_package.py`:
```python
import hitglow


def test_version_is_a_string():
    assert isinstance(hitglow.__version__, str)
    assert hitglow.__version__
```

- [ ] **Step 8: Install dev dependencies and run the test**

Run:
```bash
cd E:\HitGlow
python -m venv .venv
.venv\Scripts\pip install -r requirements-dev.txt
.venv\Scripts\pytest -v
```
Expected: `test_version_is_a_string` PASSES (1 passed).

- [ ] **Step 9: git init and first commit**

```bash
cd E:\HitGlow
git init
git add .gitignore LICENSE pyproject.toml requirements.txt requirements-dev.txt src tests docs
git commit -m "chore: scaffold HitGlow project"
```

---

## Task 2: Configuration module

**Files:**
- Create: `E:\HitGlow\src\hitglow\config.py`
- Test: `E:\HitGlow\tests\test_config.py`

**Interfaces:**
- Produces: `DIRECTION_SOURCE`, `HAT_INDEX`, `AXIS_MAPPING`, `AXIS_DEADZONE`, `BUTTON_DIRECTION_MAPPING`, `ACTION_BUTTONS` (dict, 6 keys), `WINDOW_WIDTH`, `WINDOW_HEIGHT`, `TRANSPARENT_BACKGROUND`, `CHROMA_FALLBACK_COLOR`, `INITIAL_SCALE`, `SCALE_STEP`, `MIN_SCALE`, `MAX_SCALE`, `COLOR_OFF`, `COLOR_DIRECTION`, `COLOR_ROW_TOP`, `COLOR_ROW_BOTTOM`, `COLOR_LABEL_TEXT`, `FADE_MS`, `CIRCLE_RADIUS`, `DIRECTION_LAYOUT` (dict, 4 keys), `ACTION_LAYOUT` (dict, 6 keys), `ACTION_ROW_TOP`, `ACTION_ROW_BOTTOM`, `QUIT_KEY`, `CALIBRATION_KEY`, `JOYSTICK_INDEX` — consumed by every later task.

- [ ] **Step 1: Write the failing test**

`tests/test_config.py`:
```python
from hitglow import config

DIRECTIONS = {"UP", "DOWN", "LEFT", "RIGHT"}
ACTION_NAMES = {"1", "2", "3", "4", "HEAT", "RAGE"}


def test_direction_sources_default_to_unmapped():
    assert set(config.DIRECTION_SOURCE) == DIRECTIONS
    assert all(v is None for v in config.DIRECTION_SOURCE.values())


def test_action_buttons_have_all_six_names_unmapped():
    assert set(config.ACTION_BUTTONS) == ACTION_NAMES
    assert all(v is None for v in config.ACTION_BUTTONS.values())


def test_action_rows_partition_the_six_names():
    assert config.ACTION_ROW_TOP == {"1", "2", "HEAT"}
    assert config.ACTION_ROW_BOTTOM == {"3", "4", "RAGE"}
    assert config.ACTION_ROW_TOP | config.ACTION_ROW_BOTTOM == ACTION_NAMES
    assert config.ACTION_ROW_TOP & config.ACTION_ROW_BOTTOM == set()


def test_layouts_cover_all_circles():
    assert set(config.DIRECTION_LAYOUT) == DIRECTIONS
    assert set(config.ACTION_LAYOUT) == ACTION_NAMES


def test_colors_are_rgb_tuples():
    for color in (
        config.COLOR_OFF,
        config.COLOR_DIRECTION,
        config.COLOR_ROW_TOP,
        config.COLOR_ROW_BOTTOM,
        config.COLOR_LABEL_TEXT,
        config.CHROMA_FALLBACK_COLOR,
    ):
        assert len(color) == 3
        assert all(0 <= channel <= 255 for channel in color)


def test_fade_and_scale_bounds_are_positive():
    assert config.FADE_MS > 0
    assert config.MIN_SCALE < config.INITIAL_SCALE <= config.MAX_SCALE
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `.venv\Scripts\pytest tests/test_config.py -v`
Expected: FAIL with `ModuleNotFoundError` or `AttributeError` (config.py doesn't exist yet).

- [ ] **Step 3: Write config.py**

`src/hitglow/config.py`:
```python
"""Configuration HitGlow — mapping, couleurs, layout, touches.

Modifie ce fichier a la main pour adapter HitGlow a ta manette et a tes
gouts visuels. Aucun index n'est devine : utilise le mode calibration
(touche C) pour identifier les valeurs de TA manette, puis reporte-les
ici.
"""

import pygame

# ============================================================
# MANETTE
# ============================================================

# Index du joystick a utiliser si plusieurs sont branches (0 = premier
# detecte par pygame).
JOYSTICK_INDEX = 0

# ------------------------------------------------------------
# Directions : chaque direction logique peut venir d'une source
# differente. Valeurs possibles : "hat", "axis", "button", ou None
# (direction desactivee). Utilise le mode calibration pour voir quelle
# source ta manette utilise reellement.
# ------------------------------------------------------------
DIRECTION_SOURCE = {
    "UP": None,
    "DOWN": None,
    "LEFT": None,
    "RIGHT": None,
}

# Index du hat (POV) a lire quand une direction utilise la source "hat".
# La plupart des manettes n'ont qu'un seul hat -> 0.
HAT_INDEX = 0

# Mapping axe pour les directions en mode "axis" :
# (index_axe, signe) ou signe vaut +1 ou -1 et indique quel sens de
# l'axe correspond a cette direction logique.
# Exemple : "LEFT": (0, -1) veut dire "axe 0 negatif = gauche".
AXIS_MAPPING = {
    "UP": None,
    "DOWN": None,
    "LEFT": None,
    "RIGHT": None,
}

# Seuil (valeur absolue, entre 0 et 1) au-dela duquel un axe est
# considere comme "presse" en mode "axis".
AXIS_DEADZONE = 0.5

# Index de bouton pour les directions en mode "button".
BUTTON_DIRECTION_MAPPING = {
    "UP": None,
    "DOWN": None,
    "LEFT": None,
    "RIGHT": None,
}

# ------------------------------------------------------------
# Boutons d'action : nom logique -> index de bouton brut de la manette.
# ------------------------------------------------------------
ACTION_BUTTONS = {
    "1": None,
    "2": None,
    "3": None,
    "4": None,
    "HEAT": None,
    "RAGE": None,
}

# ============================================================
# FENETRE
# ============================================================

WINDOW_WIDTH = 640
WINDOW_HEIGHT = 320

# True = vraie transparence Windows (layered window, alpha par pixel).
# False = fond uni de repli (chroma key classique a retirer dans OBS) —
# a utiliser si ta methode de capture OBS ne restitue pas bien l'alpha
# d'une fenetre layered.
TRANSPARENT_BACKGROUND = True

# Couleur de fond utilisee uniquement quand TRANSPARENT_BACKGROUND = False.
CHROMA_FALLBACK_COLOR = (255, 0, 255)

# Echelle de rendu, modifiable en direct a la molette pendant l'execution.
INITIAL_SCALE = 1.0
SCALE_STEP = 0.05
MIN_SCALE = 0.5
MAX_SCALE = 2.5

# ============================================================
# COULEURS
# ============================================================

COLOR_OFF = (40, 40, 40)
COLOR_DIRECTION = (0, 255, 255)      # cyan
COLOR_ROW_TOP = (255, 220, 0)        # jaune
COLOR_ROW_BOTTOM = (220, 0, 0)       # rouge
COLOR_LABEL_TEXT = (255, 255, 255)

# Duree du fondu (en millisecondes) entre la couleur active et COLOR_OFF
# a l'extinction d'un bouton. C'est un fondu de COULEUR (RGB), pas
# d'alpha : les ronds restent visibles (gris) a l'etat "off".
FADE_MS = 150

# ============================================================
# LAYOUT (positions relatives en pixels, avant application de l'echelle)
# ============================================================

CIRCLE_RADIUS = 28

# Bloc directions : LEFT, DOWN, RIGHT alignes, UP decale en dessous
# (position pouce, comme sur un hitbox physique).
DIRECTION_LAYOUT = {
    "LEFT": (40, 90),
    "DOWN": (110, 100),
    "RIGHT": (175, 130),
    "UP": (140, 210),
}

# Bloc actions : 3 colonnes x 2 rangees en quinconce diagonal, d'apres
# le croquis fourni par l'utilisateur.
ACTION_LAYOUT = {
    "1": (330, 130),
    "3": (320, 195),
    "2": (400, 105),
    "4": (390, 165),
    "HEAT": (470, 110),
    "RAGE": (460, 180),
}

ACTION_ROW_TOP = {"1", "2", "HEAT"}
ACTION_ROW_BOTTOM = {"3", "4", "RAGE"}

# ============================================================
# TOUCHES
# ============================================================

QUIT_KEY = pygame.K_ESCAPE
CALIBRATION_KEY = pygame.K_c
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `.venv\Scripts\pytest tests/test_config.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/hitglow/config.py tests/test_config.py
git commit -m "feat: add HitGlow configuration module"
```

---

## Task 3: Input mapping (pure logic) + joystick polling

**Files:**
- Create: `E:\HitGlow\src\hitglow\input_reader.py`
- Test: `E:\HitGlow\tests\test_input_reader.py`

**Interfaces:**
- Consumes: nothing beyond raw values (no import of `config` inside the pure functions — callers pass config values explicitly, so the functions stay testable without touching `hitglow.config`).
- Produces: `resolve_directions(hat_value, axis_values, button_states, direction_source, axis_mapping, axis_deadzone, button_direction_mapping) -> dict[str, bool]` (keys `UP`/`DOWN`/`LEFT`/`RIGHT`); `resolve_action_buttons(button_states, action_buttons) -> dict[str, bool]`; `JoystickReader` class with `.poll(hat_index) -> tuple[hat, axes, buttons]` — consumed by Task 7 (`main.py`).

- [ ] **Step 1: Write the failing tests**

`tests/test_input_reader.py`:
```python
from hitglow.input_reader import resolve_action_buttons, resolve_directions

NO_SOURCE = {"UP": None, "DOWN": None, "LEFT": None, "RIGHT": None}


def test_hat_source_resolves_all_four_directions():
    source = {**NO_SOURCE, "UP": "hat", "DOWN": "hat", "LEFT": "hat", "RIGHT": "hat"}
    result = resolve_directions(
        hat_value=(-1, 1), axis_values=[], button_states=[],
        direction_source=source, axis_mapping=NO_SOURCE,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
    )
    assert result == {"UP": True, "DOWN": False, "LEFT": True, "RIGHT": False}


def test_axis_source_respects_sign_and_deadzone():
    source = {**NO_SOURCE, "LEFT": "axis", "RIGHT": "axis"}
    mapping = {**NO_SOURCE, "LEFT": (0, -1), "RIGHT": (0, 1)}

    pressed_left = resolve_directions(
        hat_value=(0, 0), axis_values=[-0.9], button_states=[],
        direction_source=source, axis_mapping=mapping,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
    )
    assert pressed_left == {"UP": False, "DOWN": False, "LEFT": True, "RIGHT": False}

    below_deadzone = resolve_directions(
        hat_value=(0, 0), axis_values=[-0.2], button_states=[],
        direction_source=source, axis_mapping=mapping,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
    )
    assert below_deadzone == {"UP": False, "DOWN": False, "LEFT": False, "RIGHT": False}


def test_button_source_reads_button_state():
    source = {**NO_SOURCE, "DOWN": "button"}
    button_mapping = {**NO_SOURCE, "DOWN": 3}
    result = resolve_directions(
        hat_value=(0, 0), axis_values=[], button_states=[False, False, False, True],
        direction_source=source, axis_mapping=NO_SOURCE,
        axis_deadzone=0.5, button_direction_mapping=button_mapping,
    )
    assert result["DOWN"] is True


def test_unmapped_direction_is_never_active():
    result = resolve_directions(
        hat_value=(1, 1), axis_values=[0.9, 0.9], button_states=[True, True],
        direction_source=NO_SOURCE, axis_mapping=NO_SOURCE,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
    )
    assert result == {"UP": False, "DOWN": False, "LEFT": False, "RIGHT": False}


def test_resolve_action_buttons_reads_mapped_indices_only():
    action_buttons = {"1": 0, "2": None, "3": 5}
    result = resolve_action_buttons(
        button_states=[True, False, False, False, False, False], action_buttons=action_buttons,
    )
    assert result == {"1": True, "2": False, "3": False}


def test_resolve_action_buttons_ignores_out_of_range_index():
    action_buttons = {"HEAT": 99}
    result = resolve_action_buttons(button_states=[True, True], action_buttons=action_buttons)
    assert result == {"HEAT": False}
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\pytest tests/test_input_reader.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'hitglow.input_reader'`).

- [ ] **Step 3: Write input_reader.py**

`src/hitglow/input_reader.py`:
```python
"""Lecture des inputs manette : fonctions pures de resolution du mapping,
et polling brut via pygame.joystick."""

import pygame


def resolve_directions(
    hat_value, axis_values, button_states,
    direction_source, axis_mapping, axis_deadzone, button_direction_mapping,
):
    """Calcule l'etat presse/relache des 4 directions logiques a partir
    des valeurs brutes de la manette, selon la source configuree pour
    chaque direction."""
    result = {}
    for name in ("UP", "DOWN", "LEFT", "RIGHT"):
        source = direction_source.get(name)
        if source == "hat":
            x, y = hat_value
            if name == "LEFT":
                result[name] = x < 0
            elif name == "RIGHT":
                result[name] = x > 0
            elif name == "UP":
                result[name] = y > 0
            else:  # DOWN
                result[name] = y < 0
        elif source == "axis":
            mapping = axis_mapping.get(name)
            if mapping is None:
                result[name] = False
            else:
                axis_index, sign = mapping
                value = axis_values[axis_index] if axis_index < len(axis_values) else 0.0
                result[name] = (value * sign) > axis_deadzone
        elif source == "button":
            index = button_direction_mapping.get(name)
            result[name] = bool(button_states[index]) if index is not None and index < len(button_states) else False
        else:
            result[name] = False
    return result


def resolve_action_buttons(button_states, action_buttons):
    """Calcule l'etat presse/relache de chaque bouton d'action nomme."""
    result = {}
    for name, index in action_buttons.items():
        result[name] = bool(button_states[index]) if index is not None and index < len(button_states) else False
    return result


class JoystickReader:
    """Encapsule un pygame.joystick.Joystick et expose son etat brut."""

    def __init__(self, joystick_index):
        pygame.joystick.init()
        if pygame.joystick.get_count() <= joystick_index:
            raise RuntimeError(
                f"Aucune manette detectee a l'index {joystick_index}. "
                "Verifie qu'elle est branchee et reconnue par Windows."
            )
        self.joystick = pygame.joystick.Joystick(joystick_index)
        self.joystick.init()

    def poll(self, hat_index=0):
        """Retourne (hat, axes, buttons) : l'etat brut actuel de la manette."""
        pygame.event.pump()
        hat = self.joystick.get_hat(hat_index) if self.joystick.get_numhats() > hat_index else (0, 0)
        axes = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
        buttons = [bool(self.joystick.get_button(i)) for i in range(self.joystick.get_numbuttons())]
        return hat, axes, buttons
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\pytest tests/test_input_reader.py -v`
Expected: 6 passed.

- [ ] **Step 5: Commit**

```bash
git add src/hitglow/input_reader.py tests/test_input_reader.py
git commit -m "feat: add pure input mapping resolution and joystick polling"
```

---

## Task 4: Color fade and frame rendering (pure/testable rendering logic)

**Files:**
- Create: `E:\HitGlow\src\hitglow\overlay_window.py`
- Test: `E:\HitGlow\tests\test_overlay_render.py`

**Interfaces:**
- Consumes: nothing from earlier tasks directly (works with plain values); will be consumed by `config` values at call sites in Task 7.
- Produces: `lerp_color(color_from, color_to, t) -> tuple[int,int,int]`; `ButtonGlow(off_color, fade_ms)` class with `.update(is_pressed, active_color, now_ms) -> tuple[int,int,int]`; `render_frame(width, height, glow_colors, direction_layout, action_layout, circle_radius, label_color, scale=1.0, calibration_lines=None) -> pygame.Surface` — consumed by Task 6 (calibration overlay) and Task 7 (`main.py`).
- This task also lays the groundwork (constants, imports) for Task 5's win32 window class, which lives in the same file.

- [ ] **Step 1: Write the failing tests**

`tests/test_overlay_render.py`:
```python
import pygame
import pytest

from hitglow.overlay_window import ButtonGlow, lerp_color, render_frame

pygame.font.init()


def test_lerp_color_at_start_and_end():
    assert lerp_color((255, 0, 0), (0, 0, 0), 0.0) == (255, 0, 0)
    assert lerp_color((255, 0, 0), (0, 0, 0), 1.0) == (0, 0, 0)


def test_lerp_color_midpoint():
    assert lerp_color((200, 100, 0), (0, 0, 0), 0.5) == (100, 50, 0)


def test_lerp_color_clamps_t_outside_0_1():
    assert lerp_color((10, 10, 10), (0, 0, 0), -1.0) == (10, 10, 10)
    assert lerp_color((10, 10, 10), (0, 0, 0), 2.0) == (0, 0, 0)


def test_button_glow_is_off_color_when_never_pressed():
    glow = ButtonGlow(off_color=(40, 40, 40), fade_ms=150)
    assert glow.update(is_pressed=False, active_color=(0, 255, 255), now_ms=0) == (40, 40, 40)


def test_button_glow_is_active_color_while_pressed():
    glow = ButtonGlow(off_color=(40, 40, 40), fade_ms=150)
    assert glow.update(is_pressed=True, active_color=(0, 255, 255), now_ms=0) == (0, 255, 255)
    assert glow.update(is_pressed=True, active_color=(0, 255, 255), now_ms=500) == (0, 255, 255)


def test_button_glow_fades_after_release():
    glow = ButtonGlow(off_color=(40, 40, 40), fade_ms=100)
    glow.update(is_pressed=True, active_color=(240, 40, 40), now_ms=0)

    mid_fade = glow.update(is_pressed=False, active_color=(240, 40, 40), now_ms=50)
    assert mid_fade == lerp_color((240, 40, 40), (40, 40, 40), 0.5)

    fully_faded = glow.update(is_pressed=False, active_color=(240, 40, 40), now_ms=200)
    assert fully_faded == (40, 40, 40)


def test_render_frame_paints_pressed_circle_at_its_center():
    glow_colors = {"UP": (40, 40, 40), "DOWN": (40, 40, 40), "LEFT": (0, 255, 255), "RIGHT": (40, 40, 40)}
    surface = render_frame(
        width=200, height=200, glow_colors=glow_colors,
        direction_layout={"UP": (50, 150), "DOWN": (50, 150), "LEFT": (100, 100), "RIGHT": (50, 150)},
        action_layout={}, circle_radius=20, label_color=(255, 255, 255),
    )
    assert surface.get_at((100, 100))[:3] == (0, 255, 255)
    assert surface.get_at((100, 100))[3] == 255


def test_render_frame_leaves_background_fully_transparent():
    surface = render_frame(
        width=50, height=50, glow_colors={}, direction_layout={}, action_layout={},
        circle_radius=10, label_color=(255, 255, 255),
    )
    assert surface.get_at((0, 0))[3] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\pytest tests/test_overlay_render.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'hitglow.overlay_window'`).

- [ ] **Step 3: Write the pure/rendering part of overlay_window.py**

`src/hitglow/overlay_window.py` (this file grows further in Task 5 — only the pure/rendering pieces are added now):
```python
"""Fenetre overlay HitGlow : transparence Win32 (layered window) et rendu.

Contrainte importante : tout ce qui est dessine sur la surface doit avoir
une alpha de 0 (invisible) ou 255 (opaque) — jamais une valeur intermediaire.
La fenetre layered saute volontairement l'etape de premultiplication de
l'alpha (voir LayeredWindow.update) pour rester performante sans dependance
a numpy ; ca ne fonctionne que si l'alpha est toujours binaire. Le "fondu"
des boutons est donc un fondu de COULEUR (RGB) vers COLOR_OFF, jamais un
fondu d'alpha.
"""

import pygame


def lerp_color(color_from, color_to, t):
    """Interpole lineairement entre deux couleurs RGB. t est clampe a [0, 1]."""
    t = max(0.0, min(1.0, t))
    return tuple(
        round(a + (b - a) * t)
        for a, b in zip(color_from, color_to)
    )


class ButtonGlow:
    """Suit la couleur d'affichage courante d'un bouton : couleur active
    tant qu'il est presse, puis fondu vers off_color sur fade_ms apres
    relachement."""

    def __init__(self, off_color, fade_ms):
        self.off_color = off_color
        self.fade_ms = fade_ms
        self._active_color = None
        self._last_pressed_ms = None

    def update(self, is_pressed, active_color, now_ms):
        if is_pressed:
            self._active_color = active_color
            self._last_pressed_ms = now_ms
            return active_color

        if self._active_color is None:
            return self.off_color

        elapsed = now_ms - self._last_pressed_ms
        if elapsed >= self.fade_ms:
            self._active_color = None
            return self.off_color

        t = elapsed / self.fade_ms
        return lerp_color(self._active_color, self.off_color, t)


def render_frame(
    width, height, glow_colors, direction_layout, action_layout,
    circle_radius, label_color, scale=1.0, calibration_lines=None,
):
    """Construit la frame a afficher : fond transparent + ronds colores
    (+ labels texte pour les boutons d'action) + overlay de calibration
    optionnel. Retourne une pygame.Surface avec canal alpha."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))

    for name, (x, y) in direction_layout.items():
        color = glow_colors[name]
        pygame.draw.circle(surface, color, (round(x * scale), round(y * scale)), round(circle_radius * scale))

    if action_layout:
        font = pygame.font.SysFont(None, max(1, round(20 * scale)))
        for name, (x, y) in action_layout.items():
            color = glow_colors[name]
            cx, cy = round(x * scale), round(y * scale)
            radius = round(circle_radius * scale)
            pygame.draw.circle(surface, color, (cx, cy), radius)
            label = font.render(name, False, label_color).convert_alpha()
            surface.blit(label, label.get_rect(center=(cx, cy)))

    if calibration_lines:
        _draw_calibration_overlay(surface, calibration_lines)

    return surface


def _draw_calibration_overlay(surface, lines):
    """Dessine le panneau de calibration : fond opaque uni (jamais
    translucide, pour respecter la contrainte alpha binaire) + texte."""
    font = pygame.font.SysFont(None, 22)
    line_height = 24
    panel_height = 12 + line_height * len(lines)
    panel_width = 360
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((10, 10, 10, 255))
    for i, line in enumerate(lines):
        text = font.render(line, False, (255, 255, 255)).convert_alpha()
        panel.blit(text, (8, 8 + i * line_height))
    surface.blit(panel, (0, 0))
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\pytest tests/test_overlay_render.py -v`
Expected: 8 passed.

- [ ] **Step 5: Commit**

```bash
git add src/hitglow/overlay_window.py tests/test_overlay_render.py
git commit -m "feat: add color fade math and pure frame rendering"
```

---

## Task 5: Win32 layered window (manual verification)

**Files:**
- Modify: `E:\HitGlow\src\hitglow\overlay_window.py` (append the Win32/window-management pieces below the pure functions from Task 4)

**Interfaces:**
- Consumes: `render_frame(...)` (Task 4) as the Surface it presents each frame.
- Produces: `LayeredWindow(hwnd, width, height)` with `.update(surface)` and `.close()`; `OverlayWindow(config)` with `.present(surface)`, `.start_drag(cursor_pos)`, `.drag_to(cursor_pos)`, `.end_drag()`, `.close()`, and module-level `get_cursor_pos() -> (x, y)` — consumed by Task 7 (`main.py`).
- **Not unit tested** — per Global Constraints, win32/window code is GUI/OS-dependent and is verified manually in Step 2 below.

- [ ] **Step 1: Append the Win32 window code to overlay_window.py**

Add to the top of `src/hitglow/overlay_window.py`, alongside the existing `import pygame`:
```python
import ctypes
from ctypes import wintypes
```

Append the rest of the file:
```python
user32 = ctypes.windll.user32
gdi32 = ctypes.windll.gdi32

GWL_EXSTYLE = -20
WS_EX_LAYERED = 0x00080000
HWND_TOPMOST = -1
SWP_NOMOVE = 0x0002
SWP_NOSIZE = 0x0001
SWP_NOZORDER = 0x0004
ULW_ALPHA = 0x02
AC_SRC_OVER = 0x00
AC_SRC_ALPHA = 0x01
DIB_RGB_COLORS = 0


class POINT(ctypes.Structure):
    _fields_ = [("x", ctypes.c_long), ("y", ctypes.c_long)]


class SIZE(ctypes.Structure):
    _fields_ = [("cx", ctypes.c_long), ("cy", ctypes.c_long)]


class BLENDFUNCTION(ctypes.Structure):
    _fields_ = [
        ("BlendOp", ctypes.c_byte),
        ("BlendFlags", ctypes.c_byte),
        ("SourceConstantAlpha", ctypes.c_byte),
        ("AlphaFormat", ctypes.c_byte),
    ]


class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", ctypes.c_long),
        ("biHeight", ctypes.c_long),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", ctypes.c_long),
        ("biYPelsPerMeter", ctypes.c_long),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD),
    ]


class BITMAPINFO(ctypes.Structure):
    _fields_ = [("bmiHeader", BITMAPINFOHEADER), ("bmiColors", wintypes.DWORD * 3)]


gdi32.CreateDIBSection.argtypes = [
    wintypes.HDC, ctypes.POINTER(BITMAPINFO), wintypes.UINT,
    ctypes.POINTER(ctypes.c_void_p), wintypes.HANDLE, wintypes.DWORD,
]
gdi32.CreateDIBSection.restype = ctypes.c_void_p

user32.UpdateLayeredWindow.argtypes = [
    wintypes.HWND, wintypes.HDC, ctypes.POINTER(POINT), ctypes.POINTER(SIZE),
    wintypes.HDC, ctypes.POINTER(POINT), wintypes.COLORREF,
    ctypes.POINTER(BLENDFUNCTION), wintypes.DWORD,
]
user32.UpdateLayeredWindow.restype = wintypes.BOOL

# Tous les handles/pointeurs Win32 ci-dessous peuvent depasser la plage
# d'un int C 32 bits sur un process 64 bits (ex: adresse d'un objet GDI).
# Sans argtypes explicites, ctypes convertit par defaut en c_int et leve
# "OverflowError: int too long to convert" des que la valeur est trop
# grande — d'ou la declaration systematique ci-dessous.
HGDIOBJ = wintypes.HANDLE

user32.GetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int]
user32.GetWindowLongW.restype = ctypes.c_long

user32.SetWindowLongW.argtypes = [wintypes.HWND, ctypes.c_int, ctypes.c_long]
user32.SetWindowLongW.restype = ctypes.c_long

user32.SetWindowPos.argtypes = [
    wintypes.HWND, wintypes.HWND, ctypes.c_int, ctypes.c_int,
    ctypes.c_int, ctypes.c_int, wintypes.UINT,
]
user32.SetWindowPos.restype = wintypes.BOOL

user32.GetWindowRect.argtypes = [wintypes.HWND, ctypes.POINTER(wintypes.RECT)]
user32.GetWindowRect.restype = wintypes.BOOL

user32.GetCursorPos.argtypes = [ctypes.POINTER(POINT)]
user32.GetCursorPos.restype = wintypes.BOOL

user32.GetDC.argtypes = [wintypes.HWND]
user32.GetDC.restype = wintypes.HDC

user32.ReleaseDC.argtypes = [wintypes.HWND, wintypes.HDC]
user32.ReleaseDC.restype = ctypes.c_int

gdi32.CreateCompatibleDC.argtypes = [wintypes.HDC]
gdi32.CreateCompatibleDC.restype = wintypes.HDC

gdi32.SelectObject.argtypes = [wintypes.HDC, HGDIOBJ]
gdi32.SelectObject.restype = HGDIOBJ

gdi32.DeleteObject.argtypes = [HGDIOBJ]
gdi32.DeleteObject.restype = wintypes.BOOL

gdi32.DeleteDC.argtypes = [wintypes.HDC]
gdi32.DeleteDC.restype = wintypes.BOOL


def get_cursor_pos():
    """Position du curseur en coordonnees ecran (pas coordonnees fenetre)."""
    pt = POINT()
    user32.GetCursorPos(ctypes.byref(pt))
    return pt.x, pt.y


class LayeredWindow:
    """Pousse une pygame.Surface (RGBA, alpha binaire) vers l'ecran via
    UpdateLayeredWindow pour une vraie transparence par pixel."""

    def __init__(self, hwnd, width, height):
        self.hwnd = hwnd
        self.width = width
        self.height = height

        style = user32.GetWindowLongW(hwnd, GWL_EXSTYLE)
        user32.SetWindowLongW(hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED)

        self._screen_dc = user32.GetDC(0)
        self._mem_dc = gdi32.CreateCompatibleDC(self._screen_dc)

        bmi = BITMAPINFO()
        bmi.bmiHeader.biSize = ctypes.sizeof(BITMAPINFOHEADER)
        bmi.bmiHeader.biWidth = width
        bmi.bmiHeader.biHeight = -height  # top-down
        bmi.bmiHeader.biPlanes = 1
        bmi.bmiHeader.biBitCount = 32
        bmi.bmiHeader.biCompression = 0  # BI_RGB

        self._bits_ptr = ctypes.c_void_p()
        self._bitmap = gdi32.CreateDIBSection(
            self._mem_dc, ctypes.byref(bmi), DIB_RGB_COLORS,
            ctypes.byref(self._bits_ptr), None, 0,
        )
        self._old_bitmap = gdi32.SelectObject(self._mem_dc, self._bitmap)

    def update(self, surface):
        """surface : pygame.Surface RGBA de taille (width, height), alpha
        binaire (0 ou 255) uniquement — voir le docstring du module."""
        raw = pygame.image.tostring(surface, "BGRA")
        ctypes.memmove(self._bits_ptr, raw, len(raw))

        size = SIZE(self.width, self.height)
        src_point = POINT(0, 0)
        blend = BLENDFUNCTION(AC_SRC_OVER, 0, 255, AC_SRC_ALPHA)

        user32.UpdateLayeredWindow(
            self.hwnd, self._screen_dc, None, ctypes.byref(size),
            self._mem_dc, ctypes.byref(src_point), 0, ctypes.byref(blend), ULW_ALPHA,
        )

    def close(self):
        gdi32.SelectObject(self._mem_dc, self._old_bitmap)
        gdi32.DeleteObject(self._bitmap)
        gdi32.DeleteDC(self._mem_dc)
        user32.ReleaseDC(0, self._screen_dc)


class OverlayWindow:
    """Fenetre pygame borderless, topmost, deplacable, avec transparence
    layered (ou fond chroma key de repli selon config.TRANSPARENT_BACKGROUND)."""

    def __init__(self, config):
        self.config = config
        pygame.display.set_caption("HitGlow")
        self.screen = pygame.display.set_mode((config.WINDOW_WIDTH, config.WINDOW_HEIGHT), pygame.NOFRAME)
        self.hwnd = pygame.display.get_wm_info()["window"]
        self._make_topmost()

        self.layered = None
        if config.TRANSPARENT_BACKGROUND:
            self.layered = LayeredWindow(self.hwnd, config.WINDOW_WIDTH, config.WINDOW_HEIGHT)

        self._drag_offset = None
        self._win_pos = self._get_window_pos()

    def _make_topmost(self):
        user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0, SWP_NOMOVE | SWP_NOSIZE)

    def _get_window_pos(self):
        rect = wintypes.RECT()
        user32.GetWindowRect(self.hwnd, ctypes.byref(rect))
        return rect.left, rect.top

    def present(self, surface):
        if self.layered is not None:
            self.layered.update(surface)
        else:
            self.screen.fill(self.config.CHROMA_FALLBACK_COLOR)
            self.screen.blit(surface, (0, 0))
            pygame.display.flip()
            self._make_topmost()

    def start_drag(self, cursor_pos):
        self._drag_offset = (cursor_pos[0] - self._win_pos[0], cursor_pos[1] - self._win_pos[1])

    def drag_to(self, cursor_pos):
        if self._drag_offset is None:
            return
        new_x = cursor_pos[0] - self._drag_offset[0]
        new_y = cursor_pos[1] - self._drag_offset[1]
        user32.SetWindowPos(self.hwnd, 0, new_x, new_y, 0, 0, SWP_NOSIZE | SWP_NOZORDER)
        self._win_pos = (new_x, new_y)

    def end_drag(self):
        self._drag_offset = None

    def close(self):
        if self.layered is not None:
            self.layered.close()
```

- [ ] **Step 2: Manual smoke test (no automated test — see Global Constraints)**

Run this ad hoc script to confirm the window opens, is topmost, and is transparent:
```bash
.venv\Scripts\python -c "import pygame, time; from hitglow import config; from hitglow.overlay_window import OverlayWindow, render_frame; pygame.init(); w = OverlayWindow(config); surf = render_frame(config.WINDOW_WIDTH, config.WINDOW_HEIGHT, {k: config.COLOR_DIRECTION for k in config.DIRECTION_LAYOUT}, config.DIRECTION_LAYOUT, {}, config.CIRCLE_RADIUS, config.COLOR_LABEL_TEXT); [w.present(surf) or time.sleep(0.05) for _ in range(100)]"
```
Expected: a window with 4 cyan circles appears on top of everything else, with a fully see-through background (desktop visible around the circles), for ~5 seconds. If instead the whole window shows as solid black or solid magenta, the layered-window path failed — flip `TRANSPARENT_BACKGROUND = False` in `config.py` as the documented fallback and note the failure for later investigation; do not block the rest of the plan on this, since Task 7 wires calibration/drag before this is exercised interactively.

- [ ] **Step 3: Run the full test suite to confirm nothing else broke**

Run: `.venv\Scripts\pytest -v`
Expected: all previous tests still pass (the new code added no importable side effects at module load).

- [ ] **Step 4: Commit**

```bash
git add src/hitglow/overlay_window.py
git commit -m "feat: add Win32 layered-window transparency, topmost, and drag"
```

---

## Task 6: Calibration mode

**Files:**
- Create: `E:\HitGlow\src\hitglow\calibration.py`
- Test: `E:\HitGlow\tests\test_calibration.py`

**Interfaces:**
- Consumes: nothing (pure formatting function, takes raw values).
- Produces: `format_calibration_lines(hat_value, axis_values, pressed_button_indices) -> list[str]` — consumed by Task 7 (`main.py`), which passes the result into `render_frame(..., calibration_lines=...)` from Task 4.

- [ ] **Step 1: Write the failing tests**

`tests/test_calibration.py`:
```python
from hitglow.calibration import format_calibration_lines


def test_shows_hat_value():
    lines = format_calibration_lines((1, -1), [], [])
    assert lines[0] == "HAT: (1, -1)"


def test_shows_each_axis_with_two_decimals():
    lines = format_calibration_lines((0, 0), [0.5, -0.333], [])
    assert "AXIS 0: +0.50" in lines
    assert "AXIS 1: -0.33" in lines


def test_shows_pressed_buttons_sorted():
    lines = format_calibration_lines((0, 0), [], [5, 1, 3])
    assert lines[-1] == "BOUTONS: [1, 3, 5]"


def test_shows_placeholder_when_no_button_pressed():
    lines = format_calibration_lines((0, 0), [], [])
    assert lines[-1] == "BOUTONS: (aucun)"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.venv\Scripts\pytest tests/test_calibration.py -v`
Expected: FAIL (`ModuleNotFoundError: No module named 'hitglow.calibration'`).

- [ ] **Step 3: Write calibration.py**

`src/hitglow/calibration.py`:
```python
"""Mode calibration : formatte l'etat brut de la manette en texte lisible
pour identifier quel input physique correspond a quel index."""


def format_calibration_lines(hat_value, axis_values, pressed_button_indices):
    lines = [f"HAT: {tuple(hat_value)}"]
    for i, value in enumerate(axis_values):
        lines.append(f"AXIS {i}: {value:+.2f}")
    if pressed_button_indices:
        lines.append(f"BOUTONS: {sorted(pressed_button_indices)}")
    else:
        lines.append("BOUTONS: (aucun)")
    return lines
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `.venv\Scripts\pytest tests/test_calibration.py -v`
Expected: 4 passed.

- [ ] **Step 5: Commit**

```bash
git add src/hitglow/calibration.py tests/test_calibration.py
git commit -m "feat: add calibration mode text formatting"
```

---

## Task 7: Main loop and launcher

**Files:**
- Create: `E:\HitGlow\src\hitglow\main.py`
- Create: `E:\HitGlow\run_hitglow.py`

**Interfaces:**
- Consumes: `hitglow.config` (Task 2), `resolve_directions`/`resolve_action_buttons`/`JoystickReader` (Task 3), `ButtonGlow`/`render_frame`/`OverlayWindow`/`get_cursor_pos` (Tasks 4–5), `format_calibration_lines` (Task 6).
- Produces: `main.run()` — the entry point called by `run_hitglow.py`.
- **Not unit tested** — the full loop requires a real joystick and window (per Global Constraints); verified manually in Step 2.

- [ ] **Step 1: Write main.py**

`src/hitglow/main.py`:
```python
"""Boucle principale HitGlow : lit la manette, met a jour les couleurs des
ronds, affiche la fenetre overlay."""

import sys

import pygame

from hitglow import config
from hitglow.calibration import format_calibration_lines
from hitglow.input_reader import JoystickReader, resolve_action_buttons, resolve_directions
from hitglow.overlay_window import ButtonGlow, OverlayWindow, get_cursor_pos, render_frame

FPS = 60


def _row_color(name):
    if name in config.ACTION_ROW_TOP:
        return config.COLOR_ROW_TOP
    return config.COLOR_ROW_BOTTOM


def run():
    pygame.init()

    try:
        joystick = JoystickReader(config.JOYSTICK_INDEX)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        pygame.quit()
        sys.exit(1)

    window = OverlayWindow(config)
    clock = pygame.time.Clock()

    glows = {name: ButtonGlow(config.COLOR_DIRECTION, config.FADE_MS) for name in config.DIRECTION_LAYOUT}
    active_colors = {name: config.COLOR_DIRECTION for name in config.DIRECTION_LAYOUT}
    for name in config.ACTION_LAYOUT:
        glows[name] = ButtonGlow(config.COLOR_OFF, config.FADE_MS)
        active_colors[name] = _row_color(name)

    scale = config.INITIAL_SCALE
    calibration_mode = False
    dragging = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == config.QUIT_KEY:
                    running = False
                elif event.key == config.CALIBRATION_KEY:
                    calibration_mode = not calibration_mode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging = True
                window.start_drag(get_cursor_pos())
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
                window.end_drag()
            elif event.type == pygame.MOUSEMOTION and dragging:
                window.drag_to(get_cursor_pos())
            elif event.type == pygame.MOUSEWHEEL:
                scale += event.y * config.SCALE_STEP
                scale = max(config.MIN_SCALE, min(config.MAX_SCALE, scale))

        hat, axes, buttons = joystick.poll(config.HAT_INDEX)
        directions = resolve_directions(
            hat, axes, buttons,
            config.DIRECTION_SOURCE, config.AXIS_MAPPING, config.AXIS_DEADZONE,
            config.BUTTON_DIRECTION_MAPPING,
        )
        actions = resolve_action_buttons(buttons, config.ACTION_BUTTONS)
        pressed = {**directions, **actions}

        now_ms = pygame.time.get_ticks()
        glow_colors = {
            name: glows[name].update(pressed[name], active_colors[name], now_ms)
            for name in glows
        }

        calibration_lines = None
        if calibration_mode:
            calibration_lines = format_calibration_lines(hat, axes, [i for i, pressed_ in enumerate(buttons) if pressed_])

        frame = render_frame(
            config.WINDOW_WIDTH, config.WINDOW_HEIGHT, glow_colors,
            config.DIRECTION_LAYOUT, config.ACTION_LAYOUT, config.CIRCLE_RADIUS,
            config.COLOR_LABEL_TEXT, scale=scale, calibration_lines=calibration_lines,
        )
        window.present(frame)
        clock.tick(FPS)

    window.close()
    pygame.quit()
```

- [ ] **Step 2: Write the root launcher**

`run_hitglow.py`:
```python
"""Lanceur HitGlow : python run_hitglow.py"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from hitglow.main import run

if __name__ == "__main__":
    run()
```

- [ ] **Step 3: Manual verification (no automated test — see Global Constraints)**

With the leverless controller plugged in:
```bash
.venv\Scripts\python run_hitglow.py
```
Expected: the overlay window opens, topmost, transparent (or magenta if `TRANSPARENT_BACKGROUND = False`); pressing `C` toggles the calibration text panel showing live hat/axis/button values; dragging the window with the left mouse button moves it; the mouse wheel resizes the circles; `Échap` closes the window cleanly (no traceback). Since `config.py` mapping is still all `None` at this point, no circle will light up yet — that's expected; mapping is filled in by the end user after calibration, per the spec.

- [ ] **Step 4: Run the full test suite one more time**

Run: `.venv\Scripts\pytest -v`
Expected: all tests still pass (12+ tests total from Tasks 1–3, 4, 6; `main.py`/`run_hitglow.py` are untested by design).

- [ ] **Step 5: Commit**

```bash
git add src/hitglow/main.py run_hitglow.py
git commit -m "feat: wire input, rendering, calibration and drag into the main loop"
```

---

## Task 8: README

**Files:**
- Create: `E:\HitGlow\README.md`

**Interfaces:**
- Consumes: nothing (documentation only).
- Produces: nothing consumed by code; this is the public-facing entry point of the repo.

- [ ] **Step 1: Write README.md**

`README.md`:
```markdown
# HitGlow

Overlay desktop Windows qui affiche en temps reel les inputs d'une manette
leverless (Haute42 sous GP2040-CE, vue comme un pad standard) — pense pour
le stream Tekken 8 capture avec OBS.

![Apercu de l'overlay HitGlow](docs/screenshot-placeholder.png)
<!-- TODO: remplacer par une vraie capture ou un GIF de l'overlay en action -->

## Fonctionnalites

- Fenetre sans bordure, toujours au-dessus, deplacable au clic-glisser,
  redimensionnable a la molette.
- Vraie transparence Windows par pixel (pas besoin de filtre chroma key
  dans OBS dans le cas general) — avec un mode de repli fond uni magenta
  configurable si ta methode de capture OBS ne gere pas bien l'alpha.
- Bloc directions (gauche) : Gauche / Bas / Droite alignes + Haut decale
  en dessous (position pouce), en cyan.
- Bloc actions (droite) : 6 ronds en quinconce façon hitbox — `1`, `2`,
  `3`, `4` (attaques) + `HEAT`, `RAGE`, rangee haute en jaune, rangee
  basse en rouge.
- Fondu de couleur configurable a l'extinction d'un bouton.
- Mode calibration (touche `C`) : affiche en direct l'index du hat, la
  valeur de tous les axes et la liste des boutons presses, pour mapper
  precisement TA manette sans rien deviner.

## Prerequis

- Windows 10 (1903+) ou Windows 11.
- Python 3.11 ou plus recent.
- La manette leverless branchee et reconnue par Windows.

## Installation

```bash
git clone https://github.com/Khatoonn/HitGlow.git
cd HitGlow
python -m venv .venv
.venv\Scripts\pip install -r requirements.txt
```

## Lancement

```bash
.venv\Scripts\python run_hitglow.py
```

## Calibration du mapping

Le fichier [`src/hitglow/config.py`](src/hitglow/config.py) centralise tout
le mapping — aucun index n'est devine, tous les champs demarrent a `None`.

1. Lance HitGlow puis appuie sur `C` pour activer le mode calibration.
2. Un panneau de texte affiche en direct :
   - `HAT: (x, y)` — la valeur du D-pad/hat si ta manette en envoie un.
   - `AXIS i: ±v.vv` — la valeur de chaque axe, pour les manettes qui
     envoient les directions comme des axes.
   - `BOUTONS: [...]` — les index des boutons actuellement presses.
3. Presse chaque direction et chaque bouton d'action un par un, note les
   index/axes qui bougent.
4. Reporte ces valeurs dans `config.py` :
   - `DIRECTION_SOURCE` : mets `"hat"`, `"axis"` ou `"button"` pour
     chaque direction selon ce que tu as observe.
   - Selon la source choisie, renseigne `HAT_INDEX`, `AXIS_MAPPING`
     (`(index_axe, signe)`) ou `BUTTON_DIRECTION_MAPPING`.
   - `ACTION_BUTTONS` : l'index de bouton brut pour `"1"`, `"2"`, `"3"`,
     `"4"`, `"HEAT"`, `"RAGE"`.
5. Relance HitGlow (ou re-presse `C` pour ressortir du mode calibration)
   et verifie que chaque rond s'allume au bon moment.

Couleurs, tailles, positions des ronds et duree du fondu (`FADE_MS`) sont
egalement dans `config.py`, commentes, modifiables librement.

## Integration OBS

1. Lance HitGlow, positionne et redimensionne la fenetre comme tu veux
   (clic-glisser pour deplacer, molette pour redimensionner).
2. Dans OBS, ajoute une source **Capture de fenetre** (Window Capture),
   cible la fenetre `HitGlow`.
   - Methode de capture recommandee : **Windows 10 (1903 et plus)**
     (Windows Graphics Capture) — c'est celle qui restitue correctement
     la transparence par pixel de la fenetre.
3. Si la fenetre apparait opaque/noire dans OBS malgre tout : ouvre
   `src/hitglow/config.py` et passe `TRANSPARENT_BACKGROUND` a `False`.
   HitGlow bascule alors sur un fond magenta uni (`#FF00FF`) — ajoute
   simplement un filtre **Incrustation couleur** (Chroma Key) sur la
   source dans OBS, cible le magenta.

## Build en .exe

```bash
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller --onefile --noconsole --name HitGlow run_hitglow.py
```

L'executable est genere dans `dist/HitGlow.exe`.

## Structure du projet

```
HitGlow/
├── run_hitglow.py          # lanceur : python run_hitglow.py
├── src/hitglow/
│   ├── config.py             # mapping, couleurs, layout — a editer
│   ├── input_reader.py       # lecture manette (hat/axes/boutons)
│   ├── overlay_window.py     # fenetre transparente Win32 + rendu
│   ├── calibration.py        # formatage du mode calibration
│   └── main.py                 # boucle principale
├── tests/                    # tests de la logique pure (pytest)
├── requirements.txt
├── requirements-dev.txt
├── LICENSE                    # MIT
└── .gitignore
```

## Licence

MIT — voir [LICENSE](LICENSE).
```

- [ ] **Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add complete French README"
```

---

## Task 9: Build the .exe

**Files:**
- No new source files — this task only produces `dist/HitGlow.exe` (already gitignored per Task 1).

**Interfaces:**
- Consumes: `run_hitglow.py` (Task 7).
- Produces: nothing consumed by later tasks — this is a manual packaging verification.

- [ ] **Step 1: Install PyInstaller and build**

```bash
.venv\Scripts\pip install pyinstaller
.venv\Scripts\pyinstaller --onefile --noconsole --name HitGlow run_hitglow.py
```
Expected: no build errors; `dist\HitGlow.exe` exists.

- [ ] **Step 2: Manual verification**

```bash
dist\HitGlow.exe
```
Expected: same behavior as `python run_hitglow.py` in Task 7 Step 3 — window opens, topmost, transparent/magenta, calibration toggles with `C`, drag/resize/quit all work. Close the exe when confirmed.

- [ ] **Step 3: Clean up build artifacts before the next commit**

`build/`, `dist/`, and `*.spec` are already in `.gitignore` from Task 1 — confirm with `git status` that they don't show as untracked-to-be-added.

No commit needed for this task (nothing new is tracked by git).

---

## Task 10: Publish to GitHub

**Files:**
- No new files.

**Interfaces:**
- Consumes: the complete repo from Tasks 1–9.
- Produces: the public repo at `https://github.com/Khatoonn/HitGlow`.

- [ ] **Step 1: Final local commit check**

```bash
git status
```
Expected: clean working tree (everything from Tasks 1–8 already committed). If anything is outstanding, `git add` and commit it with a descriptive message before continuing.

- [ ] **Step 2: Confirm GitHub authentication**

```bash
gh auth status
```
Expected: shows an authenticated account. If not authenticated, stop and tell the user to run `gh auth login` themselves (credential handling is not something to automate).

- [ ] **Step 3: Create the GitHub repository and push**

```bash
gh repo create Khatoonn/HitGlow --public --source=. --remote=origin --push
```
Expected: repo created (or, if it already exists, this step fails — in that case use `git remote add origin https://github.com/Khatoonn/HitGlow.git` and `git push -u origin main` instead) and all commits pushed to `main`.

- [ ] **Step 4: Verify**

```bash
gh repo view Khatoonn/HitGlow --web
```
Expected: opens the repo in the browser showing the full file tree and README rendered.

---

## Self-Review Notes

- **Spec coverage:** every spec section maps to a task — stack/deps (Tasks 1, 9), transparency + fallback (Task 5), window behavior/drag/resize (Tasks 5, 7), joystick reading + 3 direction sources (Task 3), calibration mode (Task 6), layout/colors/fade (Tasks 2, 4), config centralization (Task 2), file tree (Task 1 onward), packaging (Task 9), git/publication (Tasks 1, 10), tests scope (Global Constraints + every task's Interfaces section).
- **Placeholder scan:** no TBD/TODO in code; the one `<!-- TODO -->` HTML comment in the README is an intentional, user-facing placeholder for a screenshot the assistant cannot generate, not a plan gap.
- **Type consistency:** `resolve_directions`/`resolve_action_buttons` return `dict[str, bool]` in Task 3 and are merged (`{**directions, **actions}`) in Task 7 exactly as produced. `ButtonGlow.update` returns the same `tuple[int,int,int]` shape as `lerp_color` and `config` color constants throughout. `render_frame`'s `glow_colors` parameter is fed exactly the dict `main.py` builds from `ButtonGlow.update` calls, keyed by the same names as `DIRECTION_LAYOUT`/`ACTION_LAYOUT`.
