# @Nom@ (@CODE@) — instructions Claude Code

@BUT@ Ce fichier dit comment travailler sur @Nom@.

## Répondre à l'utilisateur

- En français, en **tutoyant**. Court et direct, mais **toujours avec le pourquoi** ; il n'est pas
  expert : pas de jargon sans explication.
- L'action ou la conclusion d'abord, puis les étapes. Chaque choix d'architecture : pourquoi celui-là,
  les alternatives écartées. **Avis critique** même sans qu'on le demande ; le meilleur code, pas le
  plus rapide.
- **Gros changement** : plan + discussion, attendre un « go ». **Choix visuel** : montrer avant de
  trancher. Finir par **une seule** prochaine action.

## @Nom@ est un système (S0, S1, S2…)

La norme des systèmes vit dans le dépôt d'ARRSA, **`~/ARRSA/docs/systemes.md`**, et elle seule
fait foi (fiche, identité en un seul endroit, paquet, apparence, tests, publication) : la relire
avant un changement qui touche l'identité, le paquet ou la publication. Ce fichier ne la recopie
pas. @Nom@ est **@CODE@** ; S0 est ARRSA, l'OS de l'utilisateur.

- Ce qui vit ici : identité `@nom@/__init__.py` (`CODE`, `NOM`, `ID_APPLI`), apparence lue par
  `@nom@/norme.py`, paquet `paquet/`, fiche `systeme.toml` (ses `[tests] commandes`).
- Conforme à la norme : `python3 ~/Projets/arrsa-systemes/outils/verifier.py .` (avant chaque
  commit qui touche la fiche, le paquet ou la publication).
- Pousser, publier, monter la version : des gestes que l'utilisateur demande.

## Commandes

- Tests : `uv run pytest -q` (ceux que déclare la fiche)
- Norme : `python3 ~/Projets/arrsa-systemes/outils/verifier.py .`
- Lancer depuis le clone : `uv run python -m @nom@`
- Le travail notable se note au journal de dev d'ARRSA (`python3 ~/ARRSA/scripts/journal-add.py
  "[@nom@] Titre" "puce" …`), comme pour Atlas.
