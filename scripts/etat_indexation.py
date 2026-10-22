"""
État d'indexation Google de chaque page du sitemap (API Inspection d'URL de Search Console).

Affiche un tableau : pages indexées, pages en attente, avec la raison donnée par Google
et la date du dernier passage du robot. Les pages non indexées sont listées en premier :
ce sont celles à soumettre via « Demander l'indexation ».

Usage : python scripts/etat_indexation.py
Nécessite la clé du compte de service dans GSC_SERVICE_ACCOUNT_JSON.
"""
import json
import os
import re

SITE = "https://informatique-plouguerneau-antoine-conter.fr/"
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ETATS = {
    "Submitted and indexed": "Indexée",
    "Indexed, not submitted in sitemap": "Indexée",
    "Discovered - currently not indexed": "Détectée, pas encore explorée",
    "Crawled - currently not indexed": "Explorée, pas indexée",
    "URL is unknown to Google": "Inconnue de Google",
    "Duplicate, Google chose different canonical than user": "Doublon (autre page choisie)",
    "Page with redirect": "Redirection",
    "Excluded by 'noindex' tag": "Exclue (noindex)",
}


def main():
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession

    creds = service_account.Credentials.from_service_account_info(
        json.loads(os.environ["GSC_SERVICE_ACCOUNT_JSON"]),
        scopes=["https://www.googleapis.com/auth/webmasters.readonly"])
    s = AuthorizedSession(creds)
    with open(os.path.join(RACINE, "sitemap.xml"), encoding="utf-8") as f:
        urls = re.findall(r"<loc>\s*(.*?)\s*</loc>", f.read())

    lignes = []
    for u in urls:
        r = s.post("https://searchconsole.googleapis.com/v1/urlInspection/index:inspect",
                   json={"inspectionUrl": u, "siteUrl": SITE, "languageCode": "fr-FR"})
        if r.status_code != 200:
            lignes.append((u, "Erreur API", str(r.status_code), ""))
            continue
        res = r.json().get("inspectionResult", {}).get("indexStatusResult", {})
        etat = res.get("coverageState", "")
        crawl = (res.get("lastCrawlTime") or "")[:10]
        indexee = res.get("verdict") == "PASS"
        lignes.append((u, "Indexée" if indexee else "À indexer", ETATS.get(etat, etat), crawl))

    a_faire = [l for l in lignes if l[1] != "Indexée"]
    ok = [l for l in lignes if l[1] == "Indexée"]
    md = [f"## État d'indexation : {len(ok)} indexées sur {len(lignes)} pages", "",
          "| Page | Statut | Détail Google | Dernier passage |", "|---|---|---|---|"]
    for u, st, det, crawl in a_faire + ok:
        md.append(f"| {u.replace(SITE, '/')} | {'✅' if st == 'Indexée' else '⏳'} {st} | {det} | {crawl or 'jamais'} |")
    md += ["", "### À soumettre dans Search Console (Inspection de l'URL, puis Demander l'indexation)", ""]
    md += [f"- {u}" for u, *_ in a_faire] or ["- Rien, tout est indexé."]
    texte = "\n".join(md)
    print(texte)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as f:
            f.write(texte + "\n")


if __name__ == "__main__":
    main()
