from hitglow.combo_store import add_combo, grouped_by_game_and_character, load_combos, remove_combo, save_combos


def test_load_combos_returns_empty_list_when_file_missing(tmp_path):
    assert load_combos(tmp_path / "does_not_exist.json") == []


def test_add_combo_appends_and_returns_it():
    combos = []
    combo = add_combo(combos, "Steve", "uf+2 combo", "f+3,1 ⏵ df+1")
    assert combos == [combo]
    assert combo["character"] == "Steve"
    assert combo["name"] == "uf+2 combo"
    assert combo["notation"] == "f+3,1 ⏵ df+1"
    assert combo["game"] == "Tekken 8"
    assert combo["id"]


def test_add_combo_accepts_custom_game():
    combos = []
    combo = add_combo(combos, "Ryu", "Hadouken combo", "d,df,f+1", game="Street Fighter 6")
    assert combo["game"] == "Street Fighter 6"


def test_add_combo_defaults_game_when_blank():
    combos = []
    combo = add_combo(combos, "Steve", "Combo 1", "f+2", game="   ")
    assert combo["game"] == "Tekken 8"


def test_add_combo_strips_whitespace():
    combos = []
    combo = add_combo(combos, "  Steve  ", "  Combo 1  ", "  f+2  ")
    assert combo["character"] == "Steve"
    assert combo["name"] == "Combo 1"
    assert combo["notation"] == "f+2"


def test_save_then_load_roundtrips(tmp_path):
    path = tmp_path / "combos.json"
    combos = []
    add_combo(combos, "Steve", "Combo 1", "f+2")
    add_combo(combos, "Jun", "Combo 2", "d+1+2")
    save_combos(combos, path)

    reloaded = load_combos(path)
    assert len(reloaded) == 2
    assert reloaded[0]["character"] == "Steve"
    assert reloaded[1]["character"] == "Jun"


def test_remove_combo_by_id():
    combos = []
    combo1 = add_combo(combos, "Steve", "Combo 1", "f+2")
    add_combo(combos, "Steve", "Combo 2", "d+1")
    remove_combo(combos, combo1["id"])
    assert len(combos) == 1
    assert combos[0]["name"] == "Combo 2"


def test_remove_combo_with_unknown_id_is_a_noop():
    combos = []
    add_combo(combos, "Steve", "Combo 1", "f+2")
    remove_combo(combos, "unknown-id")
    assert len(combos) == 1


def test_grouped_by_game_and_character_sorts_and_groups():
    combos = []
    add_combo(combos, "Jun", "J Combo", "f+2", game="Tekken 8")
    add_combo(combos, "Steve", "S Combo 1", "f+2", game="Tekken 8")
    add_combo(combos, "Steve", "S Combo 2", "d+1", game="Tekken 8")
    add_combo(combos, "Ryu", "R Combo", "d,df,f+1", game="Street Fighter 6")

    groups = grouped_by_game_and_character(combos)
    keys = [key for key, _ in groups]
    assert keys == [
        ("Street Fighter 6", "Ryu"),
        ("Tekken 8", "Jun"),
        ("Tekken 8", "Steve"),
    ]
    steve_group = dict(groups)[("Tekken 8", "Steve")]
    assert [c["name"] for c in steve_group] == ["S Combo 1", "S Combo 2"]
