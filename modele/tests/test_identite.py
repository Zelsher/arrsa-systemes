"""L'identité du système suit sa fiche, et le paquet l'embarque (~/ARRSA/docs/systemes.md)."""
import tomllib
from pathlib import Path

import @nom@
from @nom@ import norme

ICI = Path(__file__).resolve().parent.parent


def test_identite_suit_la_fiche():
    fiche = tomllib.loads((ICI / "systeme.toml").read_text(encoding="utf-8"))["systeme"]
    assert (@nom@.CODE, @nom@.NOM) == (fiche["code"], fiche["nom"])
    assert @nom@.ID_APPLI == f"org.arrsa.{fiche['nom']}"


def test_le_paquet_embarque_la_fiche():
    """ARRSA lit la plaque dans /app/share/arrsa/systeme.toml ; la fenêtre se relie à son .desktop."""
    manifeste = (ICI / f"paquet/{@nom@.ID_APPLI}.yml").read_text(encoding="utf-8")
    assert "install -Dm644 systeme.toml -t /app/share/arrsa" in manifeste
    assert "--filesystem=xdg-data/themes/arrsa:ro" in manifeste
    bureau = (ICI / f"paquet/{@nom@.ID_APPLI}.desktop").read_text(encoding="utf-8")
    assert f"StartupWMClass={@nom@.ID_APPLI}" in bureau


def test_norme_absente_valeurs_par_defaut(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    assert norme.lire()["couleur"]["accent"] == norme.DEFAUT["couleur"]["accent"]
    (tmp_path / "themes/arrsa/norme").mkdir(parents=True)
    (tmp_path / "themes/arrsa/norme/norme.json").write_text('{"version": 1, "couleur": {"accent": "#33ccff"}}')
    lue = norme.lire()
    assert lue["couleur"]["accent"] == "#33ccff" and lue["couleur"]["fond"] == norme.DEFAUT["couleur"]["fond"]
