import pygame
import pytest

from hitglow.overlay_window import ButtonGlow, build_glows, lerp_color, render_frame

pygame.font.init()


def test_lerp_color_at_start_and_end():
    assert lerp_color((255, 0, 0), (0, 0, 0), 0.0) == (255, 0, 0)
    assert lerp_color((255, 0, 0), (0, 0, 0), 1.0) == (0, 0, 0)


def test_lerp_color_midpoint():
    assert lerp_color((200, 100, 0), (0, 0, 0), 0.5) == (100, 50, 0)


def test_lerp_color_clamps_t_outside_0_1():
    assert lerp_color((10, 10, 10), (0, 0, 0), -1.0) == (10, 10, 10)
    assert lerp_color((10, 10, 10), (0, 0, 0), 2.0) == (0, 0, 0)


def test_button_glow_is_off_color_when_never_pressed():
    glow = ButtonGlow(off_color=(40, 40, 40), fade_ms=150)
    assert glow.update(is_pressed=False, active_color=(0, 255, 255), now_ms=0) == (40, 40, 40)


def test_button_glow_is_active_color_while_pressed():
    glow = ButtonGlow(off_color=(40, 40, 40), fade_ms=150)
    assert glow.update(is_pressed=True, active_color=(0, 255, 255), now_ms=0) == (0, 255, 255)
    assert glow.update(is_pressed=True, active_color=(0, 255, 255), now_ms=500) == (0, 255, 255)


def test_button_glow_fades_after_release():
    glow = ButtonGlow(off_color=(40, 40, 40), fade_ms=100)
    glow.update(is_pressed=True, active_color=(240, 40, 40), now_ms=0)

    mid_fade = glow.update(is_pressed=False, active_color=(240, 40, 40), now_ms=50)
    assert mid_fade == lerp_color((240, 40, 40), (40, 40, 40), 0.5)

    fully_faded = glow.update(is_pressed=False, active_color=(240, 40, 40), now_ms=200)
    assert fully_faded == (40, 40, 40)


def test_render_frame_paints_pressed_circle_at_its_center():
    glow_colors = {"UP": (40, 40, 40), "DOWN": (40, 40, 40), "LEFT": (0, 255, 255), "RIGHT": (40, 40, 40)}
    surface = render_frame(
        width=200, height=200, glow_colors=glow_colors,
        direction_layout={"UP": (50, 150), "DOWN": (50, 150), "LEFT": (100, 100), "RIGHT": (50, 150)},
        action_layout={}, circle_radius=20, label_color=(255, 255, 255),
    )
    assert surface.get_at((100, 100))[:3] == (0, 255, 255)
    assert surface.get_at((100, 100))[3] == 255


def test_render_frame_leaves_background_fully_transparent():
    surface = render_frame(
        width=50, height=50, glow_colors={}, direction_layout={}, action_layout={},
        circle_radius=10, label_color=(255, 255, 255),
    )
    assert surface.get_at((0, 0))[3] == 0


def test_render_frame_draws_a_dark_bezel_at_the_circle_edge():
    color = (0, 255, 255)
    surface = render_frame(
        width=200, height=200, glow_colors={"LEFT": color},
        direction_layout={"LEFT": (100, 100)}, action_layout={},
        circle_radius=30, label_color=(255, 255, 255),
    )
    edge_pixel = surface.get_at((100, 100 - 29))
    assert edge_pixel[:3] != color
    assert edge_pixel[3] == 255
    assert sum(edge_pixel[:3]) < sum(color)


def test_render_frame_draws_a_lighter_highlight_above_center():
    color = (0, 255, 255)
    surface = render_frame(
        width=200, height=200, glow_colors={"LEFT": color},
        direction_layout={"LEFT": (100, 100)}, action_layout={},
        circle_radius=30, label_color=(255, 255, 255),
    )
    highlight_pixel = surface.get_at((100, 100 - 12))
    assert highlight_pixel[:3] != color
    assert highlight_pixel[3] == 255


def test_build_glows_uses_off_color_for_every_input_when_never_pressed():
    # Regression : un ButtonGlow doit toujours demarrer avec off_color comme
    # couleur d'extinction, quel que soit son type (direction ou action) —
    # jamais la couleur active, sinon l'input reste "allume" en permanence
    # meme sans etre presse.
    off_color = (40, 40, 40)
    glows = build_glows(off_color, fade_ms=150, direction_names=["LEFT", "UP"], action_names=["1", "HEAT"])
    assert set(glows) == {"LEFT", "UP", "1", "HEAT"}
    for name, glow in glows.items():
        assert glow.update(is_pressed=False, active_color=(0, 255, 255), now_ms=0) == off_color


def test_render_frame_draws_direction_labels_when_provided():
    without_label = render_frame(
        width=200, height=200, glow_colors={"LEFT": (0, 255, 255)},
        direction_layout={"LEFT": (100, 100)}, action_layout={},
        circle_radius=30, label_color=(255, 255, 255),
    )
    with_label = render_frame(
        width=200, height=200, glow_colors={"LEFT": (0, 255, 255)},
        direction_layout={"LEFT": (100, 100)}, action_layout={},
        circle_radius=30, label_color=(255, 255, 255), labels={"LEFT": "B"},
    )
    assert without_label.get_at((100, 100))[:3] != with_label.get_at((100, 100))[:3]
