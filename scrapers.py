import requests
from bs4 import BeautifulSoup
import re
import logging
from config import HEADERS

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
                
                # Add to results
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
    url = "https://www.crunchyroll.com/news"
    try:
        logger.info("Scraping Crunchyroll...")
        res = requests.get(url, headers=HEADERS)
        soup = BeautifulSoup(res.text, "html.parser")
        articles = soup.select("a.news-card__link")
        
        news = []
        for a in articles:
            try:
                # Extract basic info from main page
                title_tag = a.select_one(".news-card__title")
                title = title_tag.text.strip() if title_tag else "No title"
                link = "https://www.crunchyroll.com" + a["href"]
                
                # Visit article page to get more details
                article_res = requests.get(link, headers=HEADERS)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                
                # Extract images
                images = []
                og_image = article_soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    images.append(og_image["content"])
                
                # Extract YouTube videos
                youtube_links = []
                iframe = article_soup.find("iframe")
                if iframe and "youtube.com" in iframe.get("src", ""):
                    src = iframe["src"]
                    if src.startswith('//'):
                        src = 'https:' + src
                    youtube_links.append(src)
                
                # Extract content text
                content_div = article_soup.select_one("div.article-body")
                content = content_div.get_text(strip=True) if content_div else ""
                
                # Add to results
                news.append({
                    "title": title,
                    "url": link,
                    "content": content,
                    "images": images,
                    "videos": [],
                    "youtube": youtube_links,
                    "source": "Crunchyroll"
                })
            except Exception as e:
                logger.error(f"Error processing Crunchyroll article: {str(e)}")
        
        logger.info(f"Found {len(news)} Crunchyroll articles")
        return news
    
    except Exception as e:
        logger.error(f"Crunchyroll scraping error: {str(e)}")
        return []
