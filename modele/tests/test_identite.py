"""L'identité du code suit la fiche (~/ARRSA/docs/systemes.md, « Identité dans le code »).

Le paquet (fiche embarquée, norme en lecture seule, StartupWMClass…) est vérifié par
`python3 ~/Projets/arrsa-systemes/outils/verifier.py .`, commun à tous les systèmes."""
import tomllib
from pathlib import Path

import @nom@
from @nom@ import norme

ICI = Path(__file__).resolve().parent.parent


def test_identite_suit_la_fiche():
    fiche = tomllib.loads((ICI / "systeme.toml").read_text(encoding="utf-8"))["systeme"]
    assert (@nom@.CODE, @nom@.NOM) == (fiche["code"], fiche["nom"])
    assert @nom@.ID_APPLI == f"org.arrsa.{fiche['nom']}"


def test_norme_absente_valeurs_par_defaut(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert norme.lire()["couleur"]["accent"] == norme.DEFAUT["couleur"]["accent"]
    (tmp_path / "themes/arrsa/norme").mkdir(parents=True)
    (tmp_path / "themes/arrsa/norme/norme.json").write_text('{"version": 1, "couleur": {"accent": "#33ccff"}}')
    lue = norme.lire()
    assert lue["couleur"]["accent"] == "#33ccff" and lue["couleur"]["fond"] == norme.DEFAUT["couleur"]["fond"]
