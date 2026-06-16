import os
import re
import json
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

# Scraping page nouveautés
result = app.scrape_url(SEARCH_URL)
markdown = result.markdown

# Extraction des liens /book/
book_urls = re.findall(r'https://z-lib\.fm/book/[^\s)]+', markdown)

# Suppression doublons
book_urls = list(dict.fromkeys(book_urls))

# Premier lancement = seulement 10 livres
if len(seen_books) == 0:
    new_books = book_urls[:10]
else:
    new_books = [url for url in book_urls if url not in seen_books]

print(f"{len(new_books)} nouveaux livres trouvés")

for url in new_books:

    try:
        page = app.scrape_url(url)
        text = page.markdown

        # Titre
        title_match = re.search(r'# (.+)', text)
        title = title_match.group(1).strip() if title_match else "Titre inconnu"

        # Auteur
        author_match = re.search(r'_\[(.*?)\]', text)
        author = author_match.group(1).strip() if author_match else "Auteur inconnu"

        # Image couverture
        cover_match = re.search(r'!\[\]\((https://covers.*?)\)', text)
        cover = cover_match.group(1) if cover_match else ""

        # Lien téléchargement
        dl_match = re.search(r'\[epub.*?\]\((https://z-lib\.fm/dl/.*?)\)', text)
        dl_url = dl_match.group(1) if dl_match else url

        # Résumé
        desc_match = re.search(
            r'What’s the quality of the downloaded files\?\n\n(.*?)\n\nCategories:',
            text,
            re.S
        )

        description = desc_match.group(1).strip() if desc_match else "Pas de résumé"

        payload = {
            "embeds": [{
                "title": f"📚 {title}",
                "description": f"✍ {author}\n\n{description}\n\n📥 {dl_url}",
                "image": {
                    "url": cover
                }
            }]
        }

        requests.post(WEBHOOK, json=payload)

        seen_books.append(url)

    except Exception as e:
        print(e)

with open("seen_books.json", "w", encoding="utf-8") as f:
    json.dump(seen_books, f, indent=2, ensure_ascii=False)
