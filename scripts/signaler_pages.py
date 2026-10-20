"""
Signale les pages du site aux moteurs de recherche après chaque mise en ligne.

1. Google : renvoie le sitemap via l'API Search Console (méthode officielle).
   Nécessite le secret GitHub GSC_SERVICE_ACCOUNT_JSON (clé du compte de service).
   Sans ce secret, l'étape Google est simplement ignorée.
2. Bing, Yandex, Seznam : envoie toutes les URL du sitemap via IndexNow.

Usage local :  python scripts/signaler_pages.py [--dry-run]
"""
import json
import os
import re
import sys
import urllib.parse
import urllib.request

DOMAINE = "informatique-plouguerneau-antoine-conter.fr"
SITE = f"https://{DOMAINE}/"
SITEMAP = SITE + "sitemap.xml"
INDEXNOW_CLE = "33f6073a09f8585df2b849076003bda6"
RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DRY_RUN = "--dry-run" in sys.argv


def urls_du_sitemap():
    with open(os.path.join(RACINE, "sitemap.xml"), encoding="utf-8") as f:
        return re.findall(r"<loc>\s*(.*?)\s*</loc>", f.read())


def google():
    info = os.environ.get("GSC_SERVICE_ACCOUNT_JSON", "").strip()
    if not info:
        print("Google : secret GSC_SERVICE_ACCOUNT_JSON absent, étape ignorée.")
        return True
    from google.oauth2 import service_account
    from google.auth.transport.requests import AuthorizedSession

    creds = service_account.Credentials.from_service_account_info(
        json.loads(info), scopes=["https://www.googleapis.com/auth/webmasters"])
    session = AuthorizedSession(creds)

    # Propriété Search Console : domaine ou préfixe d'URL, selon ce qui a été créé.
    candidats = [os.environ.get("GSC_SITE", "").strip()] if os.environ.get("GSC_SITE") else []
    candidats += [f"sc-domain:{DOMAINE}", SITE]
    for site in candidats:
        url = ("https://www.googleapis.com/webmasters/v3/sites/"
               f"{urllib.parse.quote(site, safe='')}/sitemaps/{urllib.parse.quote(SITEMAP, safe='')}")
        if DRY_RUN:
            print(f"Google (simulation) : PUT {url}")
            return True
        r = session.put(url)
        if r.status_code in (200, 204):
            print(f"Google : sitemap renvoyé pour la propriété {site}")
            return True
        print(f"Google : propriété {site} refusée ({r.status_code}) {r.text[:200]}")
    print("Google : échec. Vérifie que l'email du compte de service est propriétaire dans Search Console.")
    return False


def indexnow(urls):
    corps = json.dumps({
        "host": DOMAINE,
        "key": INDEXNOW_CLE,
        "keyLocation": f"{SITE}{INDEXNOW_CLE}.txt",
        "urlList": urls,
    }).encode("utf-8")
    if DRY_RUN:
        print(f"IndexNow (simulation) : {len(urls)} URL")
        return True
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=corps, method="POST",
                                 headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            print(f"IndexNow : {len(urls)} URL envoyées (réponse {r.status})")
            return True
    except urllib.error.HTTPError as e:
        print(f"IndexNow : erreur {e.code} {e.read()[:200]!r}")
        return False


if __name__ == "__main__":
    urls = urls_du_sitemap()
    print(f"{len(urls)} URL trouvées dans le sitemap")
    ok_google = google()
    ok_indexnow = indexnow(urls)
    sys.exit(0 if (ok_google and ok_indexnow) else 1)
