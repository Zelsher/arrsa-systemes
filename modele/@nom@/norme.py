"""L'apparence d'ARRSA OS, lue par son canal public (~/ARRSA/docs/systemes.md, « Apparence »).

ARRSA écrit, à chaque changement de thème, ~/.local/share/themes/arrsa/norme/norme.json : couleurs
de la session, pièces des fenêtres (coupes, traits, opacités), polices, tailles, espaces ; et
norme.css (variables --arrsa-*) pour une interface web. Le Flatpak l'ouvre en lecture seule
(--filesystem=xdg-data/themes/arrsa:ro). Fichier absent (autre OS, ARRSA pas encore lancé) : les
valeurs par défaut ci-dessous, sombres et neutres. Jamais les fichiers internes d'ARRSA.
"""
import json
import os
from pathlib import Path

DEFAUT = {
    "version": 1,
    "couleur": {"fond": "#0a0a0a", "surface": "#181818", "surface-2": "#212122", "coque": "#111111",
                "trait": "#2e2f30", "accent": "#ff2d95", "texte": "#eef2f6", "texte-attenue": "#7c8798",
                "ok": "#4ade80", "attention": "#f5b041", "danger": "#f2577a"},
    "police": {"principale": "Chakra Petch", "lecture": "Chakra Petch", "chasse-fixe": "Share Tech Mono"},
}


def chemin() -> Path:
    donnees = os.environ.get("XDG_DATA_HOME") or str(Path.home() / ".local/share")
    return Path(donnees) / "themes/arrsa/norme/norme.json"


def lire() -> dict:
    """La norme en place ; ce qui manque garde la valeur par défaut. Une version plus récente que
    celle que ce code connaît se lit quand même (les clés connues ne changent pas de sens)."""
    try:
        lue = json.loads(chemin().read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return DEFAUT
    return {**DEFAUT, **lue, "couleur": {**DEFAUT["couleur"], **lue.get("couleur", {})},
            "police": {**DEFAUT["police"], **lue.get("police", {})}}
