# @Nom@ (@CODE@) — instructions Claude Code

@BUT@ Ce fichier dit comment travailler sur @Nom@ ; la norme des systèmes vit dans le dépôt d'ARRSA
(`~/ARRSA/docs/systemes.md`) : la relire avant un changement qui touche l'identité, le paquet ou la
publication.

## Répondre à l'utilisateur

- En français, en **tutoyant**. Court et direct, mais **toujours avec le pourquoi** ; il n'est pas
  expert : pas de jargon sans explication.
- L'action ou la conclusion d'abord, puis les étapes. Chaque choix d'architecture : pourquoi celui-là,
  les alternatives écartées. **Avis critique** même sans qu'on le demande ; le meilleur code, pas le
  plus rapide.
- **Gros changement** : plan + discussion, attendre un « go ». **Choix visuel** : montrer avant de
  trancher. Finir par **une seule** prochaine action.

## @Nom@ est un système (norme S0, S1, S2…)

- **S0** = ARRSA, l'OS de l'utilisateur ; @Nom@ est **@CODE@**. Un code ne change jamais. La nature
  (instrument, autonome) est dans la fiche `systeme.toml`, pas dans le code.
- Il ne touche les autres systèmes que par leurs **canaux publics** (tableau « Portes » de
  `docs/systemes.md`) : jamais `api.sock` d'ARRSA, ni ses fichiers internes, ni le trousseau entier.
- **Identité en un seul endroit** : `@nom@/__init__.py` (`CODE`, `NOM`, `ID_APPLI`) ; le test
  `tests/test_identite.py` vérifie qu'elle suit la fiche.

## Apparence

- La **plaque** « @NOM@ / SYSTEM NN » de la barre de titre est dessinée par ARRSA à partir de la
  fiche embarquée dans le Flatpak : ne pas remettre de plaque d'identité dans la fenêtre.
- L'intérieur suit la norme des fenêtres d'ARRSA (`~/ARRSA/docs/style/03-formes.md` : plaques aux
  angles coupés, champs soulignés, case « voyant », trait d'accent) en lisant sa **norme publique**
  (`@nom@/norme.py` : `~/.local/share/themes/arrsa/norme/norme.json`, ou `norme.css` pour une page
  web). Aucune couleur écrite en dur.

## Paquet et publication

- Flatpak `org.arrsa.@Nom@` (`paquet/`), runtime de Flathub, permissions au plus juste et commentées,
  aucune source sans `sha256`. Essai local : `sh outils/flatpak.sh`, puis désinstaller la copie.
- Une version = monter `<release>` dans le metainfo, puis une étiquette `vX.Y.Z` poussée (ou
  « Publier » dans Atelier › Systèmes). Pousser reste un geste demandé par l'utilisateur.

## Commandes

- Tests : `uv run pytest -q`
- Lancer depuis le clone : `uv run python -m @nom@`
- Le travail notable se note au journal de dev d'ARRSA (`python3 ~/ARRSA/scripts/journal-add.py
  "[@nom@] Titre" "puce" …`), comme pour Atlas.
