#!/usr/bin/env python3
"""La version d'un système : celle de la `<release>` la plus récente de son metainfo (docs/systemes.md d'ARRSA,
« Publier »), la seule source de sa version.

    version.py lire <metainfo>                                → X.Y.Z
    version.py monter <metainfo> [patch|minor|major] [--date AAAA-MM-JJ]   → X.Y.Z+1, ajoutée en tête

Appelé par le flux commun publier.yml : une publication lancée à la main (hangar, onglet Actions) monte la
version, la committe et pose l'étiquette vX.Y.Z ; une publication partie d'une étiquette vérifie qu'elle
dit la même version que le metainfo. Le fichier est modifié comme texte (sa mise en forme reste).
Bibliothèque standard seule.
"""
import argparse
import datetime
import re
import sys
from pathlib import Path

RELEASE = re.compile(r'<release\b[^>]*\bversion="(\d+)\.(\d+)\.(\d+)"')
NIVEAUX = ("patch", "minor", "major")


def lire(texte: str) -> str:
    m = RELEASE.search(texte)
    if not m:
        raise SystemExit('metainfo : pas de <release version="X.Y.Z">')
    return ".".join(m.groups())


def suivante(version: str, niveau: str) -> str:
    majeur, mineur, correctif = (int(n) for n in version.split("."))
    if niveau == "major":
        return f"{majeur + 1}.0.0"
    if niveau == "minor":
        return f"{majeur}.{mineur + 1}.0"
    return f"{majeur}.{mineur}.{correctif + 1}"


def monter(texte: str, niveau: str, date: str) -> tuple[str, str]:
    """(texte avec la nouvelle <release> en tête, nouvelle version)."""
    nouvelle = suivante(lire(texte), niveau)
    debut = RELEASE.search(texte).start()
    ligne = texte.rfind("\n", 0, debut) + 1
    retrait = texte[ligne:debut] if not texte[ligne:debut].strip() else ""
    ajout = f'<release version="{nouvelle}" date="{date}"/>' + ("\n" + retrait if retrait else "")
    return texte[:debut] + ajout + texte[debut:], nouvelle


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("geste", choices=("lire", "monter"))
    a.add_argument("metainfo", type=Path)
    a.add_argument("niveau", nargs="?", choices=NIVEAUX, default="patch")
    a.add_argument("--date", default=datetime.date.today().isoformat())
    o = a.parse_args()
    texte = o.metainfo.read_text(encoding="utf-8")
    if o.geste == "lire":
        print(lire(texte))
        return 0
    texte, nouvelle = monter(texte, o.niveau, o.date)
    o.metainfo.write_text(texte, encoding="utf-8")
    print(nouvelle)
    return 0


if __name__ == "__main__":
    sys.exit(main())
