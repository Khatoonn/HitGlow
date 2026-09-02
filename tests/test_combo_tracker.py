from hitglow.combo_tracker import ComboTracker

TRACKABLE = lambda inputs: {"raw": "x", "trackable": True, "inputs": frozenset(inputs)}
TEXT_ONLY = {"raw": "LNH 2", "trackable": False, "inputs": None}


def test_starts_at_step_zero_not_complete():
    tracker = ComboTracker([TRACKABLE({"RIGHT"})])
    assert tracker.current_step() == TRACKABLE({"RIGHT"})
    assert not tracker.is_complete()


def test_advances_when_required_inputs_are_pressed():
    tracker = ComboTracker([TRACKABLE({"RIGHT", "2"}), TRACKABLE({"1"})])
    assert tracker.update({"RIGHT", "2"}) is True
    assert tracker.index == 1
    assert tracker.current_step() == TRACKABLE({"1"})


def test_does_not_advance_on_partial_match():
    tracker = ComboTracker([TRACKABLE({"RIGHT", "2"})])
    assert tracker.update({"RIGHT"}) is False
    assert tracker.index == 0


def test_does_not_double_advance_while_input_stays_held():
    tracker = ComboTracker([TRACKABLE({"2"}), TRACKABLE({"2"})])
    assert tracker.update({"2"}) is True
    assert tracker.index == 1
    # Meme input toujours enfonce la frame suivante : ne doit pas aussi
    # valider l'etape 2 (qui demande exactement le meme input) d'un coup.
    assert tracker.update({"2"}) is False
    assert tracker.index == 1


def test_requires_a_fresh_press_after_release():
    tracker = ComboTracker([TRACKABLE({"2"}), TRACKABLE({"2"})])
    tracker.update({"2"})
    tracker.update(set())  # relache
    assert tracker.update({"2"}) is True
    assert tracker.index == 2


def test_text_only_step_never_auto_advances():
    tracker = ComboTracker([TEXT_ONLY])
    assert tracker.update({"RIGHT", "1", "2", "3", "4", "UP", "DOWN", "LEFT"}) is False
    assert tracker.index == 0


def test_advance_manual_moves_past_text_only_step():
    tracker = ComboTracker([TEXT_ONLY, TRACKABLE({"1"})])
    tracker.advance_manual()
    assert tracker.index == 1
    assert tracker.current_step() == TRACKABLE({"1"})


def test_is_complete_after_last_step():
    tracker = ComboTracker([TRACKABLE({"1"})])
    tracker.update({"1"})
    assert tracker.is_complete()
    assert tracker.current_step() is None


def test_reset_returns_to_start():
    tracker = ComboTracker([TRACKABLE({"1"}), TRACKABLE({"2"})])
    tracker.update({"1"})
    tracker.reset()
    assert tracker.index == 0
    assert not tracker.is_complete()
