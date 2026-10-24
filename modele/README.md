# @Nom@ (@CODE@)

@BUT@

Système d'ARRSA OS (fiche `systeme.toml`, norme : `~/ARRSA/docs/systemes.md`), installé en Flatpak
`org.arrsa.@Nom@` depuis le catalogue `arrsa-systemes`.

```sh
uv run python -m @nom@        # lancer depuis le clone
uv run pytest -q              # tests
sh outils/flatpak.sh          # construire et installer le Flatpak en local (essai)
```
