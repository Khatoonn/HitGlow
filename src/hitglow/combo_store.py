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


def add_combo(combos, character, name, notation, game="Tekken 8"):
    """Ajoute un combo a la liste (mutee en place) et le retourne."""
    combo = {
        "id": str(uuid.uuid4()),
        "game": (game or "Tekken 8").strip() or "Tekken 8",
        "character": character.strip(),
        "name": name.strip(),
        "notation": notation.strip(),
    }
    combos.append(combo)
    return combo


def grouped_by_game_and_character(combos):
    """Regroupe les combos par (jeu, personnage), tries alphabetiquement,
    pour un affichage range plutot qu'une liste plate. Le regroupement est
    insensible a la casse ("Steve" et "STEVE" tombent dans le meme groupe)
    pour eviter que deux saisies differentes du meme nom ne se retrouvent
    dans des groupes separes ; l'affichage est normalise en Title Case.
    Retourne une liste de ((jeu, personnage), [combos])."""
    groups = {}
    for combo in combos:
        game = (combo.get("game") or "Tekken 8").strip()
        character = combo["character"].strip()
        key = (game.lower(), character.lower())
        groups.setdefault(key, []).append(combo)
    return [((key[0].title(), key[1].title()), groups[key]) for key in sorted(groups)]


def remove_combo(combos, combo_id):
    """Retire (en place) le combo dont l'id correspond. Ne fait rien si
    l'id est introuvable."""
    combos[:] = [c for c in combos if c["id"] != combo_id]
