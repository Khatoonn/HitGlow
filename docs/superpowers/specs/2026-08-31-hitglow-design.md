# HitGlow — Design

Date : 2026-08-31
Repo cible : https://github.com/Khatoonn/HitGlow

## Contexte et objectif

HitGlow est un overlay desktop Windows qui affiche en temps réel les inputs d'une
manette leverless (Haute42 sous GP2040-CE, exposée comme un pad standard SDL/DirectInput)
pour du stream Tekken 8 capturé dans OBS. L'utilisateur veut un `.py` unique à lancer,
empaquetable en `.exe` via PyInstaller, avec un mapping entièrement configurable (aucun
index deviné) et un mode de calibration pour identifier les inputs physiques.

## Stack

- **Python 3.11+**
- **pygame** : lecture manette (`pygame.joystick` — hat/axes/boutons), boucle
  d'événements, rendu 2D (Surface avec canal alpha), police pour les labels texte.
- **ctypes (stdlib)** : appels Win32 (`user32`, `gdi32`) pour la fenêtre borderless
  layered/topmost et `UpdateLayeredWindow`. Pas de dépendance `pywin32`, pour rester
  simple à empaqueter avec PyInstaller.

## Transparence de fenêtre

Décision : **vraie transparence Windows** (et non un simple chroma key retiré côté OBS),
avec un mode de repli configurable.

- Fenêtre pygame borderless (`pygame.NOFRAME`) ; on récupère le HWND via
  `pygame.display.get_wm_info()['window']`.
- Style étendu `WS_EX_LAYERED` posé via `SetWindowLong`/`SetWindowLongPtr`, fenêtre
  passée en `HWND_TOPMOST` via `SetWindowPos`.
- Chaque frame, au lieu de `pygame.display.flip()`, on construit un DIB 32 bits BGRA
  premultiplié à partir de la Surface pygame et on l'envoie via `UpdateLayeredWindow`
  → transparence par pixel réelle, pas juste une couleur clé masquée en post-traitement.
- **Repli configurable** (`TRANSPARENT_BACKGROUND = False` dans `config.py`) : fond uni
  magenta `#FF00FF` (chroma key classique), pour le cas où une méthode de capture OBS
  particulière ne restituerait pas bien l'alpha d'une fenêtre layered. Documenté dans le
  README avec la recommandation d'utiliser la méthode de capture "Windows 10 (1903 et
  plus)" / WGC dans OBS pour la transparence réelle.

## Fenêtre : comportement

- Toujours au-dessus (topmost).
- Déplaçable : clic-gauche + drag n'importe où sur la fenêtre (pas de barre de titre —
  gestion manuelle via `MOUSEBUTTONDOWN`/`MOUSEMOTION` + `SetWindowPos`).
