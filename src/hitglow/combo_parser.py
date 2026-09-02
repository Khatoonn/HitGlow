"""Parseur de notation de combo Tekken (ex: "f+3,1 pass df+1,[ 2~1 ] pass f+2,2")
vers une suite d'etapes. Chaque etape est soit "trackable" (resolue en un
ensemble d'inputs HitGlow reels — directions/boutons — que le trainer peut
detecter en direct), soit gardee en texte brut quand la notation depend de
conventions propres a un personnage (noms de stance en capitales comme IZU/
LNH/PAB), d'une condition (CH, heat on, FC, ws) ou d'une annotation (T!,
"~X", parentheses/crochets) qu'on ne peut pas fiablement traduire en input
sans se tromper. Mieux vaut une etape affichee en texte que mal interpretee.
"""

import re

DIRECTION_TO_INPUTS = {
    "u": {"UP"},
    "d": {"DOWN"},
    "f": {"RIGHT"},
    "b": {"LEFT"},
    "uf": {"UP", "RIGHT"},
    "ub": {"UP", "LEFT"},
    "df": {"DOWN", "RIGHT"},
    "db": {"DOWN", "LEFT"},
}

# L'ordre compte : les directions a 2 lettres doivent etre tentees avant
# leurs prefixes a 1 lettre (sinon "uf" matcherait "u" puis echouerait sur
# le "f" restant).
_CLEAN_TOKEN_RE = re.compile(
    r"^(?P<dir>uf|ub|df|db|u|d|f|b)?\+?(?P<buttons>[1234](?:\+[1234])*)?$"
)

_MOVE_SEPARATOR_RE = re.compile(r"⏵|➜|→|->")


def parse_step(raw_token):
    """Parse un seul token (une entree entre deux virgules/fleches).
    Retourne None pour un token vide, sinon un dict :
      {"raw": texte original, "trackable": bool, "inputs": frozenset|None}
    "inputs" est un sous-ensemble de {"UP","DOWN","LEFT","RIGHT","1","2","3","4"}."""
    text = raw_token.strip()
    if not text:
        return None

    match = _CLEAN_TOKEN_RE.match(text)
    if not match or (not match.group("dir") and not match.group("buttons")):
        return {"raw": text, "trackable": False, "inputs": None}

    inputs = set()
    if match.group("dir"):
        inputs |= DIRECTION_TO_INPUTS[match.group("dir")]
    if match.group("buttons"):
        inputs |= set(match.group("buttons").split("+"))
    return {"raw": text, "trackable": True, "inputs": frozenset(inputs)}


def parse_combo_notation(raw_notation):
    """Parse une notation de combo complete (plusieurs coups separes par
    des virgules et/ou des fleches) en une liste d'etapes, dans l'ordre."""
    steps = []
    for move_segment in _MOVE_SEPARATOR_RE.split(raw_notation):
        for token in move_segment.split(","):
            step = parse_step(token)
            if step is not None:
                steps.append(step)
    return steps
