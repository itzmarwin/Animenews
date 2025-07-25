import requests
from bs4 import BeautifulSoup
import re
import logging
import random
import time
from config import get_random_headers, PROXIES, REQUEST_TIMEOUT, DEBUG_MODE

logger = logging.getLogger(__name__)

def make_request(url, max_retries=3):
    """Make a request with retries and random delays"""
    for attempt in range(max_retries):
        try:
            headers = get_random_headers()
            # Use proxies only if defined in config
            proxies = PROXIES if 'PROXIES' in globals() and PROXIES else None
            
            response = requests.get(
                url, 
                headers=headers, 
                proxies=proxies, 
                timeout=REQUEST_TIMEOUT
            )
            response.raise_for_status()
            
            # Check for Cloudflare challenge
            if "cloudflare" in response.text.lower() and "challenge" in response.text.lower():
                raise Exception("Cloudflare challenge detected")
                
            return response
        except Exception as e:
            logger.warning(f"Request failed (attempt {attempt+1}/{max_retries}): {str(e)}")
            if attempt < max_retries - 1:
                # Exponential backoff with jitter
                delay = (2 ** attempt) + random.uniform(0, 1)
                time.sleep(delay)
    
    raise Exception(f"Failed to fetch {url} after {max_retries} attempts")

def scrape_myanimelist():
    url = "https://myanimelist.net/news"
    try:
        logger.info("Scraping MyAnimeList...")
        response = make_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find news items
        articles = soup.select("div.news-unit.clearfix")
        if not articles:
            articles = soup.select("div.news-unit")
            
        logger.debug(f"Found {len(articles)} news units")
        
        news = []
        for a in articles:
            try:
                # Extract title
                title_elem = a.select_one(".title")
                if not title_elem:
                    title_elem = a.select_one("p.title")
                title = title_elem.text.strip() if title_elem else "No title"
                
                # Extract link
                link_elem = a.select_one("a")
                link = link_elem["href"] if link_elem else None
                if link and not link.startswith('http'):
                    link = f'https://myanimelist.net{link}'
                
                # Extract image
                img = a.select_one("img")
                image_url = img["src"] if img and "src" in img.attrs else None
                if image_url and image_url.startswith('//'):
                    image_url = 'https:' + image_url
                
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
        response = make_request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Find news cards - using multiple selectors for reliability
        articles = soup.select("a.news-card__link")
        if not articles:
            articles = soup.select("a.erc-browse-card")
        if not articles:
            articles = soup.select("a[href*='/news/']")
            
        logger.debug(f"Found {len(articles)} potential articles")
        
        news = []
        for a in articles[:20]:  # Limit to 20 articles
            try:
                # Extract title
                title_tag = a.select_one(".news-card__title")
                if not title_tag:
                    title_tag = a.select_one(".erc-browse-card__title")
                if not title_tag:
                    title_tag = a.select_one("h3")
                title = title_tag.text.strip() if title_tag else "No title"
                
                # Get article link
                link = a["href"]
                if not link.startswith('http'):
                    link = f'https://www.crunchyroll.com{link}'
                
                # Skip non-news links
                if "/news/" not in link:
                    logger.debug(f"Skipping non-news link: {link}")
                    continue
                
                # Visit article page to get more details
                logger.debug(f"Fetching article: {link}")
                article_response = make_request(link)
                article_soup = BeautifulSoup(article_response.text, "html.parser")
                
                # Extract images
                images = []
                # Try multiple image sources
                og_image = article_soup.find("meta", property="og:image")
                if og_image and og_image.get("content"):
                    images.append(og_image["content"])
                
                # Try hero image
                hero_image = article_soup.select_one("img.article-hero__image")
                if hero_image and hero_image.get("src"):
                    img_src = hero_image["src"]
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    images.append(img_src)
                
                # Extract content text
                content_div = article_soup.select_one("div.article-body")
                if not content_div:
                    content_div = article_soup.select_one("div.content")
                content = content_div.get_text(strip=True) if content_div else ""
                
                # Extract YouTube videos
                youtube_links = []
                iframe = article_soup.find("iframe")
                if iframe and "youtube.com" in iframe.get("src", ""):
                    src = iframe["src"]
                    if src.startswith('//'):
                        src = 'https:' + src
                    youtube_links.append(src)
                
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
