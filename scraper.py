import os
import re
import json
import time
import requests

from firecrawl import FirecrawlApp

SEARCH_URL = "https://z-lib.fm/s/?yearFrom=2026&languages%5B%5D=french&extensions%5B%5D=EPUB&order=date"

app = FirecrawlApp(api_key=os.environ["FIRECRAWL_API_KEY"])
WEBHOOK = os.environ["DISCORD_WEBHOOK"]

# Chargement des livres déjà vus
try:
    with open("seen_books.json", "r", encoding="utf-8") as f:
        seen_books = json.load(f)
except:
    seen_books = []

# Nombre de livres déjà vus d'affilée
already_seen_count = 0

# Scraping page nouveautés
result = app.scrape_url(SEARCH_URL)
markdown = result.markdown

# Extraction des liens /book/
book_urls = re.findall(r'https://z-lib\.fm/book/[^\s)]+', markdown)

# Suppression des doublons
book_urls = list(dict.fromkeys(book_urls))

print(f"{len(book_urls)} livres à analyser")

for url in book_urls:

    try:
        page = app.scrape_url(url)
        text = page.markdown

        # ------------------------
        # TITRE
        # ------------------------
        title_match = re.search(r'# (.+)', text)
        title = title_match.group(1).strip() if title_match else "Titre inconnu"

        # ------------------------
        # AUTEUR
        # ------------------------
        author_match = re.search(r'_\[(.*?)\]', text)
        author = author_match.group(1).strip() if author_match else "Auteur inconnu"

        # ------------------------
        # CLE UNIQUE
        # ------------------------
        book_key = (
            f"{title.lower().strip()}|"
            f"{author.lower().strip()}|"
            f"{url}"
        )

        # ------------------------
        # DEJA VU ?
        # ------------------------
        if book_key in seen_books:

            already_seen_count += 1

            print(f"Déjà vu : {title}")

            # Si 10 livres déjà vus d'affilée,
            # on considère qu'on est arrivé dans les anciennes nouveautés
            if already_seen_count >= 10:
                print("10 livres déjà vus d'affilée → arrêt")
                break

            continue

        already_seen_count = 0

        # ------------------------
        # COUVERTURE
        # ------------------------
        cover_match = re.search(
            r'!\[\]\((https://covers.*?)\)',
            text
        )

        cover = cover_match.group(1) if cover_match else ""

        # ------------------------
        # LIEN TELECHARGEMENT
        # ------------------------
        dl_match = re.search(
            r'\[epub.*?\]\((https://z-lib\.fm/dl/.*?)\)',
            text
        )

        dl_url = dl_match.group(1) if dl_match else url

        # ------------------------
        # RESUME
        # ------------------------
        desc_match = re.search(
            r'What’s the quality of the downloaded files\?\n\n(.*?)\n\nCategories:',
            text,
            re.S
        )

        description = (
            desc_match.group(1).strip()
            if desc_match
            else "Pas de résumé"
        )

        # Limite Discord
        if len(description) > 1500:
            description = description[:1500] + "..."

        # ------------------------
        # DISCORD
        # ------------------------
        payload = {
            "embeds": [
                {
                    "title": f"📚 {title}",
                    "description": (
                        f"✍ {author}\n\n"
                        f"{description}\n\n"
                        f"📥 {dl_url}"
                    ),
                    "color": 10181046,
                    "image": {
                        "url": cover
                    },
                    "footer": {
                        "text": "Détecté automatiquement"
                    }
                }
            ]
        }

        response = requests.post(WEBHOOK, json=payload)

        if response.status_code in [200, 204]:

            print(f"Posté : {title}")

            seen_books.append(book_key)

        else:

            print(f"Erreur Discord : {response.status_code}")

        # Petite pause pour éviter de bourriner
        time.sleep(1)

    except Exception as e:

        print(f"Erreur sur {url}")
        print(e)

# Sauvegarde
with open("seen_books.json", "w", encoding="utf-8") as f:
    json.dump(
        seen_books,
        f,
        indent=2,
        ensure_ascii=False
    )
