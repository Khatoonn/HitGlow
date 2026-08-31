import hitglow


def test_version_is_a_string():
    assert isinstance(hitglow.__version__, str)
    assert hitglow.__version__
