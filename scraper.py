from firecrawl import FirecrawlApp
import os

SEARCH_URL = "https://z-lib.fm/s/?yearFrom=2026&languages%5B%5D=french&extensions%5B%5D=EPUB&order=date"

app = FirecrawlApp(
    api_key=os.environ["FIRECRAWL_API_KEY"]
)

result = app.scrape_url(SEARCH_URL)

print(result)
