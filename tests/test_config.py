from hitglow import config

DIRECTIONS = {"UP", "DOWN", "LEFT", "RIGHT"}
ACTION_NAMES = {"1", "2", "3", "4", "HEAT", "RAGE"}


def test_direction_sources_default_to_unmapped():
    assert set(config.DIRECTION_SOURCE) == DIRECTIONS
    assert all(v is None for v in config.DIRECTION_SOURCE.values())


def test_action_buttons_have_all_six_names_unmapped():
    assert set(config.ACTION_BUTTONS) == ACTION_NAMES
    assert all(v is None for v in config.ACTION_BUTTONS.values())


def test_action_rows_partition_the_six_names():
    assert config.ACTION_ROW_TOP == {"1", "2", "HEAT"}
    assert config.ACTION_ROW_BOTTOM == {"3", "4", "RAGE"}
    assert config.ACTION_ROW_TOP | config.ACTION_ROW_BOTTOM == ACTION_NAMES
    assert config.ACTION_ROW_TOP & config.ACTION_ROW_BOTTOM == set()


def test_layouts_cover_all_circles():
    assert set(config.DIRECTION_LAYOUT) == DIRECTIONS
    assert set(config.ACTION_LAYOUT) == ACTION_NAMES


def test_colors_are_rgb_tuples():
    for color in (
        config.COLOR_OFF,
        config.COLOR_DIRECTION,
        config.COLOR_ROW_TOP,
        config.COLOR_ROW_BOTTOM,
        config.COLOR_LABEL_TEXT,
        config.CHROMA_FALLBACK_COLOR,
    ):
        assert len(color) == 3
        assert all(0 <= channel <= 255 for channel in color)


def test_fade_and_scale_bounds_are_positive():
    assert config.FADE_MS > 0
    assert config.MIN_SCALE < config.INITIAL_SCALE <= config.MAX_SCALE
