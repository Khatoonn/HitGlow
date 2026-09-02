from hitglow.combo_parser import parse_combo_notation, parse_step


def test_parse_step_plain_direction():
    step = parse_step("f")
    assert step == {"raw": "f", "trackable": True, "inputs": frozenset({"RIGHT"})}


def test_parse_step_direction_plus_button():
    step = parse_step("f+2")
    assert step["trackable"] is True
    assert step["inputs"] == frozenset({"RIGHT", "2"})


def test_parse_step_diagonal_direction():
    step = parse_step("df+1")
    assert step["inputs"] == frozenset({"DOWN", "RIGHT", "1"})


def test_parse_step_multiple_buttons():
    step = parse_step("d+1+2")
    assert step["inputs"] == frozenset({"DOWN", "1", "2"})


def test_parse_step_plain_button():
    step = parse_step("3")
    assert step == {"raw": "3", "trackable": True, "inputs": frozenset({"3"})}


def test_parse_step_stance_name_is_not_trackable():
    step = parse_step("LNH")
    assert step["trackable"] is False
    assert step["raw"] == "LNH"
    assert step["inputs"] is None


def test_parse_step_stance_name_with_button_is_not_trackable():
    # "LNH 2" contient un espace + des majuscules -> jamais mappe a un input.
    step = parse_step("LNH 2")
    assert step["trackable"] is False


def test_parse_step_bracket_annotation_is_not_trackable():
    step = parse_step("[ 2~1 ]")
    assert step["trackable"] is False
    assert step["raw"] == "[ 2~1 ]"


def test_parse_step_tornado_annotation_is_not_trackable():
    step = parse_step("1+2 T!")
    assert step["trackable"] is False


def test_parse_step_while_standing_condition_is_not_trackable():
    step = parse_step("ws+1,2")
    assert step["trackable"] is False


def test_parse_step_heat_dash_prefix_is_not_trackable():
    step = parse_step("heat dash f+2")
    assert step["trackable"] is False


def test_parse_step_empty_token_returns_none():
    assert parse_step("") is None
    assert parse_step("   ") is None


def test_parse_combo_notation_splits_on_comma():
    steps = parse_combo_notation("3,1,2")
    assert [s["raw"] for s in steps] == ["3", "1", "2"]
    assert all(s["trackable"] for s in steps)


def test_parse_combo_notation_splits_on_arrow():
    steps = parse_combo_notation("f+2 ⏵ df+1")
    assert [s["raw"] for s in steps] == ["f+2", "df+1"]


def test_parse_combo_notation_steve_real_example():
    # Ligne reelle de la feuille Steve ("MOST IMPORTANT COMBOS", uf+2).
    notation = "f+3,1 ⏵ df+1,[ 2~1 ] ⏵ f+2,2 ⏵ LNH 2 T! ⏵ 3,1,2 ⏵ LNH 2"
    steps = parse_combo_notation(notation)
    raws = [s["raw"] for s in steps]
    assert raws == ["f+3", "1", "df+1", "[ 2~1 ]", "f+2", "2", "LNH 2 T!", "3", "1", "2", "LNH 2"]
    trackable_raws = [s["raw"] for s in steps if s["trackable"]]
    assert trackable_raws == ["f+3", "1", "df+1", "f+2", "2", "3", "1", "2"]
    assert steps[0]["inputs"] == frozenset({"RIGHT", "3"})
    assert steps[4]["inputs"] == frozenset({"RIGHT", "2"})
