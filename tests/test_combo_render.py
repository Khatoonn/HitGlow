import pygame

from hitglow.combo_parser import parse_combo_notation
from hitglow.combo_render import DEFAULT_COLORS, combo_bar_size, render_combo_bar

pygame.font.init()


def test_render_combo_bar_empty_steps_returns_small_surface():
    surface = render_combo_bar([], current_index=0, circle_radius=20)
    assert surface.get_size()[0] > 0
    assert surface.get_size()[1] > 0


def test_render_combo_bar_matches_computed_size():
    steps = parse_combo_notation("f+2,3,1")
    width, height = combo_bar_size(len(steps), circle_radius=20)
    surface = render_combo_bar(steps, current_index=0, circle_radius=20)
    assert surface.get_size() == (width, height)


def test_render_combo_bar_current_step_uses_current_color():
    steps = parse_combo_notation("f+2,3")
    surface = render_combo_bar(steps, current_index=0, circle_radius=20)
    cx = 20 + 10
    cy = surface.get_height() // 2
    # Echantillonne pres du bord du rond (pas le centre exact, recouvert
    # par le texte du label) pour lire la couleur de fond du rond.
    assert surface.get_at((cx - 15, cy))[:3] == DEFAULT_COLORS["current"]


def test_render_combo_bar_done_step_uses_done_color():
    steps = parse_combo_notation("f+2,3")
    surface = render_combo_bar(steps, current_index=1, circle_radius=20)
    cx = 20 + 10
    cy = surface.get_height() // 2
    assert surface.get_at((cx - 15, cy))[:3] == DEFAULT_COLORS["done"]


def test_render_combo_bar_manual_step_uses_manual_color():
    # "LNH 2" est le 2e pas (index 1), pas encore atteint (current_index=0)
    # et non trackable -> doit s'afficher en couleur "manual".
    steps = parse_combo_notation("3,LNH 2")
    surface = render_combo_bar(steps, current_index=0, circle_radius=20)
    spacing = round(20 * 2 + 14)
    cx = 20 + 10 + spacing  # 2e rond
    cy = surface.get_height() // 2
    assert surface.get_at((cx - 12, cy))[:3] == DEFAULT_COLORS["manual"]
