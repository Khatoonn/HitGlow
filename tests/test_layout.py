from hitglow import layout

DIRECTIONS = {"UP", "DOWN", "LEFT", "RIGHT"}
ACTION_NAMES = {"1", "2", "3", "4", "HEAT", "RAGE"}


def test_direction_layout_covers_all_four_directions():
    assert set(layout.DIRECTION_LAYOUT) == DIRECTIONS


def test_action_layout_covers_all_six_buttons():
    assert set(layout.ACTION_LAYOUT) == ACTION_NAMES


def test_action_rows_partition_the_six_names():
    assert layout.ACTION_ROW_TOP == {"1", "2", "HEAT"}
    assert layout.ACTION_ROW_BOTTOM == {"3", "4", "RAGE"}
    assert layout.ACTION_ROW_TOP | layout.ACTION_ROW_BOTTOM == ACTION_NAMES
    assert layout.ACTION_ROW_TOP & layout.ACTION_ROW_BOTTOM == set()


def test_circle_radius_is_positive():
    assert layout.CIRCLE_RADIUS > 0
