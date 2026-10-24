"""@CODE@ @Nom@ : @BUT@

L'identité en un seul endroit du code (la fiche `systeme.toml` du dépôt n'est pas lue à
l'exécution) ; tests/test_identite.py vérifie qu'elle suit la fiche. La plaque « @NOM@ / SYSTEM NN »
de la barre de titre, c'est ARRSA qui la dessine (depuis la fiche du Flatpak) : rien à dessiner ici.
"""
CODE, NOM = "@CODE@", "@Nom@"
ID_APPLI = "org.arrsa.@Nom@"  # identifiant d'appli : Flatpak, .desktop, D-Bus, plaque d'ARRSA
