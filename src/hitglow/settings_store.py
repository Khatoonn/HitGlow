"""Persistance des parametres HitGlow (JSON) et logique pure associee :
resolution de la manette selectionnee, detection d'un nouvel input pendant
le mapping interactif. Remplace l'edition manuelle d'un config.py."""

import copy
import json
import os
from pathlib import Path

DEFAULT_SETTINGS = {
    "joystick_name": None,
    "joystick_index": 0,
    "direction_source": {"UP": None, "DOWN": None, "LEFT": None, "RIGHT": None},
    "hat_index": 0,
    "axis_mapping": {"UP": None, "DOWN": None, "LEFT": None, "RIGHT": None},
    "axis_deadzone": 0.5,
    "button_direction_mapping": {"UP": None, "DOWN": None, "LEFT": None, "RIGHT": None},
    "action_buttons": {"1": None, "2": None, "3": None, "4": None, "HEAT": None, "RAGE": None},
    "window_width": 640,
    "window_height": 320,
    "window_pos": None,
    "transparent_background": True,
    "chroma_fallback_color": [255, 0, 255],
    "scale": 1.0,
    "colors": {
        "off": [40, 40, 40],
        "direction": [0, 255, 255],
        "row_top": [255, 220, 0],
        "row_bottom": [220, 0, 0],
        "label_text": [255, 255, 255],
    },
    "fade_ms": 150,
}


def settings_path():
    """Emplacement du fichier de parametres : %APPDATA%\\HitGlow\\settings.json
    (persiste independamment de l'endroit ou l'exe est installe)."""
    appdata = Path(os.environ.get("APPDATA", str(Path.home())))
    directory = appdata / "HitGlow"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "settings.json"


def load_settings(path=None):
    """Charge les parametres depuis path (ou l'emplacement par defaut),
    fusionnes avec DEFAULT_SETTINGS pour que les cles manquantes (ancien
    fichier, nouvelle version) aient toujours une valeur."""
    path = path or settings_path()
    merged = copy.deepcopy(DEFAULT_SETTINGS)
    if path.exists():
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _deep_update(merged, data)
    return merged


def save_settings(settings, path=None):
    path = path or settings_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2, ensure_ascii=False)


def _deep_update(base, overrides):
    for key, value in overrides.items():
        if isinstance(value, dict) and isinstance(base.get(key), dict):
            _deep_update(base[key], value)
        else:
            base[key] = value


def resolve_joystick_index(available_names, saved_name, saved_index):
    """Determine quel index de manette utiliser parmi celles actuellement
    detectees (available_names), a partir du nom sauvegarde (prioritaire,
    car les index peuvent changer d'une session a l'autre) ou de l'index
    sauvegarde en repli. Retourne None si aucune manette n'est branchee."""
    if not available_names:
        return None
    if saved_name is not None and saved_name in available_names:
        return available_names.index(saved_name)
    if saved_index is not None and 0 <= saved_index < len(available_names):
        return saved_index
    return 0


def detect_new_input(baseline, current, axis_threshold=0.5):
    """Compare deux etats bruts de manette ('hat', 'axes', 'buttons') et
    retourne le premier input qui a change de facon significative depuis
    baseline, sous la forme (source, payload) :
      - ("hat", (x, y))
      - ("axis", (index, signe))
      - ("button", index)
    Retourne None si rien de significatif n'a change."""
    if tuple(current["hat"]) != tuple(baseline["hat"]):
        return ("hat", tuple(current["hat"]))

    for i, (b, c) in enumerate(zip(baseline["axes"], current["axes"])):
        if abs(c) > axis_threshold and abs(c - b) > axis_threshold:
            sign = 1 if c > 0 else -1
            return ("axis", (i, sign))

    for i, (b, c) in enumerate(zip(baseline["buttons"], current["buttons"])):
        if c and not b:
            return ("button", i)

    return None


def apply_detection(settings, target, is_direction, detection):
    """Applique le resultat de detect_new_input() aux parametres, pour le
    mapping interactif ("Detecter") de la fenetre de parametrage.

    Pour un bouton d'action (is_direction=False), seul un input de type
    "button" est accepte : un hat/axe ignore accidentellement pendant
    l'attente (drift de stick, etc.) ne doit pas produire un mapping
    incorrect."""
    source, payload = detection
    if is_direction:
        if source == "hat":
            settings["direction_source"][target] = "hat"
        elif source == "axis":
            settings["direction_source"][target] = "axis"
            settings["axis_mapping"][target] = list(payload)
        elif source == "button":
            settings["direction_source"][target] = "button"
            settings["button_direction_mapping"][target] = payload
    elif source == "button":
        settings["action_buttons"][target] = payload
