import os
import re
from firecrawl import Firecrawl

app = Firecrawl(api_key=os.environ["FIRECRAWL_API_KEY"])


def search_books(query):

    search_url = (
        "https://z-lib.fm/s/"
        + query.replace(" ", "%20")
        + "/?languages%5B0%5D=french&extensions%5B0%5D=EPUB&order=date"
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

    book_urls = list(dict.fromkeys(book_urls))

    return book_urls[:5]
