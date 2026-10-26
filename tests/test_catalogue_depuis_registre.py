"""La liste du catalogue est une copie du registre d'ARRSA (outils/catalogue-depuis-registre.py)."""
import tomllib
import unittest

from test_verifier import charger

outil = charger("catalogue-depuis-registre")

REGISTRE = """
[S0]
nom = "ARRSA"
flatpak = ""
[S2]
nom = "Vigie"
flatpak = "org.arrsa.Vigie"
paquet = "systemes-vigie"
[S1]
nom = "Atlas"
flatpak = "org.arrsa.Atlas"
paquet = "systemes-atlas"
catalogue = true
[retires]
"S0.1" = "ancien code d'Atlas"
"""


class Liste(unittest.TestCase):
    def test_seuls_les_systemes_au_catalogue(self):
        liste = tomllib.loads(outil.liste(tomllib.loads(REGISTRE)))["systeme"]
        self.assertEqual(liste, [{"code": "S1", "appli": "org.arrsa.Atlas", "paquet": "systemes-atlas"}])

    def test_catalogue_sans_paquet_refuse(self):
        with self.assertRaises(SystemExit):
            outil.liste(tomllib.loads('[S1]\nnom = "A"\nflatpak = "org.arrsa.A"\ncatalogue = true\n'))


if __name__ == "__main__":
    unittest.main()
