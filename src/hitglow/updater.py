"""Verification de mise a jour via les releases GitHub. Ne telecharge ni
n'execute jamais rien automatiquement : se contente de comparer la version
locale a la derniere release publiee, et laisse l'utilisateur ouvrir la
page de telechargement lui-meme (voir settings_app._check_for_update)."""

import json
import re
import urllib.request

GITHUB_REPO = "Khatoonn/HitGlow"
REQUEST_TIMEOUT_SECONDS = 5


def parse_version(text):
    """Parse "v1.2.3" ou "1.2.3" en tuple (1, 2, 3). Retourne (0, 0, 0)
    si le texte ne ressemble a aucune version connue."""
    match = re.search(r"(\d+)\.(\d+)\.(\d+)", text or "")
    if not match:
        return (0, 0, 0)
    return tuple(int(part) for part in match.groups())


def is_newer(remote_version_text, local_version_text):
    return parse_version(remote_version_text) > parse_version(local_version_text)


def check_for_update(current_version, repo=GITHUB_REPO, timeout=REQUEST_TIMEOUT_SECONDS):
    """Interroge l'API GitHub pour la derniere release publiee. Retourne
    None si aucune mise a jour n'est disponible OU si la verification a
    echoue pour n'importe quelle raison (pas de connexion, API
    indisponible, etc.) — un echec de verification ne doit jamais gener
    l'utilisation normale de l'application.

    En cas de mise a jour disponible, retourne :
      {"version": "0.3.0", "url": "https://github.com/.../releases/tag/v0.3.0"}
    """
    url = f"https://api.github.com/repos/{repo}/releases/latest"
    try:
        request = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
        with urllib.request.urlopen(request, timeout=timeout) as response:
            data = json.loads(response.read().decode("utf-8"))
    except Exception:
        return None

    tag_name = data.get("tag_name", "")
    if not is_newer(tag_name, current_version):
        return None

    return {
        "version": tag_name.lstrip("v"),
        "url": data.get("html_url") or f"https://github.com/{repo}/releases/latest",
    }
