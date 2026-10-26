# Modèle d'un système d'ARRSA

La base d'un nouveau système (S2, S3…). La norme qu'il suit est `~/ARRSA/docs/systemes.md` et elle
seule (fiche, identité, paquet, apparence, tests, publication) ; un système qui sort de ce modèle
la passe, ce que vérifie `outils/verifier.py` (`tests/test_verifier.py`).

| Fichier | Rôle |
|---|---|
| `systeme.toml` | la fiche |
| `@nom@/__init__.py` | l'identité en un seul endroit du code |
| `@nom@/norme.py` | l'apparence d'ARRSA par son canal public (norme.json) |
| `@nom@/__main__.py` | une fenêtre Qt (PySide6) qui suit la norme et se relie à son .desktop |
| `tests/test_identite.py` | identité ↔ fiche, norme absente |
| `paquet/` | manifeste Flatpak, .desktop, metainfo (version), icône de départ |
| `outils/flatpak.sh` | essai local du Flatpak |
| `.github/workflows/publier.yml` | publication dans le catalogue (appelle celle de ce dépôt) |
| `CLAUDE.md`, `README.md` | comment travailler sur le système |

Ne pas copier à la main : `python3 outils/nouveau-systeme.py --code S2 --nom Vigie --but "…"
--nature instrument ~/Projets/vigie` remplace les marques (`@CODE@`, `@Nom@`, `@nom@`, `@NOM@`,
`@BUT@`, `@NATURE@`, `@DATE@`) dans les noms et les contenus. Dans une session Claude Code
d'ARRSA, la skill `creer-systeme` fait tout le chemin. Une autre langue que Python : garder la
fiche, le paquet et la lecture de norme.json, réécrire l'identité et son test ; le reste appartient
au système. Changer ce modèle : changer d'abord la norme, puis le vérificateur, puis ici.
