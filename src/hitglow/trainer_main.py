"""Boucle du combo trainer HitGlow (mode --trainer --combo <id>) : fenetre
separee qui affiche un combo choisi et suit la progression en direct via
les inputs reels (manette et/ou clavier, meme mapping que l'overlay
principal). Lance depuis la fenetre de parametrage (onglet Combos) en
sous-processus, independamment de l'overlay d'affichage des inputs."""

import os
import sys

import pygame

from hitglow import combo_store, settings_store
from hitglow.combo_parser import parse_combo_notation
from hitglow.combo_render import combo_bar_size, render_combo_bar
from hitglow.combo_tracker import ComboTracker
from hitglow.input_reader import JoystickReader, poll_keyboard, resolve_action_buttons, resolve_directions
from hitglow.overlay_window import OverlayWindow, get_cursor_pos

FPS = 60
CIRCLE_RADIUS = 26
QUIT_KEY = pygame.K_ESCAPE
RESET_KEY = pygame.K_r
MANUAL_ADVANCE_KEY = pygame.K_SPACE


def _list_joystick_names():
    pygame.joystick.init()
    return [pygame.joystick.Joystick(i).get_name() for i in range(pygame.joystick.get_count())]


def run(combo_id):
    os.environ.setdefault("SDL_JOYSTICK_ALLOW_BACKGROUND_EVENTS", "1")
    pygame.init()

    combos = combo_store.load_combos()
    combo = next((c for c in combos if c["id"] == combo_id), None)
    if combo is None:
        print(f"Combo introuvable (id={combo_id}).", file=sys.stderr)
        pygame.quit()
        sys.exit(1)

    steps = parse_combo_notation(combo["notation"])
    tracker = ComboTracker(steps)

    settings = settings_store.load_settings()
    available_names = _list_joystick_names()
    index = settings_store.resolve_joystick_index(
        available_names, settings["joystick_name"], settings["joystick_index"],
    )
    joystick = JoystickReader(index) if index is not None else None

    width, height = combo_bar_size(len(steps), CIRCLE_RADIUS)
    window = OverlayWindow(
        width, height, settings["transparent_background"], tuple(settings["chroma_fallback_color"]),
    )
    pygame.display.set_caption(f"HitGlow Trainer - {combo['character']} - {combo['name']}")

    running = True
    dragging = False
    clock = pygame.time.Clock()

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == QUIT_KEY:
                    running = False
                elif event.key == RESET_KEY:
                    tracker.reset()
                elif event.key == MANUAL_ADVANCE_KEY:
                    tracker.advance_manual()
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                dragging = True
                window.start_drag(get_cursor_pos())
            elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                dragging = False
                window.end_drag()
            elif event.type == pygame.MOUSEMOTION and dragging:
                window.drag_to(get_cursor_pos())

        if joystick is not None:
            hat, axes, buttons = joystick.poll(settings["hat_index"])
        else:
            hat, axes, buttons = (0, 0), [], []
        keyboard_keys = poll_keyboard()

        directions = resolve_directions(
            hat, axes, buttons,
            settings["direction_source"], settings["axis_mapping"], settings["axis_deadzone"],
            settings["button_direction_mapping"], keyboard_keys, settings["keyboard_mapping"],
        )
        actions = resolve_action_buttons(
            axes, buttons, settings["action_buttons"],
            settings["action_source"], settings["action_axis_mapping"], settings["axis_deadzone"],
            keyboard_keys, settings["action_keyboard_mapping"],
        )
        pressed_names = {name for name, is_down in {**directions, **actions}.items() if is_down}

        tracker.update(pressed_names)
        if tracker.is_complete():
            tracker.reset()  # boucle pour un entrainement repete, sans avoir a relancer

        frame = render_combo_bar(steps, tracker.index, CIRCLE_RADIUS)
        window.present(frame)
        clock.tick(FPS)

    window.close()
    pygame.quit()
