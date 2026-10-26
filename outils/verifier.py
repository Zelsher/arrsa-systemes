#!/usr/bin/env python3
"""Vérifie qu'un dépôt de système suit la norme d'ARRSA (~/ARRSA/docs/systemes.md, « Règles vérifiées »).

    python3 outils/verifier.py <dossier> [--json] [--registre <registre-systemes.toml>] [--tests]

Déterministe et sans réseau : il lit les fichiers du dépôt (ceux que suit git, s'il y en a un) et
ses étiquettes locales. Code de sortie : 0 conforme, 1 au moins un écart, 2 mauvais appel. Chaque
écart nomme sa règle et le paragraphe de la norme qui la fonde.

Contrat lu par Horizon (ADR 0171 et 0173 d'ARRSA) : ne pas le changer sans le dire.
  --json     sort `[{"regle": "...", "fichier": "...", "message": "..."}]` (liste vide : conforme) ;
             `fichier` est relatif au dossier, "." pour le dépôt entier.
  --registre ajoute la règle registre-reserve (code réservé, même nom, même appli, même paquet).
  --tests    lance aussi les commandes de test de la fiche (règle tests-passent) : plus lent, et
             dépend de ce que ces commandes font ; sans lui, le vérificateur ne lance rien.

Bibliothèque standard seule (pas de YAML : le manifeste se lit ligne à ligne, comme le modèle l'écrit).
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tomllib
import xml.etree.ElementTree as ET
from dataclasses import asdict, dataclass
from pathlib import Path

NORME = "docs/systemes.md d'ARRSA"
CODE = re.compile(r"^S[1-9][0-9]{0,2}$")  # S0 est ARRSA, le seul socle : pas un dépôt de système
CODE_LIEN = re.compile(r"^S(0|[1-9][0-9]{0,2})$")
NOM = re.compile(r"^[A-Z][A-Za-z0-9]*$")
NATURES = ("instrument", "autonome")
ETATS = ("actif", "pause", "abandon", "absorbe")
VERSION = re.compile(r"^(\d+)\.(\d+)\.(\d+)$")
RUNTIMES = ("org.kde.Platform", "org.freedesktop.Platform", "org.gnome.Platform")
# Le socle d'une fenêtre : ces permissions-là n'ont pas à être commentées.
FENETRE = {"--share=ipc", "--socket=wayland", "--socket=fallback-x11", "--device=dri"}
LARGES = re.compile(r"^--filesystem=(home|host|host-os|host-etc|~)(/?)(:r[ow])?$")
EXCEPTION = "exception norme"
SOURCES = {".py", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".qml", ".c", ".cc", ".cpp", ".h",
           ".hpp", ".rs", ".go", ".java", ".kt", ".html", ".css", ".vue", ".svelte", ".sh"}
HORS_CODE = {"tests", "test", "paquet", ".github", "docs"}
EXCLUS = {".git", ".venv", "venv", "node_modules", "construction", ".flatpak-builder", "__pycache__"}


@dataclass
class Ecart:
    regle: str
    fichier: str
    message: str


class Verif:
    def __init__(self, dossier: Path) -> None:
        self.d = dossier
        self.ecarts: list[Ecart] = []

    def ecart(self, regle: str, fichier: str, message: str, section: str) -> None:
        self.ecarts.append(Ecart(regle, fichier, f"{message} ({NORME}, « {section} »)"))

    def lire(self, relatif: str) -> str | None:
        try:
            return (self.d / relatif).read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            return None


# --- fiche -------------------------------------------------------------------------------------

def plaque_de_la_decoration(texte: str) -> tuple[str, str] | None:
    """Ce que grave la décoration de KWin d'ARRSA (shell/decoration/fiche.cpp, lireFiche), recopié
    ici à l'identique : `cle = "valeur"` sur une ligne de la section [systeme], le reste ignoré."""
    cle_valeur = re.compile(r'^\s*([a-z_]+)\s*=\s*"([^"]*)"\s*(#.*)?$')
    section, nom, numero = "", "", ""
    for ligne in texte.split("\n"):
        ligne = ligne.strip()
        if ligne.startswith("["):
            section = ligne
            continue
        if section != "[systeme]":
            continue
        m = cle_valeur.match(ligne)
        if not m:
            continue
        if m.group(1) == "nom":
            nom = m.group(2).strip()
        elif m.group(1) == "code":
            c = re.match(r"^S(\d{1,3})$", m.group(2).strip())
            if c:
                numero = c.group(1)
    if not nom or not numero:
        return None
    return nom.upper(), f"SYSTEM {int(numero):02d}"


