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
