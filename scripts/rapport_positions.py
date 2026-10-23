"""
Rapport des positions Google par commune, depuis Search Console (28 derniers jours).

Pour chaque commune : impressions, clics, position moyenne, meilleure requête,
et la page du site qui ressort. Le tableau s'affiche dans le résumé du workflow GitHub.

Usage : python scripts/rapport_positions.py [nb_jours]
Nécessite la clé du compte de service dans GSC_SERVICE_ACCOUNT_JSON.
"""
import datetime as dt
import json
import os
import sys
import unicodedata
import urllib.parse

SITE = "https://informatique-plouguerneau-antoine-conter.fr/"
COMMUNES = [
    # Pays des Abers et Côte des Légendes
    "Plouguerneau", "Lannilis", "Landéda", "Lesneven", "Le Folgoët", "Saint-Pabu",
    "Kerlouan", "Guissény", "Kernilis", "Tréglonou", "Loc-Brévalaire",
    # Entre les Abers et Brest
    "Plabennec", "Bourg-Blanc", "Kersaint-Plabennec", "Le Drennec", "Coat-Méal",
    "Plouvien", "Plouguin", "Gouesnou", "Guipavas", "Bohars", "Milizac",
    # Couronne de Brest et Iroise
    "Brest", "Plouzané", "Guilers", "Le Relecq-Kerhuon", "Plougastel", "Saint-Renan",
    "Locmaria-Plouzané", "Plougonvelin", "Le Conquet", "Trébabu",
    # Iroise nord, Landerneau, Léon
    "Ploudalmézeau", "Lampaul-Ploudalmézeau", "Plouarzel", "Brélès", "Landerneau",
    "Ploudaniel", "Goulven", "Plouider", "Plounévez-Lochrist", "Landivisiau",
    "Brignogan", "Saint-Frégant",
]


def norm(s):
    s = unicodedata.normalize("NFKD", s.lower()).encode("ascii", "ignore").decode()
    return s.replace("-", " ").replace("'", " ")


def main():
    jours = int(sys.argv[1]) if len(sys.argv) > 1 else 28
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession

    creds = service_account.Credentials.from_service_account_info(
        json.loads(os.environ["GSC_SERVICE_ACCOUNT_JSON"]),
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    s = AuthorizedSession(creds)
    fin = dt.date.today() - dt.timedelta(days=2)  # Search Console a ~2 jours de retard
    debut = fin - dt.timedelta(days=jours)
    url = ("https://www.googleapis.com/webmasters/v3/sites/"
           f"{urllib.parse.quote(SITE, safe='')}/searchAnalytics/query")
    r = s.post(url, json={"startDate": str(debut), "endDate": str(fin),
                          "dimensions": ["query", "page"], "rowLimit": 25000})
    r.raise_for_status()
    rows = r.json().get("rows", [])

    lignes = []
    for c in COMMUNES:
        nc = norm(c)
        sel = [x for x in rows if nc in norm(x["keys"][0])]
        imp = sum(x["impressions"] for x in sel)
        clics = sum(x["clicks"] for x in sel)
        pos = (sum(x["position"] * x["impressions"] for x in sel) / imp) if imp else None
        best = max(sel, key=lambda x: x["impressions"]) if sel else None
        lignes.append((c, imp, clics, pos,
                       best["keys"][0] if best else "",
                       best["keys"][1].replace(SITE, "/") if best else ""))

    titre = f"Positions Google par commune, du {debut:%d/%m/%Y} au {fin:%d/%m/%Y}"
    md = [f"## {titre}", "",
          "| Commune | Impressions | Clics | Position moyenne | Requête principale | Page |",
          "|---|---:|---:|---:|---|---|"]
    for c, imp, clics, pos, q, p in lignes:
        md.append(f"| {c} | {imp} | {clics} | {pos:.1f} | {q} | {p} |" if imp
                  else f"| {c} | 0 | 0 | non classé | | |")
    md += ["", "Position moyenne : 1 à 10 = première page Google, 11 à 20 = deuxième page.",
           "« non classé » : aucune recherche contenant la commune n'a encore affiché le site."]
    texte = "\n".join(md)
    print(texte)
    resume = os.environ.get("GITHUB_STEP_SUMMARY")
    if resume:
        with open(resume, "a", encoding="utf-8") as f:
            f.write(texte + "\n")


if __name__ == "__main__":
    main()