def verifier_fiche(v: Verif) -> dict | None:
    f, sec = "systeme.toml", "Fiche d'identité"
    texte = v.lire(f)
    if texte is None:
        v.ecart("fiche-lisible", f, "pas de fiche systeme.toml à la racine", sec)
        return None
    try:
        data = tomllib.loads(texte)
    except tomllib.TOMLDecodeError as exc:
        v.ecart("fiche-lisible", f, f"fiche illisible : {exc}", sec)
        return None
    s = data.get("systeme")
    if not isinstance(s, dict):
        v.ecart("fiche-lisible", f, "pas de section [systeme]", sec)
        return None
    code, nom = str(s.get("code") or ""), str(s.get("nom") or "").strip()
    if not CODE.match(code):
        v.ecart("fiche-plaque", f, f"code « {code} » : S1, S2… sans point (S0 est ARRSA)", sec)
    if not nom:
        v.ecart("fiche-plaque", f, "nom vide : la barre de titre n'aurait pas de plaque", sec)
    elif not NOM.match(nom):
        v.ecart("fiche-nom", f, f"nom « {nom} » : lettres et chiffres, une majuscule au début (org.arrsa.<Nom>)", sec)
    if CODE.match(code) and nom:
        attendu = (nom.upper(), f"SYSTEM {int(code[1:]):02d}")
        lu = plaque_de_la_decoration(texte)
        if lu != attendu:
            v.ecart("fiche-plaque", f, f"la décoration lirait {lu or 'aucune plaque'} au lieu de {attendu} : "
                    'code et nom en `cle = "valeur"` sur une ligne de [systeme]', "Apparence")
    nature = s.get("nature")
    if nature == "socle":
        v.ecart("fiche-nature", f, "nature « socle » : réservée à S0 ARRSA ; instrument ou autonome", sec)
    elif nature not in NATURES:
        v.ecart("fiche-nature", f, f"nature « {nature or ''} » : instrument ou autonome", sec)
    etat, absorbe = s.get("etat"), str(s.get("absorbe_par") or "")
    if etat not in ETATS:
        v.ecart("fiche-etat", f, f"état « {etat or ''} » : {' | '.join(ETATS)}", sec)
    elif (etat == "absorbe") != bool(absorbe) or (absorbe and not CODE_LIEN.match(absorbe)):
        v.ecart("fiche-etat", f, "absorbe_par : le code du système repreneur si et seulement si etat = absorbe", sec)
    if not str(s.get("but") or "").strip():
        v.ecart("fiche-champs", f, "but vide : une phrase", sec)
    if not re.match(r"^\d{4}-\d{2}-\d{2}$", str(s.get("naissance") or "")):
        v.ecart("fiche-champs", f, "naissance : une date AAAA-MM-JJ", sec)
    liens = data.get("liens", {})
    for cle in ("depend_de", "utilise"):
        valeur = liens.get(cle, []) if isinstance(liens, dict) else None
        if not isinstance(valeur, list) or any(not CODE_LIEN.match(str(c)) or c == code for c in valeur):
            v.ecart("fiche-liens", f, f"[liens] {cle} : une liste de codes d'autres systèmes (S0, S1…)", sec)
    tests = data.get("tests", {})
    commandes = tests.get("commandes") if isinstance(tests, dict) else None
    if not (isinstance(commandes, list) and commandes and all(isinstance(c, str) and c.strip() for c in commandes)):
        v.ecart("tests-declares", f, '[tests] commandes = ["…"] : au moins une commande de test', "Tests d'un système")
        commandes = None
    return {"code": code, "nom": nom, "commandes": commandes or []}


