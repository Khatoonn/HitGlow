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
.venv\Scripts\pyinstaller --onefile --noconsole --name HitGlow --paths src run_hitglow.py
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
