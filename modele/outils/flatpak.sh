#!/bin/sh
# Construit et installe le Flatpak en local (essai avant de publier), sans rien télécharger d'autre
# que Flathub. La version qui compte vient du catalogue : désinstaller ensuite cette copie
# (flatpak uninstall --user org.arrsa.@Nom@).
set -eu
cd "$(dirname "$0")/.."
flatpak-builder --user --install --force-clean --install-deps-from=flathub construction paquet/org.arrsa.@Nom@.yml
