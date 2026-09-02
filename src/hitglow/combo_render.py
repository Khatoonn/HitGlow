"""Rendu de la barre de combo du trainer : une rangee de ronds (meme style
glossy que l'overlay principal) representant chaque etape, façon barre de
notation Tekken 8. Couleur par etat : deja validee, en cours, a venir, ou
"a valider soi-meme" (etape non trackable)."""

import pygame

from hitglow.overlay_window import _build_font, _draw_glossy_circle

STATE_DONE = "done"
STATE_CURRENT = "current"
STATE_UPCOMING = "upcoming"
STATE_MANUAL = "manual"

DEFAULT_COLORS = {
    STATE_DONE: (70, 170, 90),
    STATE_CURRENT: (255, 220, 0),
    STATE_UPCOMING: (55, 55, 62),
    STATE_MANUAL: (230, 140, 40),
    "label_text": (255, 255, 255),
}


def _step_state(index, current_index, step):
    if index < current_index:
        return STATE_DONE
    if index == current_index:
        return STATE_CURRENT
    if not step["trackable"]:
        return STATE_MANUAL
    return STATE_UPCOMING


def combo_bar_size(step_count, circle_radius, scale=1.0):
    """Taille (largeur, hauteur) necessaire pour afficher step_count ronds,
    avec une marge raisonnable de chaque cote."""
    radius = round(circle_radius * scale)
    spacing = round((circle_radius * 2 + 14) * scale)
    width = max(1, step_count) * spacing + radius * 2
    height = radius * 2 + round(40 * scale)
    return width, height


def render_combo_bar(steps, current_index, circle_radius, colors=None, font_spec=None, scale=1.0):
    """Construit la frame de la barre de combo. Retourne une pygame.Surface
    avec canal alpha (fond transparent, comme le reste de l'overlay)."""
    colors = colors or DEFAULT_COLORS
    radius = round(circle_radius * scale)
    spacing = round((circle_radius * 2 + 14) * scale)
    width, height = combo_bar_size(len(steps), circle_radius, scale)
    cy = height // 2

    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    if not steps:
        return surface

    for i, step in enumerate(steps):
        cx = radius + 10 + i * spacing
        state = _step_state(i, current_index, step)
        color = colors[state]
        _draw_glossy_circle(surface, (cx, cy), radius, color)

        label = step["raw"]
        font_size = max(1, round((16 if len(label) <= 4 else 11) * scale))
        font = _build_font(font_spec, font_size)
        text = font.render(label, False, colors["label_text"])
        if pygame.display.get_init() and pygame.display.get_surface() is not None:
            text = text.convert_alpha()
        surface.blit(text, text.get_rect(center=(cx, cy)))

    return surface
