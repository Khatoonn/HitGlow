"""Fenetre overlay HitGlow : transparence Win32 (layered window) et rendu.

Contrainte importante : tout ce qui est dessine sur la surface doit avoir
une alpha de 0 (invisible) ou 255 (opaque) — jamais une valeur intermediaire.
La fenetre layered saute volontairement l'etape de premultiplication de
l'alpha (voir LayeredWindow.update) pour rester performante sans dependance
a numpy ; ca ne fonctionne que si l'alpha est toujours binaire. Le "fondu"
des boutons est donc un fondu de COULEUR (RGB) vers COLOR_OFF, jamais un
fondu d'alpha.
"""

import pygame


def lerp_color(color_from, color_to, t):
    """Interpole lineairement entre deux couleurs RGB. t est clampe a [0, 1]."""
    t = max(0.0, min(1.0, t))
    return tuple(
        round(a + (b - a) * t)
        for a, b in zip(color_from, color_to)
    )


class ButtonGlow:
    """Suit la couleur d'affichage courante d'un bouton : couleur active
    tant qu'il est presse, puis fondu vers off_color sur fade_ms apres
    relachement."""

    def __init__(self, off_color, fade_ms):
        self.off_color = off_color
        self.fade_ms = fade_ms
        self._active_color = None
        self._last_pressed_ms = None

    def update(self, is_pressed, active_color, now_ms):
        if is_pressed:
            self._active_color = active_color
            self._last_pressed_ms = now_ms
            return active_color

        if self._active_color is None:
            return self.off_color

        elapsed = now_ms - self._last_pressed_ms
        if elapsed >= self.fade_ms:
            self._active_color = None
            return self.off_color

        t = elapsed / self.fade_ms
        return lerp_color(self._active_color, self.off_color, t)


def render_frame(
    width, height, glow_colors, direction_layout, action_layout,
    circle_radius, label_color, scale=1.0, calibration_lines=None,
):
    """Construit la frame a afficher : fond transparent + ronds colores
    (+ labels texte pour les boutons d'action) + overlay de calibration
    optionnel. Retourne une pygame.Surface avec canal alpha."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))

    for name, (x, y) in direction_layout.items():
        color = glow_colors[name]
        pygame.draw.circle(surface, color, (round(x * scale), round(y * scale)), round(circle_radius * scale))

    if action_layout:
        font = pygame.font.SysFont(None, max(1, round(20 * scale)))
        for name, (x, y) in action_layout.items():
            color = glow_colors[name]
            cx, cy = round(x * scale), round(y * scale)
            radius = round(circle_radius * scale)
            pygame.draw.circle(surface, color, (cx, cy), radius)
            label = font.render(name, False, label_color).convert_alpha()
            surface.blit(label, label.get_rect(center=(cx, cy)))

    if calibration_lines:
        _draw_calibration_overlay(surface, calibration_lines)

    return surface


def _draw_calibration_overlay(surface, lines):
    """Dessine le panneau de calibration : fond opaque uni (jamais
    translucide, pour respecter la contrainte alpha binaire) + texte."""
    font = pygame.font.SysFont(None, 22)
    line_height = 24
    panel_height = 12 + line_height * len(lines)
    panel_width = 360
    panel = pygame.Surface((panel_width, panel_height), pygame.SRCALPHA)
    panel.fill((10, 10, 10, 255))
    for i, line in enumerate(lines):
        text = font.render(line, False, (255, 255, 255)).convert_alpha()
        panel.blit(text, (8, 8 + i * line_height))
    surface.blit(panel, (0, 0))