# --- code ------------------------------------------------------------------------------------

def fichiers_du_depot(d: Path) -> list[str]:
    """Les fichiers suivis par git (le reste n'est pas le système) ; sans git, tout sauf l'outillage."""
    if (d / ".git").exists():
        try:
            sortie = subprocess.run(["git", "-C", str(d), "ls-files", "-z"], capture_output=True, check=True).stdout
            return sorted(p for p in sortie.decode().split("\0") if p and (d / p).is_file())
        except (OSError, subprocess.CalledProcessError):
            pass
    return sorted(str(p.relative_to(d)) for p in d.rglob("*")
                  if p.is_file() and not EXCLUS & set(p.relative_to(d).parts))


def verifier_code(v: Verif, fiche: dict, fichiers: list[str]) -> None:
    sec = "Identité dans le code"
    id_appli = f"org.arrsa.{fiche['nom']}"
    litteral = re.compile(r"""["']""" + re.escape(id_appli) + r"""["']""")
    plaque = re.compile(r"""["'>]\s*SYSTEM \d{2}""")
    code = [p for p in fichiers if Path(p).suffix in SOURCES and not HORS_CODE & set(Path(p).parts[:1])]
    porteurs = []
    for p in code:
        texte = v.lire(p) or ""
        if litteral.search(texte):
            porteurs.append(p)
        if plaque.search(texte):
            v.ecart("apparence-une-plaque", p, "plaque « SYSTEM NN » dans le système : la barre de titre "
                    "d'ARRSA la porte déjà", "Apparence")
    if not porteurs:
        v.ecart("identite-un-seul-endroit", ".", f"« {id_appli} » n'est écrit nulle part dans le code", sec)
    elif len(porteurs) > 1:
        v.ecart("identite-un-seul-endroit", porteurs[1], f"« {id_appli} » écrit dans {len(porteurs)} fichiers "
                f"({', '.join(porteurs)}) : un seul endroit, les autres l'importent", sec)
    if not any(p.split("/")[0] in ("tests", "test") and "systeme.toml" in (v.lire(p) or "") for p in fichiers):
        v.ecart("identite-testee", "tests", "aucun test ne compare l'identité du code à systeme.toml", sec)


# --- paquet ----------------------------------------------------------------------------------

def bloc_finish_args(texte: str) -> list[tuple[str, str]]:
    """(permission, commentaire juste au-dessus) de chaque entrée de finish-args ; le commentaire
    d'un groupe d'entrées consécutives vaut pour tout le groupe, une ligne vide le clôt."""
    out: list[tuple[str, str]] = []
    dedans, commentaire, groupe = False, "", False
    for ligne in texte.split("\n"):
        if re.match(r"^finish-args:\s*$", ligne):
            dedans = True
            continue
        if not dedans:
            continue
        if ligne and not ligne[0].isspace() and not ligne.startswith("#"):
            break
        brut = ligne.strip()
        if not brut:
            commentaire, groupe = "", False
        elif brut.startswith("#"):
            commentaire = (commentaire if not groupe else "") + " " + brut.lstrip("# ")
            groupe = False
        elif brut.startswith("- "):
            out.append((brut[2:].split(" #")[0].strip().strip("'\""), commentaire.strip()))
            groupe = True
    return out


def sources_sans_empreinte(texte: str) -> list[str]:
    """Les sources téléchargées (`url:`) d'un manifeste YAML sans sha256 (archive, file) ni commit (git)."""
    lignes = texte.split("\n")
    retrait = lambda s: len(s) - len(s.lstrip(" "))  # noqa: E731
    fautes = []
    for i, ligne in enumerate(lignes):
        m = re.match(r"^(\s*)- (.*)$", ligne)
        if not m:
            continue
        niveau, corps = len(m.group(1)), [m.group(2)]
        for suite in lignes[i + 1:]:
            if suite.strip() and retrait(suite) <= niveau:
                break
            if retrait(suite) == niveau + 2:
                corps.append(suite.strip())
        cles = dict(c.split(":", 1) for c in corps if re.match(r"^[a-z0-9-]+:", c))
        genre = cles.get("type", "").strip()
        if "url" not in cles:
            continue
        if genre in ("archive", "file") and not cles.get("sha256", "").strip():
            fautes.append(cles["url"].strip())
        elif genre == "git" and not cles.get("commit", "").strip():
            fautes.append(cles["url"].strip())
    return fautes


