import requests
from bs4 import BeautifulSoup
import re
import logging
from config import HEADERS
import json

logger = logging.getLogger(__name__)

def scrape_myanimelist():
    url = "https://myanimelist.net/news"
    try:
        logger.info("Scraping MyAnimeList...")
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select(".news-unit.clearfix")
        
        news = []
        for a in articles:
            try:
                title = a.select_one(".title").text.strip()
                link = a.select_one("a")["href"]
                if not link.startswith('http'):
                    link = f'https://myanimelist.net{link}'
                
                img = a.select_one("img")
                image_url = img["src"] if img and "src" in img.attrs else None
                
                news.append({
                    "title": title,
                    "url": link,
                    "images": [image_url] if image_url else [],
                    "videos": [],
                    "youtube": [],
                    "source": "MyAnimeList"
                })
            except Exception as e:
                logger.error(f"Error processing MAL article: {str(e)}")
        
        logger.info(f"Found {len(news)} MyAnimeList articles")
        return news
    
    except Exception as e:
        logger.error(f"MyAnimeList scraping error: {str(e)}")
        return []

def scrape_crunchyroll():
    try:
        logger.info("Scraping Crunchyroll via API...")
        # API URL for Crunchyroll news
        api_url = "https://www.crunchyroll.com/content/v2/discover/news"
        
        # API parameters to get latest news
        params = {
            'n': 20,  # Number of articles to fetch
            'locale': 'en-US'
        }
        
        # Make API request
        response = requests.get(api_url, headers=HEADERS, params=params)
        if response.status_code != 200:
            logger.error(f"Crunchyroll API returned {response.status_code}")
            return []
        
        data = response.json()
        articles = []
        
        for item in data.get('data', []):
            try:
                # Get article ID and slug for URL
                article_id = item['id']
                slug = item.get('slug', 'news')
                
                # Construct article URL
                link = f"https://www.crunchyroll.com/news/{article_id}/{slug}"
                
                # Fetch article details
                article_url = f"https://www.crunchyroll.com/content/v2/cms/articles/{article_id}?locale=en-US"
                article_res = requests.get(article_url, headers=HEADERS)
                article_data = article_res.json().get('data', {})
                
                # Extract content
                content = article_data.get('body', '')
                
                # Extract images
                images = []
                for img in article_data.get('images', []):
                    if img.get('type') == 'hero' and img.get('url'):
                        images.append(img['url'])
                
                # Extract YouTube videos from content
                youtube_links = []
                if content:
                    soup = BeautifulSoup(content, 'html.parser')
                    for iframe in soup.find_all('iframe'):
                        src = iframe.get('src', '')
                        if 'youtube.com' in src or 'youtu.be' in src:
                            if src.startswith('//'):
                                src = 'https:' + src
                            youtube_links.append(src)
                
                articles.append({
                    "title": item.get('title', 'No Title'),
                    "url": link,
                    "content": content,
                    "images": images,
                    "videos": [],
                    "youtube": youtube_links,
                    "source": "Crunchyroll"
                })
            except Exception as e:
                logger.error(f"Error processing Crunchyroll article: {str(e)}")
        
        logger.info(f"Found {len(articles)} Crunchyroll articles")
        return articles
    
    except Exception as e:
        logger.error(f"Crunchyroll API scraping error: {str(e)}")
        return []
