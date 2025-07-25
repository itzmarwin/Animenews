# test_scrapers.py
from scrapers import scrape_crunchyroll, scrape_myanimelist
import logging

logging.basicConfig(level=logging.INFO)

print("Testing Crunchyroll...")
cr_articles = scrape_crunchyroll()
print(f"Found {len(cr_articles)} articles")
for article in cr_articles:
    print(f" - {article['title']}")

print("\nTesting MyAnimeList...")
mal_articles = scrape_myanimelist()
print(f"Found {len(mal_articles)} articles")
for article in mal_articles:
    print(f" - {article['title']}")
