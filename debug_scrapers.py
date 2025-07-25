import logging
from scrapers import scrape_crunchyroll, scrape_myanimelist

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def debug_crunchyroll():
    print("=== DEBUGGING CRUNCHYROLL ===")
    articles = scrape_crunchyroll()
    print(f"Found {len(articles)} articles")
    
    for i, article in enumerate(articles):
        print(f"\nArticle {i+1}: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Images: {len(article['images'])}")
        print(f"Videos: {len(article['videos'])}")
        print(f"YouTube: {len(article['youtube'])}")
        print("Content snippet:", article['content'][:100] + "...")

def debug_myanimelist():
    print("\n=== DEBUGGING MYANIMELIST ===")
    articles = scrape_myanimelist()
    print(f"Found {len(articles)} articles")
    
    for i, article in enumerate(articles):
        print(f"\nArticle {i+1}: {article['title']}")
        print(f"URL: {article['url']}")
        print(f"Images: {len(article['images'])}")
        print(f"Videos: {len(article['videos'])}")
        print(f"YouTube: {len(article['youtube'])}")
        print("Content snippet:", article['content'][:100] + "...")

if __name__ == '__main__':
    debug_crunchyroll()
    debug_myanimelist()
