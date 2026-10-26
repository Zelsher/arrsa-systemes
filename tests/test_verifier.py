"""Le vérificateur de la norme (outils/verifier.py) et le modèle qu'il juge.

    python3 -m unittest discover -s tests

Un système tout juste sorti du modèle est conforme ; chaque test casse ensuite une seule chose et
attend la règle qui la nomme. Bibliothèque standard seule, comme les outils.
"""
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ICI = Path(__file__).resolve().parent.parent
OUTILS = ICI / "outils"


def charger(nom: str):
    spec = importlib.util.spec_from_file_location(nom.replace("-", "_"), OUTILS / f"{nom}.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module  # les dataclasses relisent leur module
    spec.loader.exec_module(module)
    return module


verifier = charger("verifier")


class Systeme(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory()
        self.d = Path(self._tmp.name) / "vigie"
        subprocess.run([sys.executable, OUTILS / "nouveau-systeme.py", "--code", "S7", "--nom", "Vigie",
                        "--but", "Veiller.", "--nature", "autonome", self.d], check=True, capture_output=True)

    def tearDown(self):
        self._tmp.cleanup()

    def regles(self, **kw):
        return sorted({e.regle for e in verifier.verifier(self.d, **kw)})

    def remplacer(self, relatif, avant, apres):
        p = self.d / relatif
        texte = p.read_text(encoding="utf-8")
        self.assertIn(avant, texte)
        p.write_text(texte.replace(avant, apres), encoding="utf-8")

    def test_le_modele_est_conforme(self):
        self.assertEqual(verifier.verifier(self.d), [])

    def test_contrat_ligne_de_commande(self):
        """Le contrat qu'Horizon lit : --json, trois clés, code de sortie 0 / 1."""
        appel = [sys.executable, OUTILS / "verifier.py", self.d, "--json"]
        ok = subprocess.run(appel, capture_output=True, text=True)
        self.assertEqual((ok.returncode, json.loads(ok.stdout)), (0, []))
        self.remplacer("systeme.toml", 'nature = "autonome"', 'nature = "socle"')
        ko = subprocess.run(appel, capture_output=True, text=True)
        sortie = json.loads(ko.stdout)
        self.assertEqual(ko.returncode, 1)
        self.assertEqual([set(e) for e in sortie], [{"regle", "fichier", "message"}])
        self.assertEqual((sortie[0]["regle"], sortie[0]["fichier"]), ("fiche-nature", "systeme.toml"))
        self.assertIn("docs/systemes.md", sortie[0]["message"])

    def test_fiche(self):
        cas = [
            ('code = "S7"', 'code = "S0"', "fiche-plaque"),
            ('code = "S7"', "code = 'S7'", "fiche-plaque"),  # TOML valide, mais la décoration ne le lit pas
            ('nom = "Vigie"', 'nom = "Vigie"\n[autre]', "fiche-champs"),
            ('etat = "actif"', 'etat = "absorbe"', "fiche-etat"),
            ('etat = "actif"', 'etat = "fini"', "fiche-etat"),
            ("utilise = []", 'utilise = ["S0.1"]', "fiche-liens"),
            ("utilise = []", 'utilise = ["S7"]', "fiche-liens"),
            ('commandes = ["uv run pytest -q"]', "commandes = []", "tests-declares"),
        ]
        original = (self.d / "systeme.toml").read_text(encoding="utf-8")
        for avant, apres, regle in cas:
            with self.subTest(apres):
                (self.d / "systeme.toml").write_text(original.replace(avant, apres), encoding="utf-8")
                self.assertIn(regle, self.regles())
        (self.d / "systeme.toml").unlink()
        self.assertEqual(self.regles(), ["fiche-lisible"])

    def test_identite_en_un_seul_endroit(self):
        self.remplacer("vigie/__main__.py", "from . import ID_APPLI, NOM, norme",
                       "from . import NOM, norme\nID_APPLI = 'org.arrsa.Vigie'")
        self.assertEqual(self.regles(), ["identite-un-seul-endroit"])

    def test_identite_testee(self):
        (self.d / "tests/test_identite.py").unlink()
        self.assertEqual(self.regles(), ["identite-testee"])

    def test_une_seule_plaque(self):
        self.remplacer("vigie/__main__.py", "from . import ID_APPLI, NOM, norme",
                       "from . import ID_APPLI, NOM, norme\nPLAQUE = 'SYSTEM 07'")
        self.assertEqual(self.regles(), ["apparence-une-plaque"])

    def test_permissions(self):
        manifeste = "paquet/org.arrsa.Vigie.yml"
        cas = [
            ("  - --device=dri\n", "  - --device=dri\n  - --share=network\n", "paquet-permissions-commentees"),
            ("  - --device=dri\n", "  - --device=dri\n  # tout\n  - --filesystem=home\n", "paquet-acces-larges"),
            ("  - --device=dri\n", "  - --device=dri\n  # la porte\n  - --filesystem=xdg-run/arrsa\n", "paquet-portes"),
            ("  - --device=dri\n", "  - --device=dri\n  # clé\n  - --talk-name=org.freedesktop.secrets\n", "paquet-portes"),
            ("themes/arrsa:ro", "themes/arrsa", "paquet-norme-lecture-seule"),
            ("install -Dm644 systeme.toml -t /app/share/arrsa", "true", "paquet-fiche-embarquee"),
            ("runtime: org.kde.Platform", "runtime: com.exemple.Platform", "paquet-runtime"),
        ]
        original = (self.d / manifeste).read_text(encoding="utf-8")
        for avant, apres, regle in cas:
            with self.subTest(apres):
                self.assertIn(avant, original)
                (self.d / manifeste).write_text(original.replace(avant, apres), encoding="utf-8")
                self.assertEqual(self.regles(), [regle])

    def test_acces_large_avec_exception_ecrite(self):
        self.remplacer("paquet/org.arrsa.Vigie.yml", "  - --device=dri\n",
                       "  - --device=dri\n  # exception norme : lire n'importe quel projet\n  - --filesystem=home:ro\n")
        self.assertEqual(self.regles(), [])

    def test_sources_sans_empreinte(self):
        source = ("      - type: dir\n        path: ..\n")
        archive = ("      - type: archive\n        url: https://exemple.org/x.tar.xz\n")
        self.remplacer("paquet/org.arrsa.Vigie.yml", source, archive + source)
        self.assertEqual(self.regles(), ["paquet-sha256"])
        self.remplacer("paquet/org.arrsa.Vigie.yml", archive, archive + "        sha256: " + "0" * 64 + "\n")
        self.assertEqual(self.regles(), [])
        # un module inclus en JSON (dépendances générées) se lit aussi
        self.remplacer("paquet/org.arrsa.Vigie.yml", "modules:\n", "modules:\n  - deps.json\n")
        (self.d / "paquet/deps.json").write_text(json.dumps(
            {"name": "deps", "sources": [{"type": "file", "url": "https://exemple.org/a.whl"}]}))
        self.assertEqual(self.regles(), ["paquet-sha256"])

    def test_lanceur_et_metainfo(self):
        self.remplacer("paquet/org.arrsa.Vigie.desktop", "SingleMainWindow=true", "X-Arrsa-Code=S7")
        self.remplacer("paquet/org.arrsa.Vigie.metainfo.xml", 'version="0.1.0"', 'version="un"')
        self.assertEqual(self.regles(), ["paquet-desktop", "paquet-metainfo"])

    def test_etiquettes(self):
        git = lambda *a: subprocess.run(["git", "-C", self.d, *a], check=True, capture_output=True)  # noqa: E731
        git("init", "-q", "-b", "main")
        git("add", "-A")
        git("-c", "user.name=t", "-c", "user.email=t@t", "commit", "-q", "-m", "naissance")
        self.assertEqual(self.regles(), [])
        git("tag", "v0.1.0")
        self.assertEqual(self.regles(), [])
        git("tag", "v0.2.0")
        self.assertEqual(self.regles(), ["version-etiquette"])

    def test_publication(self):
        self.remplacer(".github/workflows/publier.yml", "paquet: systemes-vigie", "paquet: autre")
        self.assertEqual(self.regles(), ["publication-flux"])

    def test_claude_md(self):
        self.remplacer("CLAUDE.md", "docs/systemes.md", "la norme")
        self.assertEqual(self.regles(), ["depot-claude-md"])

    def test_registre(self):
        registre = Path(self._tmp.name) / "registre-systemes.toml"
        registre.write_text('[S0]\nnom = "ARRSA"\n[S7]\nnom = "Vigie"\nflatpak = "org.arrsa.Vigie"\n'
                            'paquet = "systemes-vigie"\n')
        self.assertEqual(self.regles(registre=registre), [])
        registre.write_text('[S0]\nnom = "ARRSA"\n[retires]\n"S7" = "abandonné"\n')
        self.assertEqual(self.regles(registre=registre), ["registre-reserve"])

    def test_commandes_de_test_lancees_sur_demande(self):
        self.remplacer("systeme.toml", 'commandes = ["uv run pytest -q"]', 'commandes = ["true", "exit 3"]')
        self.assertEqual(self.regles(), [])
        self.assertEqual(self.regles(tests=True), ["tests-passent"])


class Decoration(unittest.TestCase):
    def test_meme_lecture_que_le_shell(self):
        """Port de lireFiche (shell/decoration/fiche.cpp d'ARRSA)."""
        lire = verifier.plaque_de_la_decoration
        self.assertEqual(lire('[systeme]\ncode = "S1"\nnom = "Atlas"  # x\n'), ("ATLAS", "SYSTEM 01"))
        self.assertIsNone(lire('[autre]\ncode = "S1"\nnom = "Atlas"\n'))
        self.assertIsNone(lire('[systeme]\ncode = "S1.2"\nnom = "Atlas"\n'))
        self.assertIsNone(lire("[systeme]  # fiche\ncode = \"S1\"\nnom = \"Atlas\"\n"))


if __name__ == "__main__":
    unittest.main()
