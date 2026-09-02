"""Lanceur HitGlow :
  python run_hitglow.py                     -> fenetre de parametrage
  python run_hitglow.py --overlay           -> overlay transparent des inputs
  python run_hitglow.py --trainer --combo X -> combo trainer (combo id=X)
Les modes --overlay et --trainer sont normalement lances depuis la fenetre
de parametrage, en sous-processus."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    if "--overlay" in sys.argv:
        from hitglow.overlay_main import run
        run()
    elif "--trainer" in sys.argv:
        from hitglow.trainer_main import run
        combo_id = sys.argv[sys.argv.index("--combo") + 1] if "--combo" in sys.argv else None
        run(combo_id)
    else:
        from hitglow.settings_app import launch
        launch()


if __name__ == "__main__":
    main()