- Redimensionnable : molette souris (facteur d'échelle global appliqué au layout).
- `Échap` : quitter. `C` : bascule le mode calibration.

## Lecture manette

`input_reader.py` interroge `pygame.joystick` à chaque frame et expose un état :
boutons pressés (par index brut), valeurs de tous les axes, valeur du hat.

Le mapping direction supporte **trois sources possibles**, configurables indépendamment
par direction, car GP2040-CE peut être configuré différemment selon le mode :
- **hat/D-pad** (POV) — index du hat (`HAT_INDEX`)
- **axes** — index d'axe + seuil de deadzone (`AXIS_DEADZONE`)
- **boutons digitaux** — index de bouton classique

Tous les index par défaut dans `config.py` sont `None` (rien de deviné) ; l'utilisateur
les renseigne après calibration.

## Mode calibration

Activé par `C`. Affiche en overlay texte, mis à jour en direct :
- valeur courante du hat
- valeur de chaque axe détecté sur le joystick
- liste des index de boutons actuellement pressés

Permet à l'utilisateur d'identifier quel input physique correspond à quel index, sans
qu'aucun mapping ne soit pré-supposé côté code.

## Layout des ronds (déduit du croquis fourni par l'utilisateur)

**Bloc directions (gauche, 4 ronds, couleur cyan)**
- `B` (Back/Gauche), `D` (Bas), `F` (Forward/Droite) alignés horizontalement.
- `U` (Haut) positionné en dessous et légèrement décalé — position pouce, comme sur un
  hitbox physique où le pouce vient chercher le "Up" par en dessous.

**Bloc actions (droite, 6 ronds, quinconce diagonal en 3 colonnes × 2 rangées)**
- Colonne 1 : `1` (haut) / `3` (bas)
- Colonne 2 : `2` (haut) / `4` (bas)
- Colonne 3 : `HEAT` (haut) / `RAGE` (bas)
- Chaque colonne est décalée vers le haut-droite par rapport à la précédente
  (effet diagonal caractéristique d'un layout hitbox), comme dans le croquis fourni.
- Rangée haute (`1`, `2`, `HEAT`) = jaune. Rangée basse (`3`, `4`, `RAGE`) = rouge.
- Les 6 boutons affichent un label texte sur le rond (`1`, `2`, `3`, `4`, `HEAT`, `RAGE`),
  configurable dans `config.py`.

Note évolutivité (hors scope actuel, à ne pas construire maintenant) : l'utilisateur a
indiqué vouloir plus tard un mapping manuel pour joueurs clavier, puis pour d'autres
manettes. Le mapping restera donc organisé en une structure claire par "input logique →
source physique" dans `config.py`, sans coupler le rendu à la lecture manette, pour
faciliter une extension future sans réécriture.

## Couleurs et fondu

- Éteint : gris foncé.
- Directions actives : cyan.
- Rangée haute active : jaune.
- Rangée basse active : rouge.
- À l'extinction, interpolation linéaire de la couleur active vers le gris foncé sur une
  durée `FADE_MS` configurable (défaut 150 ms), plutôt qu'un fondu d'alpha (les ronds
  restent visibles à l'état "off").

## Configuration

Tout (mapping, couleurs, layout, tailles, deadzone, `FADE_MS`, touches clavier,
`TRANSPARENT_BACKGROUND`, couleur de repli) est centralisé et commenté en haut de
`src/hitglow/config.py`, modifiable à la main sans toucher au reste du code.

## Arborescence

```
HitGlow/
├── run_hitglow.py          # lanceur unique : python run_hitglow.py
├── src/hitglow/
│   ├── __init__.py
│   ├── config.py            # mapping, couleurs, layout, touches — tout commenté
│   ├── input_reader.py      # lecture pygame.joystick (hat/axes/boutons)
│   ├── overlay_window.py    # fenêtre layered win32 + rendu + drag/resize
│   ├── calibration.py       # overlay texte live des index/valeurs bruts
│   └── main.py               # boucle principale, assemblage des modules
├── requirements.txt          # pygame
├── README.md                 # FR complet
├── LICENSE                   # MIT
└── .gitignore
```

## Packaging

`pyinstaller --onefile --noconsole --name HitGlow run_hitglow.py`

## Git / publication

`git init` + premier commit fait localement par l'assistant. Le push vers
`https://github.com/Khatoonn/HitGlow` n'est exécuté qu'après confirmation explicite de
l'utilisateur ; la suite de commandes est de toute façon fournie dans le README.

## Tests

Projet GUI/matériel non testable unitairement de façon utile (dépend d'une manette
physique et du rendu fenêtré). Vérification par test manuel : lancement, calibration
avec la manette réelle, vérification visuelle dans OBS (Window Capture, méthode WGC).
Pas de suite de tests automatisés — hors scope pour un outil personnel de cette taille.

## Hors scope (explicitement reporté)

- Mapping clavier.
- Support multi-manettes / profils de mapping multiples.
- Détection automatique de la manette par nom/VID-PID.
