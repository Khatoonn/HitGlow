import copy

from hitglow.settings_app import _hex, _hex_to_rgb, _mapping_status_text
from hitglow.settings_store import DEFAULT_SETTINGS


def test_status_text_unmapped_direction():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    assert _mapping_status_text(settings, "LEFT", True) == "Non mappe"


def test_status_text_hat_direction():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    settings["direction_source"]["LEFT"] = "hat"
    assert _mapping_status_text(settings, "LEFT", True) == "Hat"


def test_status_text_axis_direction():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    settings["direction_source"]["UP"] = "axis"
    settings["axis_mapping"]["UP"] = [1, -1]
    assert _mapping_status_text(settings, "UP", True) == "Axe 1 (-)"


def test_status_text_button_direction():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    settings["direction_source"]["DOWN"] = "button"
    settings["button_direction_mapping"]["DOWN"] = 5
    assert _mapping_status_text(settings, "DOWN", True) == "Bouton 5"


def test_status_text_unmapped_action():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    assert _mapping_status_text(settings, "HEAT", False) == "Non mappe"


def test_status_text_mapped_action():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    settings["action_buttons"]["HEAT"] = 4
    assert _mapping_status_text(settings, "HEAT", False) == "Bouton 4"


def test_status_text_action_mapped_via_axis():
    # Cas gachette (RT/LT), ex: Rage Art.
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    settings["action_source"]["RAGE"] = "axis"
    settings["action_axis_mapping"]["RAGE"] = [5, 1]
    assert _mapping_status_text(settings, "RAGE", False) == "Axe 5 (+)"


def test_status_text_direction_mapped_via_keyboard():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    settings["direction_source"]["LEFT"] = "keyboard"
    settings["keyboard_mapping"]["LEFT"] = 0x41  # VK_A
    assert _mapping_status_text(settings, "LEFT", True) == "Touche A"


def test_status_text_action_mapped_via_keyboard():
    settings = copy.deepcopy(DEFAULT_SETTINGS)
    settings["action_source"]["HEAT"] = "keyboard"
    settings["action_keyboard_mapping"]["HEAT"] = 0x48  # VK_H
    assert _mapping_status_text(settings, "HEAT", False) == "Touche H"


def test_hex_roundtrip():
    assert _hex([255, 0, 128]) == "#ff0080"
    assert _hex_to_rgb("#ff0080") == [255, 0, 128]
