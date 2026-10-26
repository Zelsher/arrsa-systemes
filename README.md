# arrsa-systemes

Le catalogue des systèmes d'ARRSA (S1 Atlas, S2…) : l'index que Flatpak lit pour savoir quelles
applis existent et où les télécharger. Décision : ADR 0140 d'ARRSA (« Le hangar des systèmes »).

**Ce dépôt est public et ne contient aucun code.** Les systèmes sont des images Flatpak
**privées** sur `ghcr.io/zelsher/…` : une machine ne les télécharge qu'avec un jeton
`read:packages` (`/etc/flatpak/oci-auth.json`). L'index, lui, doit être lisible sans jeton :
Flatpak ne sait pas présenter de jeton à l'adresse de l'index. Il dit, pour chaque appli : son
nom sur ghcr.io, l'empreinte de son paquet, son identifiant, ses permissions, sa taille et le
message de sa version. Rien de privé ne doit aller dans ces messages.

## Sur une machine

ARRSA OS déclare le dépôt dans son image. À la main :

```sh
flatpak remote-add --system --no-gpg-verify arrsa-systemes oci+https://zelsher.github.io/arrsa-systemes
```

Pas de signature GPG sur un dépôt OCI : l'empreinte dans l'index protège le paquet, TLS protège
l'index.

## Créer un système

La norme est `docs/systemes.md` d'ARRSA, et elle seule. [`modele/`](modele/LISEZMOI-MODELE.md) est
la base d'un nouveau système, que `outils/nouveau-systeme.py` copie en remplaçant code et nom ;
`outils/verifier.py <dossier> [--json]` juge un dépôt de système contre la norme (règles :
« Règles vérifiées » de la norme ; tests : `python3 -m unittest discover -s tests`). Le chemin
complet (trois tests, réservation du code dans le registre d'ARRSA, dépôt privé) : skill
`creer-systeme` d'ARRSA.

## Publier un système

1. Le dépôt du système a un manifeste `flatpak-builder` qui installe sa fiche
   (`/app/share/arrsa/systeme.toml`) : ARRSA y lit son code (Flatpak retire les clés `X-…`
   inconnues du `.desktop`).
2. Son intégration continue appelle [`publier.yml`](.github/workflows/publier.yml) (exemple en
   tête du fichier) : le Flatpak part en image privée sur `ghcr.io/zelsher/<paquet>`. Aucun secret.
3. Une fois, après la première publication : dans les réglages du paquet sur GitHub, « Manage
   Actions access » → `arrsa-systemes`, rôle Read ; puis `catalogue = true` dans le registre d'ARRSA
   (`registre-systemes.toml`, qui fait foi) et [`systemes.toml`](systemes.toml) régénéré par
   `outils/catalogue-depuis-registre.py ~/ARRSA/registre-systemes.toml` (jamais écrit à la main).

Le robot [`catalogue.yml`](.github/workflows/catalogue.yml) lit ces images toutes les 15 minutes
avec son jeton éphémère et republie l'index s'il a changé. Les systèmes n'écrivent jamais ici :
aucune clé durable ne peut modifier ce que les machines installent.

Outils : `outils/catalogue.py` (l'index depuis les images), `outils/catalogue-depuis-registre.py`
(la liste depuis le registre d'ARRSA), `outils/verifier.py` (la norme), `outils/nouveau-systeme.py`,
`outils/version.py` (la version du metainfo, montée par `publier.yml` à chaque publication à la main).
