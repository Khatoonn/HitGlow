import json
from unittest.mock import MagicMock, patch

from hitglow.updater import check_for_update, download_file, is_newer, parse_version


def test_parse_version_with_v_prefix():
    assert parse_version("v1.2.3") == (1, 2, 3)


def test_parse_version_without_prefix():
    assert parse_version("1.2.3") == (1, 2, 3)


def test_parse_version_unrecognized_text_defaults_to_zero():
    assert parse_version("not-a-version") == (0, 0, 0)
    assert parse_version("") == (0, 0, 0)
    assert parse_version(None) == (0, 0, 0)


def test_is_newer_true_when_remote_ahead():
    assert is_newer("v0.3.0", "0.2.0") is True


def test_is_newer_false_when_equal():
    assert is_newer("v0.2.0", "0.2.0") is False


def test_is_newer_false_when_remote_behind():
    assert is_newer("v0.1.0", "0.2.0") is False


def _fake_response(payload):
    response = MagicMock()
    response.read.return_value = json.dumps(payload).encode("utf-8")
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_check_for_update_returns_info_when_newer_release_exists():
    payload = {
        "tag_name": "v0.3.0",
        "html_url": "https://github.com/Khatoonn/HitGlow/releases/tag/v0.3.0",
        "assets": [
            {"name": "HitGlow.exe", "browser_download_url": "https://example.com/HitGlow.exe"},
            {"name": "HitGlow-Setup.exe", "browser_download_url": "https://example.com/HitGlow-Setup.exe"},
        ],
    }
    with patch("hitglow.updater.urllib.request.urlopen", return_value=_fake_response(payload)):
        result = check_for_update("0.2.0")
    assert result == {
        "version": "0.3.0",
        "url": "https://github.com/Khatoonn/HitGlow/releases/tag/v0.3.0",
        "installer_url": "https://example.com/HitGlow-Setup.exe",
    }


def test_check_for_update_installer_url_is_none_when_asset_missing():
    payload = {"tag_name": "v0.3.0", "html_url": "https://github.com/Khatoonn/HitGlow/releases/tag/v0.3.0"}
    with patch("hitglow.updater.urllib.request.urlopen", return_value=_fake_response(payload)):
        result = check_for_update("0.2.0")
    assert result["installer_url"] is None


def test_check_for_update_returns_none_when_up_to_date():
    payload = {"tag_name": "v0.2.0", "html_url": "https://github.com/Khatoonn/HitGlow/releases/tag/v0.2.0"}
    with patch("hitglow.updater.urllib.request.urlopen", return_value=_fake_response(payload)):
        result = check_for_update("0.2.0")
    assert result is None


def test_check_for_update_returns_none_on_network_failure():
    with patch("hitglow.updater.urllib.request.urlopen", side_effect=OSError("no network")):
        result = check_for_update("0.2.0")
    assert result is None


def test_check_for_update_returns_none_on_malformed_response():
    response = MagicMock()
    response.read.return_value = b"not json"
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    with patch("hitglow.updater.urllib.request.urlopen", return_value=response):
        result = check_for_update("0.2.0")
    assert result is None


def _fake_download_response(chunks, content_length=None):
    response = MagicMock()
    response.headers = {"Content-Length": str(content_length)} if content_length is not None else {}
    remaining = list(chunks) + [b""]
    response.read.side_effect = remaining
    response.__enter__.return_value = response
    response.__exit__.return_value = False
    return response


def test_download_file_writes_full_content_and_renames_from_part(tmp_path):
    dest = tmp_path / "HitGlow-Setup.exe"
    response = _fake_download_response([b"hello ", b"world"], content_length=11)
    progress = []
    with patch("hitglow.updater.urllib.request.urlopen", return_value=response):
        result = download_file("https://example.com/HitGlow-Setup.exe", dest, progress_callback=lambda w, t: progress.append((w, t)))
    assert result == dest
    assert dest.read_bytes() == b"hello world"
    assert not (tmp_path / "HitGlow-Setup.exe.part").exists()
    assert progress == [(6, 11), (11, 11)]


def test_download_file_propagates_errors(tmp_path):
    dest = tmp_path / "HitGlow-Setup.exe"
    with patch("hitglow.updater.urllib.request.urlopen", side_effect=OSError("no network")):
        try:
            download_file("https://example.com/HitGlow-Setup.exe", dest)
            assert False, "expected OSError"
        except OSError:
            pass
    assert not dest.exists()