def sources_json(objet) -> list[str]:
    fautes = []
    if isinstance(objet, dict):
        if "url" in objet and "type" in objet:
            if objet["type"] in ("archive", "file") and not objet.get("sha256"):
                fautes.append(str(objet["url"]))
            elif objet["type"] == "git" and not objet.get("commit"):
                fautes.append(str(objet["url"]))
        for valeur in objet.values():
            fautes += sources_json(valeur)
    elif isinstance(objet, list):
        for valeur in objet:
            fautes += sources_json(valeur)
    return fautes


def verifier_paquet(v: Verif, fiche: dict) -> str | None:
    sec = "Paquet Flatpak"
    id_appli = f"org.arrsa.{fiche['nom']}"
    f = f"paquet/{id_appli}.yml"
    texte = v.lire(f)
    if texte is None:
        v.ecart("paquet-manifeste", f, "pas de manifeste flatpak-builder", sec)
    else:
        if not re.search(rf"^id:\s*['\"]?{re.escape(id_appli)}['\"]?\s*$", texte, re.M):
            v.ecart("paquet-manifeste", f, f"id: doit valoir {id_appli}", sec)
        m = re.search(r"^runtime:\s*['\"]?([\w.]+)", texte, re.M)
        if not m or m.group(1) not in RUNTIMES:
            v.ecart("paquet-runtime", f, f"runtime de Flathub : {', '.join(RUNTIMES)}", sec)
        if "install -Dm644 systeme.toml -t /app/share/arrsa" not in texte:
            v.ecart("paquet-fiche-embarquee", f, "le paquet doit installer la fiche : "
                    "install -Dm644 systeme.toml -t /app/share/arrsa", sec)
        args = bloc_finish_args(texte)
        noms = [a for a, _ in args]
        if "--filesystem=xdg-data/themes/arrsa:ro" not in noms:
            v.ecart("paquet-norme-lecture-seule", f, "--filesystem=xdg-data/themes/arrsa:ro manque "
                    "(la norme d'apparence d'ARRSA)", "Apparence")
        for arg, commentaire in args:
            if "themes/arrsa" in arg and not arg.endswith(":ro"):
                v.ecart("paquet-norme-lecture-seule", f, f"{arg} : la norme d'apparence se lit en lecture seule", "Apparence")
            if ("api.sock" in arg or re.match(r"^--filesystem=xdg-run/arrsa/?(:r[ow])?$", arg)
                    or re.match(r"^--filesystem=(xdg-data|xdg-config|xdg-cache|xdg-state|~/\.local/share|~/\.config)/arrsa\b", arg)
                    or arg == "--talk-name=org.freedesktop.secrets"):
                v.ecart("paquet-portes", f, f"{arg} : un système passe par les portes d'ARRSA, jamais par "
                        "api.sock, ses données ni le trousseau entier", "Portes entre systèmes")
            if LARGES.match(arg) and EXCEPTION not in commentaire.lower():
                v.ecart("paquet-acces-larges", f, f"{arg} : accès large ; un dossier précis, ou une "
                        f"« {EXCEPTION} : <pourquoi> » dans le commentaire", sec)
            if arg not in FENETRE and not commentaire:
                v.ecart("paquet-permissions-commentees", f, f"{arg} sans commentaire qui dise pourquoi", sec)
        fautes = sources_sans_empreinte(texte)
        for m in re.finditer(r"^\s*- ([\w./-]+\.(json|ya?ml))\s*$", texte, re.M):
            inclus = (Path(f).parent / m.group(1)).as_posix()
            contenu = v.lire(inclus)
            if contenu is None:
                v.ecart("paquet-sha256", inclus, "module inclus introuvable", sec)
            elif m.group(2) == "json":
                try:
                    fautes += sources_json(json.loads(contenu))
                except ValueError:
                    v.ecart("paquet-sha256", inclus, "module inclus illisible", sec)
            else:
                fautes += sources_sans_empreinte(contenu)
        for url in fautes:
            v.ecart("paquet-sha256", f, f"{url} téléchargé sans empreinte (sha256, ou commit pour git)", sec)

    f = f"paquet/{id_appli}.desktop"
    bureau = v.lire(f)
    if bureau is None:
        v.ecart("paquet-desktop", f, "pas de lanceur .desktop", sec)
    else:
        if not re.search(rf"^StartupWMClass={re.escape(id_appli)}\s*$", bureau, re.M):
            v.ecart("paquet-desktop", f, f"StartupWMClass={id_appli} manque (relie la fenêtre à son lanceur)", sec)
        for cle in re.findall(r"^(X-[\w-]+)=", bureau, re.M):
            v.ecart("paquet-desktop", f, f"clé maison {cle} : Flatpak la retire à l'export", sec)

    f = f"paquet/{id_appli}.metainfo.xml"
    meta = v.lire(f)
    if meta is None:
        v.ecart("paquet-metainfo", f, "pas de metainfo (la version que montrent le hangar et Bazaar)", sec)
        return None
    try:
        racine = ET.fromstring(meta)
    except ET.ParseError as exc:
        v.ecart("paquet-metainfo", f, f"metainfo illisible : {exc}", sec)
        return None
    if (racine.findtext("id") or "").strip() != id_appli:
        v.ecart("paquet-metainfo", f, f"<id> doit valoir {id_appli}", sec)
    release = racine.find("releases/release")
    version = release.get("version", "") if release is not None else ""
    if not VERSION.match(version):
        v.ecart("paquet-metainfo", f, "<release version=\"X.Y.Z\"> manque (la plus récente en premier)", sec)
        return None
    return version


