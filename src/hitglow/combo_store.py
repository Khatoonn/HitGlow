"""Persistance des combos sauvegardes (combos.json) pour le trainer.
Seule la notation brute est stockee — le parsing (combo_parser) est pur et
deterministe, pas la peine de dupliquer les etapes derivees sur disque."""

import json
import os
import uuid
from pathlib import Path


def combos_path():
    appdata = Path(os.environ.get("APPDATA", str(Path.home())))
    directory = appdata / "HitGlow"
    directory.mkdir(parents=True, exist_ok=True)
    return directory / "combos.json"


def load_combos(path=None):
    """Retourne la liste des combos sauvegardes (liste vide si aucun
    fichier n'existe encore)."""
    path = path or combos_path()
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("combos", [])


def save_combos(combos, path=None):
    path = path or combos_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"combos": combos}, f, indent=2, ensure_ascii=False)


def add_combo(combos, character, name, notation):
    """Ajoute un combo a la liste (mutee en place) et le retourne."""
    combo = {
        "id": str(uuid.uuid4()),
        "character": character.strip(),
        "name": name.strip(),
        "notation": notation.strip(),
    }
    combos.append(combo)
    return combo


def remove_combo(combos, combo_id):
    """Retire (en place) le combo dont l'id correspond. Ne fait rien si
    l'id est introuvable."""
    combos[:] = [c for c in combos if c["id"] != combo_id]
