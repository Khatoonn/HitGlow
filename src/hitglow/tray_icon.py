"""Icone de la zone de notification (system tray) pour l'overlay HitGlow.

L'overlay est une fenetre sans bordure et toujours au-dessus : sans titre,
elle n'a pas de bouton "reduire" natif. L'icone systray comble ce manque
(pattern Windows classique pour ce genre de fenetre) : clic gauche ou entree
de menu "Afficher/Masquer" pour la basculer sans fermer le processus (le
mapping et l'etat restent charges), "Quitter" pour fermer proprement.
"""

import pystray
from PIL import Image, ImageDraw


def _build_icon_image():
    size = 64
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.ellipse((4, 4, size - 4, size - 4), fill=(0, 255, 255, 255), outline=(20, 20, 20, 255), width=4)
    return img


def create_tray_icon(on_toggle, on_quit):
    """Cree (sans le demarrer) l'icone systray. on_toggle/on_quit sont
    appeles depuis le thread interne de pystray, jamais le thread principal
    pygame — a l'appelant de les rendre thread-safe (ex: une Queue)."""
    image = _build_icon_image()
    menu = pystray.Menu(
        pystray.MenuItem("Afficher/Masquer", lambda icon, item: on_toggle(), default=True),
        pystray.MenuItem("Quitter", lambda icon, item: on_quit()),
    )
    return pystray.Icon("HitGlow", image, "HitGlow", menu)
