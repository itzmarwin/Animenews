import logging
from scrapers import scrape_crunchyroll, scrape_myanimelist

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_scraping():
    print("===== DEBUGGING CRUNCHYROLL SCRAPER =====")
    cr_articles = scrape_crunchyroll()
    print(f"\nFound {len(cr_articles)} Crunchyroll articles")
    for i, article in enumerate(cr_articles):
        print(f"\nArticle {i+1}: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Images: {len(article['images'])}")
        print(f"Videos: {len(article['videos'])}")
        print(f"YouTube: {len(article['youtube'])}")
        print("Content snippet:", article['content'][:100] + "...")
    
    print("\n===== DEBUGGING MYANIMELIST SCRAPER =====")
    mal_articles = scrape_myanimelist()
    print(f"\nFound {len(mal_articles)} MyAnimeList articles")
    for i, article in enumerate(mal_articles):
        print(f"\nArticle {i+1}: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Images: {len(article['images'])}")
        print(f"Videos: {len(article['videos'])}")
        print(f"YouTube: {len(article['youtube'])}")
        print("Content snippet:", article['content'][:100] + "...")
    
    print("\nDebug HTML files saved in 'debug_html' directory")

if __name__ == '__main__':
    debug_scraping()
