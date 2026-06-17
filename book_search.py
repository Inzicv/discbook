import os
import re
from firecrawl import Firecrawl

app = Firecrawl(api_key=os.environ["FIRECRAWL_API_KEY"])

ALLOWED_LANGUAGES = ["French", "English"]


def search_books(query):

    search_url = (
        "https://z-lib.fm/s/"
        + query.replace(" ", "%20")
        + "/?extensions%5B0%5D=EPUB&order=date"
    )

    result = app.scrape(
        search_url,
        formats=["markdown"],
        max_age=0,
        only_main_content=True
    )

    markdown = result.markdown

    matches = re.findall(
        r'\[(.*?)\]\((https://z-lib\.fm/book/[^\)]+)\).*?Author:\s*(.*?)\n.*?Language:\s*(.*?)\n',
        markdown,
        re.S
    )

    books = []

    for title, url, author, language in matches:

        language = language.strip()

        if language not in ALLOWED_LANGUAGES:
            continue

        books.append({
            "title": title.strip(),
            "author": author.strip(),
            "language": language,
            "url": url
        })

    # suppression des doublons
    uniques = []

    for book in books:
        if book not in uniques:
            uniques.append(book)

    return uniques[:5]
