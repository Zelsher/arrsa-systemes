#!/usr/bin/env python3
"""Écrit `systemes.toml` (la liste que lit le robot du catalogue) depuis le registre d'ARRSA.

    python3 outils/catalogue-depuis-registre.py ~/ARRSA/registre-systemes.toml [--verifier]

Le registre d'ARRSA (`registre-systemes.toml`) fait foi pour les systèmes (ADR 0173 d'ARRSA) : il
réserve le code avant la naissance du dépôt, et dit pour chacun son appli, son paquet ghcr.io et
s'il est au catalogue (`catalogue = true`, posé après le geste « Manage Actions access » du paquet :
avant, son image serait illisible et ferait échouer tout l'index). Ce dépôt-ci est public et son robot
ne peut pas lire ARRSA (privé) : il garde une copie, générée par cet outil, jamais écrite à la main.
`--verifier` ne change rien et sort 1 si la copie a dérivé. Bibliothèque standard seule.
"""
import argparse
import re
import sys
import tomllib
from pathlib import Path

LISTE = Path(__file__).resolve().parent.parent / "systemes.toml"
CODE = re.compile(r"^S[1-9][0-9]*$")
EN_TETE = """\
# Les systèmes du catalogue : le robot lit ghcr.io/zelsher/<paquet>:latest de chacun.
# GÉNÉRÉ depuis registre-systemes.toml d'ARRSA (qui fait foi, ADR 0173) : ne pas modifier à la main.
#   python3 outils/catalogue-depuis-registre.py ~/ARRSA/registre-systemes.toml
# Un système y entre quand le registre dit catalogue = true, c'est-à-dire après sa première
# publication et le geste « Manage Actions access » → arrsa-systemes, rôle Read, sur son paquet.
"""


def liste(registre: dict) -> str:
    blocs = []
    for code, entree in sorted(registre.items(), key=lambda kv: int(kv[0][1:]) if CODE.match(kv[0]) else -1):
        if not CODE.match(code) or not isinstance(entree, dict) or entree.get("catalogue") is not True:
            continue
        if not (entree.get("flatpak") and entree.get("paquet")):
            raise SystemExit(f"{code} : catalogue = true demande flatpak et paquet")
        blocs.append(f'[[systeme]]\ncode = "{code}"\nappli = "{entree["flatpak"]}"\npaquet = "{entree["paquet"]}"\n')
    return EN_TETE + "".join("\n" + b for b in blocs)


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("registre", type=Path)
    a.add_argument("--verifier", action="store_true", help="comparer sans écrire ; 1 si la copie a dérivé")
    o = a.parse_args()
    attendu = liste(tomllib.loads(o.registre.expanduser().read_text(encoding="utf-8")))
    if o.verifier:
        if LISTE.read_text(encoding="utf-8") != attendu:
            print(f"{LISTE.name} a dérivé du registre : relancer sans --verifier", file=sys.stderr)
            return 1
        return 0
    LISTE.write_text(attendu, encoding="utf-8")
    print(LISTE)
    return 0


if __name__ == "__main__":
    sys.exit(main())
