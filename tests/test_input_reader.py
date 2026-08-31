from hitglow.input_reader import resolve_action_buttons, resolve_directions

NO_SOURCE = {"UP": None, "DOWN": None, "LEFT": None, "RIGHT": None}


def test_hat_source_resolves_all_four_directions():
    source = {**NO_SOURCE, "UP": "hat", "DOWN": "hat", "LEFT": "hat", "RIGHT": "hat"}
    result = resolve_directions(
        hat_value=(-1, 1), axis_values=[], button_states=[],
        direction_source=source, axis_mapping=NO_SOURCE,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
    )
    assert result == {"UP": True, "DOWN": False, "LEFT": True, "RIGHT": False}


def test_axis_source_respects_sign_and_deadzone():
    source = {**NO_SOURCE, "LEFT": "axis", "RIGHT": "axis"}
    mapping = {**NO_SOURCE, "LEFT": (0, -1), "RIGHT": (0, 1)}

    pressed_left = resolve_directions(
        hat_value=(0, 0), axis_values=[-0.9], button_states=[],
        direction_source=source, axis_mapping=mapping,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
    )
    assert pressed_left == {"UP": False, "DOWN": False, "LEFT": True, "RIGHT": False}

    below_deadzone = resolve_directions(
        hat_value=(0, 0), axis_values=[-0.2], button_states=[],
        direction_source=source, axis_mapping=mapping,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
    )
    assert below_deadzone == {"UP": False, "DOWN": False, "LEFT": False, "RIGHT": False}


def test_button_source_reads_button_state():
    source = {**NO_SOURCE, "DOWN": "button"}
    button_mapping = {**NO_SOURCE, "DOWN": 3}
    result = resolve_directions(
        hat_value=(0, 0), axis_values=[], button_states=[False, False, False, True],
        direction_source=source, axis_mapping=NO_SOURCE,
        axis_deadzone=0.5, button_direction_mapping=button_mapping,
    )
    assert result["DOWN"] is True


def test_unmapped_direction_is_never_active():
    result = resolve_directions(
        hat_value=(1, 1), axis_values=[0.9, 0.9], button_states=[True, True],
        direction_source=NO_SOURCE, axis_mapping=NO_SOURCE,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
    )
    assert result == {"UP": False, "DOWN": False, "LEFT": False, "RIGHT": False}


def test_resolve_action_buttons_reads_mapped_indices_only():
    action_buttons = {"1": 0, "2": None, "3": 5}
    result = resolve_action_buttons(
        axis_values=[], button_states=[True, False, False, False, False, False], action_buttons=action_buttons,
    )
    assert result == {"1": True, "2": False, "3": False}


def test_resolve_action_buttons_ignores_out_of_range_index():
    action_buttons = {"HEAT": 99}
    result = resolve_action_buttons(axis_values=[], button_states=[True, True], action_buttons=action_buttons)
    assert result == {"HEAT": False}


def test_resolve_action_buttons_defaults_missing_source_to_button():
    # Compatibilite avec un settings.json existant sans cle "action_source".
    action_buttons = {"1": 0}
    result = resolve_action_buttons(axis_values=[], button_states=[True], action_buttons=action_buttons)
    assert result == {"1": True}


def test_resolve_directions_keyboard_source():
    source = {**NO_SOURCE, "LEFT": "keyboard"}
    keyboard_mapping = {**NO_SOURCE, "LEFT": 97}  # pygame.K_a
    pressed = resolve_directions(
        hat_value=(0, 0), axis_values=[], button_states=[],
        direction_source=source, axis_mapping=NO_SOURCE,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
        keyboard_keys={97}, keyboard_mapping=keyboard_mapping,
    )
    assert pressed["LEFT"] is True

    released = resolve_directions(
        hat_value=(0, 0), axis_values=[], button_states=[],
        direction_source=source, axis_mapping=NO_SOURCE,
        axis_deadzone=0.5, button_direction_mapping=NO_SOURCE,
        keyboard_keys=set(), keyboard_mapping=keyboard_mapping,
    )
    assert released["LEFT"] is False


def test_resolve_action_buttons_keyboard_source():
    action_buttons = {"HEAT": None}
    action_source = {"HEAT": "keyboard"}
    action_keyboard_mapping = {"HEAT": 104}  # pygame.K_h
    result = resolve_action_buttons(
        axis_values=[], button_states=[], action_buttons=action_buttons,
        action_source=action_source, keyboard_keys={104}, action_keyboard_mapping=action_keyboard_mapping,
    )
    assert result == {"HEAT": True}


def test_resolve_action_buttons_reads_analog_trigger_via_axis():
    # Cas RT/LT (gachette) : source "axis", au repos a -1.0, presse pres de +1.0.
    action_buttons = {"RAGE": None}
    action_source = {"RAGE": "axis"}
    action_axis_mapping = {"RAGE": (5, 1)}

    released = resolve_action_buttons(
        axis_values=[0, 0, 0, 0, 0, -1.0], button_states=[], action_buttons=action_buttons,
        action_source=action_source, action_axis_mapping=action_axis_mapping, axis_deadzone=0.5,
    )
    assert released == {"RAGE": False}

    pressed = resolve_action_buttons(
        axis_values=[0, 0, 0, 0, 0, 0.9], button_states=[], action_buttons=action_buttons,
        action_source=action_source, action_axis_mapping=action_axis_mapping, axis_deadzone=0.5,
    )
    assert pressed == {"RAGE": True}
