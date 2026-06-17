import os
import re
from firecrawl import Firecrawl

app = Firecrawl(api_key=os.environ["FIRECRAWL_API_KEY"])


def search_books(query):

    search_url = (
        "https://z-lib.fm/s/"
        + query.replace(" ", "%20")
        + "/?languages%5B0%5D=french&languages%5B1%5D=english&extensions%5B0%5D=EPUB&order=date"
    )

    result = app.scrape(
        search_url,
        formats=["markdown"],
        max_age=0,
        only_main_content=True
    )

    markdown = result.markdown

    book_urls = re.findall(
        r'https://z-lib\.fm/book/[^\s)]+',
        markdown
    )

    book_urls = list(dict.fromkeys(book_urls))[:5]

    books = []

    for url in book_urls:

        try:

            page = app.scrape(
                url,
                formats=["markdown"],
                max_age=0,
                only_main_content=True
            )

            text = page.markdown

            # Titre
            title_match = re.search(r"# (.+)", text)
            title = (
                title_match.group(1).strip()
                if title_match
                else "Titre inconnu"
            )

            # Ignore les faux résultats
            if (
                title == "Titre inconnu"
                or "reset filters" in title.lower()
                or title.startswith('"')
            ):
                continue

            # Auteur
            author_match = re.search(r"_\[(.*?)\]", text)
            author = (
                author_match.group(1).strip()
                if author_match
                else "Auteur inconnu"
            )

            # Langue
            language_match = re.search(
                r"Language:\n\n(.*?)\n\nFile:",
                text,
                re.S
            )

            language = (
                language_match.group(1).strip()
                if language_match
                else "?"
            )

            # Couverture
            cover_match = re.search(
                r'!\[\]\((https://covers.*?)\)',
                text
            )

            cover = cover_match.group(1) if cover_match else ""

            # Lien téléchargement
            dl_match = re.search(
                r'\[epub.*?\]\((https://z-lib\.fm/dl/.*?)\)',
                text
            )

            dl_url = dl_match.group(1) if dl_match else url

            # Résumé
            desc_match = re.search(
                r"What’s the quality of the downloaded files\?\n\n(.*?)\n\nContent Type:",
                text,
                re.S
            )

            description = (
                desc_match.group(1).strip()[:1000]
                if desc_match
                else "Pas de résumé."
            )

            books.append({
                "title": title,
                "author": author,
                "language": language,
                "url": url,
                "cover": cover,
                "download": dl_url,
                "description": description
            })

        except Exception as e:
            print(e)

    return books