def verifier_publication(v: Verif, fiche: dict, version: str | None, registre_paquet: str | None) -> None:
    sec = "Publier"
    id_appli = f"org.arrsa.{fiche['nom']}"
    paquet = registre_paquet or f"systemes-{fiche['nom'].lower()}"
    f = ".github/workflows/publier.yml"
    texte = v.lire(f)
    if texte is None:
        v.ecart("publication-flux", f, "pas de flux de publication", sec)
    else:
        attendus = [
            (r"uses:\s*Zelsher/arrsa-systemes/\.github/workflows/publier\.yml@", "le flux commun d'arrsa-systemes"),
            (rf"manifeste:\s*paquet/{re.escape(id_appli)}\.yml\b", f"manifeste: paquet/{id_appli}.yml"),
            (rf"appli:\s*{re.escape(id_appli)}\s*[,}}\n]", f"appli: {id_appli}"),
            (rf"paquet:\s*{re.escape(paquet)}\s*[,}}\n]", f"paquet: {paquet}"),
        ]
        for motif, quoi in attendus:
            if not re.search(motif, texte + "\n"):
                v.ecart("publication-flux", f, f"{quoi} manque", sec)
    if version and (v.d / ".git").exists():
        try:
            sortie = subprocess.run(["git", "-C", str(v.d), "tag", "--list", "v*"],
                                    capture_output=True, text=True, check=True).stdout
        except (OSError, subprocess.CalledProcessError):
            sortie = ""
        meta = v.lire(f"paquet/{id_appli}.metainfo.xml") or ""
        publiees = set(re.findall(r'<release[^>]*\bversion="([^"]+)"', meta))
        etiquettes = [t[1:] for t in sortie.split() if VERSION.match(t[1:])]
        for t in etiquettes:
            if t not in publiees:
                v.ecart("version-etiquette", f"paquet/{id_appli}.metainfo.xml",
                        f"étiquette v{t} sans <release version=\"{t}\">", sec)
        cle = lambda x: tuple(int(n) for n in x.split("."))  # noqa: E731
        if etiquettes and cle(max(etiquettes, key=cle)) > cle(version):
            v.ecart("version-etiquette", f"paquet/{id_appli}.metainfo.xml",
                    f"<release> {version} plus vieille que l'étiquette v{max(etiquettes, key=cle)}", sec)


