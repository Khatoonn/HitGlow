"""Verification de mise a jour via les releases GitHub, et mise a jour en un
clic : telecharge le nouvel installeur (asset officiel de la release, servi
en HTTPS par GitHub) et le lance — voir settings_app._start_auto_update.
Un echec de verification ou de telechargement ne doit jamais gener
l'utilisation normale de l'application ; l'appelant est responsable
d'afficher une erreur et de proposer le lien de la release en repli."""

import json
import os
import re
import urllib.request

GITHUB_REPO = "Khatoonn/HitGlow"
REQUEST_TIMEOUT_SECONDS = 5
DOWNLOAD_TIMEOUT_SECONDS = 30
INSTALLER_ASSET_NAME = "HitGlow-Setup.exe"


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
      {"version": "0.3.0", "url": "https://github.com/.../releases/tag/v0.3.0",
       "installer_url": "https://github.com/.../releases/download/v0.3.0/HitGlow-Setup.exe"}
    "installer_url" vaut None si la release n'a pas d'asset HitGlow-Setup.exe
    (ex: release faite a la main sans binaire attache) — dans ce cas
    l'appelant doit se rabattre sur "url".
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

    installer_url = None
    for asset in data.get("assets", []) or []:
        if asset.get("name") == INSTALLER_ASSET_NAME:
            installer_url = asset.get("browser_download_url")
            break

    return {
        "version": tag_name.lstrip("v"),
        "url": data.get("html_url") or f"https://github.com/{repo}/releases/latest",
        "installer_url": installer_url,
    }


def download_file(url, dest_path, timeout=DOWNLOAD_TIMEOUT_SECONDS, progress_callback=None):
    """Telecharge url vers dest_path. Ecrit d'abord dans un fichier
    temporaire (".part") puis renomme atomiquement a la fin, pour ne
    jamais laisser un fichier tronque au chemin final en cas de coupure.
    progress_callback(bytes_written, total_bytes) est appele apres chaque
    bloc lu si fourni (total_bytes vaut 0 si le serveur ne l'annonce pas).
    Leve une exception si le telechargement echoue — a l'appelant de
    l'attraper et d'afficher une erreur."""
    request = urllib.request.Request(url, headers={"Accept": "application/octet-stream"})
    part_path = f"{dest_path}.part"
    with urllib.request.urlopen(request, timeout=timeout) as response:
        total = int(response.headers.get("Content-Length") or 0)
        written = 0
        with open(part_path, "wb") as f:
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                f.write(chunk)
                written += len(chunk)
                if progress_callback is not None:
                    progress_callback(written, total)
    os.replace(part_path, dest_path)
    return dest_path
