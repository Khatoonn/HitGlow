import pygame
import pytest

from hitglow.overlay_window import ButtonGlow, lerp_color, render_frame

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
