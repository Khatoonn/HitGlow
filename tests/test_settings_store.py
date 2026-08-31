import json

import copy

from hitglow.settings_store import (
    DEFAULT_SETTINGS,
    apply_detection,
    detect_new_input,
    load_settings,
    resolve_joystick_index,
    save_settings,
)


def test_load_settings_returns_defaults_when_file_missing(tmp_path):
    settings = load_settings(tmp_path / "does_not_exist.json")
    assert settings == DEFAULT_SETTINGS
    assert settings is not DEFAULT_SETTINGS  # deep copy, pas de reference partagee


def test_save_then_load_roundtrips(tmp_path):
    path = tmp_path / "settings.json"
    settings = load_settings(path)
    settings["fade_ms"] = 300
    settings["action_buttons"]["1"] = 4
    save_settings(settings, path)

    reloaded = load_settings(path)
    assert reloaded["fade_ms"] == 300
    assert reloaded["action_buttons"]["1"] == 4


def test_load_settings_merges_missing_keys_from_an_old_file(tmp_path):
    path = tmp_path / "settings.json"
    path.write_text(json.dumps({"fade_ms": 200}), encoding="utf-8")

    settings = load_settings(path)
    assert settings["fade_ms"] == 200
    assert settings["colors"] == DEFAULT_SETTINGS["colors"]


def test_resolve_joystick_index_prefers_saved_name():
    names = ["Xbox Controller", "Haute42"]
    assert resolve_joystick_index(names, "Haute42", 0) == 1


def test_resolve_joystick_index_falls_back_to_saved_index():
    names = ["Xbox Controller", "Haute42"]
    assert resolve_joystick_index(names, "Manette inconnue", 1) == 1


def test_resolve_joystick_index_defaults_to_zero_when_nothing_matches():
    names = ["Haute42"]
    assert resolve_joystick_index(names, None, None) == 0


def test_resolve_joystick_index_returns_none_when_no_joystick():
    assert resolve_joystick_index([], "Haute42", 0) is None


def test_detect_new_input_from_hat_change():
    baseline = {"hat": (0, 0), "axes": [], "buttons": []}
    current = {"hat": (-1, 0), "axes": [], "buttons": []}
    assert detect_new_input(baseline, current) == ("hat", (-1, 0))


def test_detect_new_input_from_axis_change():
    baseline = {"hat": (0, 0), "axes": [0.0, 0.0], "buttons": []}
    current = {"hat": (0, 0), "axes": [0.0, -0.9], "buttons": []}
    assert detect_new_input(baseline, current) == ("axis", (1, -1))


def test_detect_new_input_from_button_press():
    baseline = {"hat": (0, 0), "axes": [], "buttons": [False, False, True]}
    current = {"hat": (0, 0), "axes": [], "buttons": [False, True, True]}
    assert detect_new_input(baseline, current) == ("button", 1)


def test_detect_new_input_returns_none_when_nothing_changed():
    state = {"hat": (0, 0), "axes": [0.1], "buttons": [False]}
    assert detect_new_input(state, state) is None


def test_detect_new_input_ignores_small_axis_jitter():
    baseline = {"hat": (0, 0), "axes": [0.02], "buttons": []}
    current = {"hat": (0, 0), "axes": [0.06], "buttons": []}
    assert detect_new_input(baseline, current) is None


def test_apply_detection_hat_to_direction():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    apply_detection(settings, "LEFT", True, ("hat", (-1, 0)))
    assert settings["direction_source"]["LEFT"] == "hat"


def test_apply_detection_axis_to_direction():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    apply_detection(settings, "UP", True, ("axis", (1, -1)))
    assert settings["direction_source"]["UP"] == "axis"
    assert settings["axis_mapping"]["UP"] == [1, -1]


def test_apply_detection_button_to_direction():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    apply_detection(settings, "DOWN", True, ("button", 7))
    assert settings["direction_source"]["DOWN"] == "button"
    assert settings["button_direction_mapping"]["DOWN"] == 7


def test_apply_detection_button_to_action():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    apply_detection(settings, "HEAT", False, ("button", 4))
    assert settings["action_source"]["HEAT"] == "button"
    assert settings["action_buttons"]["HEAT"] == 4


def test_apply_detection_axis_to_action():
    # Cas gachette (RT/LT) pour une action comme Rage Art.
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    apply_detection(settings, "RAGE", False, ("axis", (5, 1)))
    assert settings["action_source"]["RAGE"] == "axis"
    assert settings["action_axis_mapping"]["RAGE"] == [5, 1]


def test_apply_detection_ignores_hat_for_action_buttons():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    apply_detection(settings, "RAGE", False, ("hat", (1, 0)))
    assert settings["action_buttons"]["RAGE"] is None
    assert settings["action_source"]["RAGE"] is None
