"""Point d'entrée : `python -m @nom@` (dans le Flatpak : la commande `@nom@`)."""
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QColor, QFont, QPalette
from PySide6.QtWidgets import QApplication, QLabel, QMainWindow

from . import ID_APPLI, NOM, norme


def palette(n: dict) -> QPalette:
    """Les couleurs de la session sur les rôles de Qt (le style Kvantum d'ARRSA n'entre pas dans
    un Flatpak sans son extension : les couleurs, elles, viennent de la norme)."""
    c = {k: QColor(v) for k, v in n["couleur"].items()}
    p = QPalette()
    for role, cle in ((QPalette.Window, "surface"), (QPalette.Base, "fond"), (QPalette.AlternateBase, "surface-2"),
                      (QPalette.Button, "surface-2"), (QPalette.Text, "texte"), (QPalette.WindowText, "texte"),
                      (QPalette.ButtonText, "texte"), (QPalette.PlaceholderText, "texte-attenue"),
                      (QPalette.Highlight, "accent"), (QPalette.HighlightedText, "texte")):
        p.setColor(role, c[cle])
    return p


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName(NOM)
    app.setDesktopFileName(ID_APPLI)  # relie la fenêtre à son .desktop : icône, et plaque d'ARRSA
    n = norme.lire()
    app.setPalette(palette(n))
    app.setFont(QFont(n["police"]["principale"], 10))
    fenetre = QMainWindow()
    fenetre.setWindowTitle(NOM)
    # La zone de travail est opaque (fond « Base ») ; seules les barres et la barre latérale sont
    # translucides sur ARRSA OS (norme des fenêtres, « Translucidité »).
    contenu = QLabel(f"{NOM} : à construire.")
    contenu.setAlignment(Qt.AlignCenter)
    contenu.setAutoFillBackground(True)
    contenu.setBackgroundRole(QPalette.Base)
    fenetre.setCentralWidget(contenu)
    fenetre.resize(960, 640)
    fenetre.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
