"""Boucle principale HitGlow : lit la manette, met a jour les couleurs des
ronds, affiche la fenetre overlay."""

import sys

import pygame

from hitglow import config
from hitglow.calibration import format_calibration_lines
from hitglow.input_reader import JoystickReader, resolve_action_buttons, resolve_directions
from hitglow.overlay_window import ButtonGlow, OverlayWindow, get_cursor_pos, render_frame

FPS = 60


def _row_color(name):
    if name in config.ACTION_ROW_TOP:
        return config.COLOR_ROW_TOP
    return config.COLOR_ROW_BOTTOM


def run():
    pygame.init()

    try:
        joystick = JoystickReader(config.JOYSTICK_INDEX)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        pygame.quit()
        sys.exit(1)

    window = OverlayWindow(config)
    clock = pygame.time.Clock()

    glows = {name: ButtonGlow(config.COLOR_DIRECTION, config.FADE_MS) for name in config.DIRECTION_LAYOUT}
    active_colors = {name: config.COLOR_DIRECTION for name in config.DIRECTION_LAYOUT}
    for name in config.ACTION_LAYOUT:
        glows[name] = ButtonGlow(config.COLOR_OFF, config.FADE_MS)
        active_colors[name] = _row_color(name)

    scale = config.INITIAL_SCALE
    calibration_mode = False
    dragging = False
    running = True

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == config.QUIT_KEY:
                    running = False
                elif event.key == config.CALIBRATION_KEY:
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
                scale += event.y * config.SCALE_STEP
                scale = max(config.MIN_SCALE, min(config.MAX_SCALE, scale))

        hat, axes, buttons = joystick.poll(config.HAT_INDEX)
        directions = resolve_directions(
            hat, axes, buttons,
            config.DIRECTION_SOURCE, config.AXIS_MAPPING, config.AXIS_DEADZONE,
            config.BUTTON_DIRECTION_MAPPING,
        )
        actions = resolve_action_buttons(buttons, config.ACTION_BUTTONS)
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
            config.WINDOW_WIDTH, config.WINDOW_HEIGHT, glow_colors,
            config.DIRECTION_LAYOUT, config.ACTION_LAYOUT, config.CIRCLE_RADIUS,
            config.COLOR_LABEL_TEXT, scale=scale, calibration_lines=calibration_lines,
        )
        window.present(frame)
        clock.tick(FPS)

    window.close()
    pygame.quit()
