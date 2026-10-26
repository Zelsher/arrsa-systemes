"""La version d'un système et sa montée (outils/version.py, appelé par le flux commun publier.yml)."""
import unittest

from test_verifier import charger

version = charger("version")

LIGNE = '<releases><release version="0.2.0" date="2026-10-14"/></releases>'
BLOC = """  <releases>
    <release version="1.4.9" date="2026-10-01"/>
    <release version="1.4.8" date="2026-09-01"/>
  </releases>
"""


class Version(unittest.TestCase):
    def test_lire_la_plus_recente(self):
        self.assertEqual(version.lire(BLOC), "1.4.9")

    def test_niveaux(self):
        self.assertEqual([version.suivante("1.4.9", n) for n in version.NIVEAUX], ["1.4.10", "1.5.0", "2.0.0"])

    def test_monter_garde_la_mise_en_forme(self):
        texte, nouvelle = version.monter(BLOC, "patch", "2026-10-27")
        self.assertEqual(nouvelle, "1.4.10")
        self.assertEqual(texte.splitlines()[1:3], ['    <release version="1.4.10" date="2026-10-27"/>',
                                                   '    <release version="1.4.9" date="2026-10-01"/>'])
        texte, _ = version.monter(LIGNE, "minor", "2026-10-27")
        self.assertEqual(texte, '<releases><release version="0.3.0" date="2026-10-27"/>'
                                '<release version="0.2.0" date="2026-10-14"/></releases>')

    def test_sans_release(self):
        with self.assertRaises(SystemExit):
            version.lire("<releases/>")


if __name__ == "__main__":
    unittest.main()
