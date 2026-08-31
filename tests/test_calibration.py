from hitglow.calibration import format_calibration_lines


def test_shows_hat_value():
    lines = format_calibration_lines((1, -1), [], [])
    assert lines[0] == "HAT: (1, -1)"


def test_shows_each_axis_with_two_decimals():
    lines = format_calibration_lines((0, 0), [0.5, -0.333], [])
    assert "AXIS 0: +0.50" in lines
    assert "AXIS 1: -0.33" in lines


def test_shows_pressed_buttons_sorted():
    lines = format_calibration_lines((0, 0), [], [5, 1, 3])
    assert lines[-1] == "BOUTONS: [1, 3, 5]"


def test_shows_placeholder_when_no_button_pressed():
    lines = format_calibration_lines((0, 0), [], [])
    assert lines[-1] == "BOUTONS: (aucun)"