def verifier_depot(v: Verif) -> None:
    texte = v.lire("CLAUDE.md")
    if texte is None or "docs/systemes.md" not in texte:
        v.ecart("depot-claude-md", "CLAUDE.md", "CLAUDE.md doit renvoyer à la norme (docs/systemes.md d'ARRSA)",
                "Ce que le dépôt contient")


def verifier_registre(v: Verif, fiche: dict, registre: Path) -> str | None:
    sec = "Registre"
    try:
        data = tomllib.loads(registre.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as exc:
        v.ecart("registre-reserve", str(registre), f"registre illisible : {exc}", sec)
        return None
    code = fiche["code"]
    if code in data.get("retires", {}):
        v.ecart("registre-reserve", "systeme.toml", f"{code} est un code retiré", sec)
        return None
    entree = data.get(code)
    if not isinstance(entree, dict):
        v.ecart("registre-reserve", "systeme.toml", f"{code} n'est pas réservé dans {registre.name}", sec)
        return None
    if entree.get("nom") != fiche["nom"]:
        v.ecart("registre-reserve", "systeme.toml", f"le registre nomme {code} « {entree.get('nom')} »", sec)
    if entree.get("flatpak") != f"org.arrsa.{fiche['nom']}":
        v.ecart("registre-reserve", "systeme.toml", f"le registre donne l'appli « {entree.get('flatpak')} »", sec)
    return str(entree.get("paquet") or "") or None


def lancer_tests(v: Verif, commandes: list[str]) -> None:
    for commande in commandes:
        try:
            fait = subprocess.run(commande, shell=True, cwd=v.d, capture_output=True, text=True, timeout=1800)
        except subprocess.TimeoutExpired:
            v.ecart("tests-passent", "systeme.toml", f"« {commande} » : plus de 30 min", "Tests d'un système")
            continue
        if fait.returncode:
            fin = (fait.stdout + fait.stderr).strip().splitlines()[-1:] or [""]
            v.ecart("tests-passent", "systeme.toml", f"« {commande} » échoue ({fait.returncode}) : {fin[0][:200]}",
                    "Tests d'un système")


def verifier(dossier: Path, registre: Path | None = None, tests: bool = False) -> list[Ecart]:
    v = Verif(dossier)
    fiche = verifier_fiche(v)
    verifier_depot(v)
    if fiche is None or not NOM.match(fiche["nom"]):
        return v.ecarts  # sans nom sûr, ni appli ni paquet ne se déduisent
    paquet = verifier_registre(v, fiche, registre) if registre else None
    verifier_code(v, fiche, fichiers_du_depot(dossier))
    version = verifier_paquet(v, fiche)
    verifier_publication(v, fiche, version, paquet)
    if tests and fiche["commandes"]:
        lancer_tests(v, fiche["commandes"])
    return v.ecarts


def main() -> int:
    a = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    a.add_argument("dossier", type=Path)
    a.add_argument("--json", action="store_true", help='[{"regle", "fichier", "message"}] sur la sortie')
    a.add_argument("--registre", type=Path, help="registre-systemes.toml d'ARRSA (règle registre-reserve)")
    a.add_argument("--tests", action="store_true", help="lancer aussi les commandes de test de la fiche")
    o = a.parse_args()
    dossier = o.dossier.expanduser().resolve()
    if not dossier.is_dir():
        a.error(f"{dossier} n'est pas un dossier")
    ecarts = verifier(dossier, o.registre.expanduser() if o.registre else None, o.tests)
    if o.json:
        print(json.dumps([asdict(e) for e in ecarts], ensure_ascii=False, indent=2))
    else:
        for e in ecarts:
            print(f"{e.regle}  {e.fichier} : {e.message}")
        print(f"{dossier.name} : " + ("conforme" if not ecarts else f"{len(ecarts)} écart(s)"))
    return 1 if ecarts else 0


if __name__ == "__main__":
    sys.exit(main())
