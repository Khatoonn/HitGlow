"""Lecture des inputs manette : fonctions pures de resolution du mapping,
et polling brut via pygame.joystick."""

import pygame


def resolve_directions(
    hat_value, axis_values, button_states,
    direction_source, axis_mapping, axis_deadzone, button_direction_mapping,
    keyboard_keys=None, keyboard_mapping=None,
):
    """Calcule l'etat presse/relache des 4 directions logiques a partir
    des valeurs brutes de la manette (et/ou du clavier), selon la source
    configuree pour chaque direction."""
    keyboard_keys = keyboard_keys or set()
    keyboard_mapping = keyboard_mapping or {}
    result = {}
    for name in ("UP", "DOWN", "LEFT", "RIGHT"):
        source = direction_source.get(name)
        if source == "hat":
            x, y = hat_value
            if name == "LEFT":
                result[name] = x < 0
            elif name == "RIGHT":
                result[name] = x > 0
            elif name == "UP":
                result[name] = y > 0
            else:  # DOWN
                result[name] = y < 0
        elif source == "axis":
            mapping = axis_mapping.get(name)
            if mapping is None:
                result[name] = False
            else:
                axis_index, sign = mapping
                value = axis_values[axis_index] if axis_index < len(axis_values) else 0.0
                result[name] = (value * sign) > axis_deadzone
        elif source == "button":
            index = button_direction_mapping.get(name)
            result[name] = bool(button_states[index]) if index is not None and index < len(button_states) else False
        elif source == "keyboard":
            key_code = keyboard_mapping.get(name)
            result[name] = key_code is not None and key_code in keyboard_keys
        else:
            result[name] = False
    return result


def resolve_action_buttons(
    axis_values, button_states, action_buttons,
    action_source=None, action_axis_mapping=None, axis_deadzone=0.5,
    keyboard_keys=None, action_keyboard_mapping=None,
):
    """Calcule l'etat presse/relache de chaque bouton d'action nomme.

    Chaque action peut venir d'un bouton digital (par defaut, y compris
    quand action_source ne precise rien pour rester compatible avec les
    anciens settings.json), d'un axe analogique — indispensable pour les
    gachettes (LT/RT) souvent utilisees pour des actions comme Rage Art,
    qui ne remontent jamais comme un bouton digital classique — ou d'une
    touche clavier."""
    action_source = action_source or {}
    action_axis_mapping = action_axis_mapping or {}
    keyboard_keys = keyboard_keys or set()
    action_keyboard_mapping = action_keyboard_mapping or {}
    result = {}
    for name, index in action_buttons.items():
        source = action_source.get(name) or "button"
        if source == "axis":
            mapping = action_axis_mapping.get(name)
            if mapping is None:
                result[name] = False
            else:
                axis_index, sign = mapping
                value = axis_values[axis_index] if axis_index < len(axis_values) else 0.0
                result[name] = (value * sign) > axis_deadzone
        elif source == "keyboard":
            key_code = action_keyboard_mapping.get(name)
            result[name] = key_code is not None and key_code in keyboard_keys
        else:
            result[name] = bool(button_states[index]) if index is not None and index < len(button_states) else False
    return result


def poll_keyboard():
    """Retourne l'ensemble des codes de touches (pygame.K_*) actuellement
    enfoncees."""
    pygame.event.pump()
    return {code for code, is_down in enumerate(pygame.key.get_pressed()) if is_down}


class JoystickReader:
    """Encapsule un pygame.joystick.Joystick et expose son etat brut."""

    def __init__(self, joystick_index):
        pygame.joystick.init()
        if pygame.joystick.get_count() <= joystick_index:
            raise RuntimeError(
                f"Aucune manette detectee a l'index {joystick_index}. "
                "Verifie qu'elle est branchee et reconnue par Windows."
            )
        self.joystick = pygame.joystick.Joystick(joystick_index)
        self.joystick.init()

    def poll(self, hat_index=0):
        """Retourne (hat, axes, buttons) : l'etat brut actuel de la manette."""
        pygame.event.pump()
        hat = self.joystick.get_hat(hat_index) if self.joystick.get_numhats() > hat_index else (0, 0)
        axes = [self.joystick.get_axis(i) for i in range(self.joystick.get_numaxes())]
        buttons = [bool(self.joystick.get_button(i)) for i in range(self.joystick.get_numbuttons())]
        return hat, axes, buttons
