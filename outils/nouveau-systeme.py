#!/usr/bin/env python3
"""Un nouveau système d'ARRSA depuis le modèle (`modele/`, voir modele/LISEZMOI-MODELE.md).

    python3 outils/nouveau-systeme.py --code S2 --nom Vigie --but "…" --nature instrument ~/Projets/vigie

Copie `modele/` dans le dossier donné (qui doit être vide ou absent) en remplaçant les marques
dans les noms de fichiers et les contenus : @CODE@ (S2), @Nom@ (Vigie), @nom@ (vigie, nom de
paquet Python), @NOM@ (VIGIE, la plaque), @BUT@, @NATURE@, @DATE@ (aujourd'hui). Ne réserve pas
le code et ne crée pas le dépôt : c'est le travail du skill `creer-systeme` d'ARRSA, qui appelle
cet outil (le code doit être réservé dans le registre d'ARRSA AVANT, docs/systemes.md).
Bibliothèque standard seule.
"""
import argparse
import datetime
import re
import shutil
import sys
from pathlib import Path

MODELE = Path(__file__).resolve().parent.parent / "modele"
EXCLUS = {"LISEZMOI-MODELE.md"}  # mode d'emploi du modèle : pas dans le système


def marques(code: str, nom: str, but: str, nature: str) -> dict[str, str]:
    paquet = re.sub(r"[^a-z0-9_]", "_", nom.lower())
    return {"@CODE@": code, "@Nom@": nom, "@nom@": paquet, "@NOM@": nom.upper(), "@BUT@": but,
            "@NATURE@": nature, "@DATE@": datetime.date.today().isoformat()}


def remplir(texte: str, m: dict[str, str]) -> str:
    for marque, valeur in m.items():
        texte = texte.replace(marque, valeur)
    return texte


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("dossier", type=Path)
    a.add_argument("--code", required=True, help="S<n>, déjà réservé dans registre-systemes.toml d'ARRSA")
    a.add_argument("--nom", required=True, help="nom du système, une majuscule (Vigie) : org.arrsa.<Nom>")
    a.add_argument("--but", required=True, help="une phrase : ce que fait le système")
    a.add_argument("--nature", choices=("instrument", "autonome"), default="instrument")
    o = a.parse_args()
    if not re.fullmatch(r"S[1-9]\d{0,2}", o.code):
        a.error("code : S1, S2… (S0 est ARRSA)")
    if not re.fullmatch(r"[A-Z][A-Za-z0-9]*", o.nom):
        a.error("nom : lettres et chiffres, une majuscule au début (il devient org.arrsa.<Nom>)")
    if '"' in o.but or "\n" in o.but:
        a.error("but : une phrase, sans guillemets droits")
    dest = o.dossier.expanduser()
    if dest.exists() and any(dest.iterdir()):
        a.error(f"{dest} n'est pas vide")
    m = marques(o.code, o.nom, o.but, o.nature)
    for source in sorted(MODELE.rglob("*")):
        relatif = source.relative_to(MODELE)
        if relatif.name in EXCLUS or "__pycache__" in relatif.parts:
            continue
        cible = dest / remplir(str(relatif), m)
        if source.is_dir():
            cible.mkdir(parents=True, exist_ok=True)
            continue
        cible.parent.mkdir(parents=True, exist_ok=True)
        cible.write_text(remplir(source.read_text(encoding="utf-8"), m), encoding="utf-8")
        shutil.copymode(source, cible)
    reste = [str(p) for p in dest.rglob("*") if p.is_file() and "@" in p.name
             or p.is_file() and re.search(r"@[A-Za-z]+@", p.read_text(encoding="utf-8"))]
    if reste:
        print("Marques non remplacées :", ", ".join(reste), file=sys.stderr)
        return 1
    print(dest)
    return 0


if __name__ == "__main__":
    sys.exit(main())
