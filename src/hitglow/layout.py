"""Positions/tailles des ronds — geometrie fixe du layout hitbox, separee
des reglages utilisateur (mapping, couleurs...) geres par settings_store.
"""

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
# le croquis fourni par l'utilisateur. Rapproche du bloc directions (moins
# d'espace vide entre les deux blocs).
ACTION_LAYOUT = {
    "1": (260, 130),
    "3": (250, 195),
    "2": (330, 105),
    "4": (320, 165),
    "HEAT": (400, 110),
    "RAGE": (390, 180),
}

ACTION_ROW_TOP = {"1", "2", "HEAT"}
ACTION_ROW_BOTTOM = {"3", "4", "RAGE"}
