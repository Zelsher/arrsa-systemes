# Modèle d'un système d'ARRSA

La base d'un nouveau système (S2, S3…) : ce que la norme demande (`~/ARRSA/docs/systemes.md`,
« Construire un système »), déjà en place et testé, sur le modèle de S1 Atlas.

| Fichier | Rôle |
|---|---|
| `systeme.toml` | la fiche : code, nom, nature, but, état, liens |
| `@nom@/__init__.py` | l'identité en un seul endroit du code |
| `@nom@/norme.py` | l'apparence d'ARRSA par son canal public (norme.json) |
| `@nom@/__main__.py` | une fenêtre Qt (PySide6) qui suit la norme et se relie à son .desktop |
| `tests/test_identite.py` | identité ↔ fiche, fiche embarquée, norme absente |
| `paquet/` | manifeste Flatpak, .desktop, metainfo (version), icône de départ |
| `outils/flatpak.sh` | essai local du Flatpak |
| `.github/workflows/publier.yml` | publication dans le catalogue (appelle celle de ce dépôt) |
| `CLAUDE.md`, `README.md` | comment travailler sur le système |

Ne pas copier à la main : `python3 outils/nouveau-systeme.py --code S2 --nom Vigie --but "…"
--nature instrument ~/Projets/vigie` remplace les marques (`@CODE@`, `@Nom@`, `@nom@`, `@NOM@`,
`@BUT@`, `@NATURE@`, `@DATE@`) dans les noms et les contenus. Dans une session Claude Code
d'ARRSA, le skill `creer-systeme` fait tout le chemin (trois tests, réservation du code, dépôt
privé, ce modèle, premier commit). Une autre langue qu'en Python : garder la fiche, le paquet, la
plaque (rien à faire) et la lecture de norme.json ; le reste appartient au système.
