"""Boucle de l'overlay HitGlow (mode --overlay) : charge settings.json,
lit la manette selectionnee, affiche la fenetre transparente. Lance depuis
la fenetre de parametrage (settings_app.py) en sous-processus."""

import os
import sys

import pygame

from hitglow import layout, settings_store
from hitglow.calibration import format_calibration_lines
from hitglow.input_reader import JoystickReader, poll_keyboard, resolve_action_buttons, resolve_directions
from hitglow.overlay_window import OverlayWindow, build_glows, get_cursor_pos, render_frame

FPS = 60
SCALE_STEP = 0.05
MIN_SCALE = 0.5
MAX_SCALE = 2.5
QUIT_KEY = pygame.K_ESCAPE
CALIBRATION_KEY = pygame.K_c


def _list_joystick_names():
    pygame.joystick.init()
    return [pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())]


def run():
    # SDL n'envoie les evenements manette que si la fenetre a le focus,
    # sauf avec ce hint. Indispensable ici : le jeu (Tekken 8) ou OBS ont
    # le focus pendant le stream, pas la fenetre HitGlow.
    os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
    pygame.init()
    settings = settings_store.load_settings()

    available_names = _list_joystick_names()
    index = settings_store.resolve_joystick_index(
        available_names, settings["joystick_name"], settings["joystick_index"],
    )
    joystick = None
    if index is not None:
        joystick = JoystickReader(index)
        settings["joystick_name"] = available_names[index]
        settings["joystick_index"] = index
        settings_store.save_settings(settings)
    else:
        print(
            "Aucune manette detectee — seuls les inputs mappes au clavier fonctionneront.",
            file=sys.stderr,
        )

    window = OverlayWindow(
        settings["window_width"], settings["window_height"],
        settings["transparent_background"], tuple(settings["chroma_fallback_color"]),
    )
    if settings["window_pos"] is not None:
        window.move_to(tuple(settings["window_pos"]))

    colors = settings["colors"]
    off_color = tuple(colors["off"])
    direction_color = tuple(colors["direction"])
    row_top_color = tuple(colors["row_top"])
    row_bottom_color = tuple(colors["row_bottom"])
    label_color = tuple(colors["label_text"])
    fade_ms = settings["fade_ms"]

    def _row_color(name):
        return row_top_color if name in layout.ACTION_ROW_TOP else row_bottom_color

    glows = build_glows(off_color, fade_ms, layout.DIRECTION_LAYOUT, layout.ACTION_LAYOUT)
    active_colors = {name: direction_color for name in layout.DIRECTION_LAYOUT}
    for name in layout.ACTION_LAYOUT:
        active_colors[name] = _row_color(name)

    scale = settings["scale"]
    calibration_mode = False
    dragging = False
    running = True
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == QUIT_KEY:
                    running = False
                elif event.key == CALIBRATION_KEY:
                    calibration_mode = not calibration_mode
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging = True
                window.start_drag(get_cursor_pos())
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
                window.end_drag()
            elif event.type == pygame.MOUSEMOTION and dragging:
                window.drag_to(get_cursor_pos())
            elif event.type == pygame.MOUSEWHEEL:
                scale += event.y * SCALE_STEP
                scale = max(MIN_SCALE, min(MAX_SCALE, scale))

        if joystick is not None:
            hat, axes, buttons = joystick.poll(settings["hat_index"])
        else:
            hat, axes, buttons = (0, 0), [], []
        keyboard_keys = poll_keyboard()

        directions = resolve_directions(
            hat, axes, buttons,
            settings["direction_source"], settings["axis_mapping"], settings["axis_deadzone"],
            settings["button_direction_mapping"],
            keyboard_keys, settings["keyboard_mapping"],
        )
        actions = resolve_action_buttons(
            axes, buttons, settings["action_buttons"],
            settings["action_source"], settings["action_axis_mapping"], settings["axis_deadzone"],
            keyboard_keys, settings["action_keyboard_mapping"],
        )
        pressed = {**directions, **actions}

        now_ms = pygame.time.get_ticks()
        glow_colors = {
            name: glows[name].update(pressed[name], active_colors[name], now_ms)
            for name in glows
        }

        calibration_lines = None
        if calibration_mode:
            calibration_lines = format_calibration_lines(hat, axes, [i for i, pressed_ in enumerate(buttons) if pressed_])

        frame = render_frame(
            settings["window_width"], settings["window_height"], glow_colors,
            layout.DIRECTION_LAYOUT, layout.ACTION_LAYOUT, layout.CIRCLE_RADIUS,
            label_color, labels=settings["labels"], font_spec=settings["font"],
            scale=scale, calibration_lines=calibration_lines,
        )
        window.present(frame)
        clock.tick(FPS)

    settings["window_pos"] = list(window.get_pos())
    settings["scale"] = scale
    settings_store.save_settings(settings)

    window.close()
    pygame.quit()
