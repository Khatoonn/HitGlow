"""Lanceur HitGlow : python run_hitglow.py (fenetre de parametrage) ou
python run_hitglow.py --overlay (overlay transparent, normalement lance
depuis la fenetre de parametrage en sous-processus)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))


def main():
    if "--overlay" in sys.argv:
        from hitglow.overlay_main import run
        run()
    else:
        from hitglow.settings_app import launch
        launch()


if __name__ == "__main__":
    main()
