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
    url = 'https://www.crunchyroll.com/news'
    try:
        response = requests.get(url, headers=HEADERS, timeout=10)
        logger.info(f"Crunchyroll status: {response.status_code}")
        
        if response.status_code != 200:
            logger.error(f"Crunchyroll blocked with status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        for item in soup.select('div.article-card'):
            title_elem = item.select_one('h3.title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            link_elem = item.select_one('a')
            if not link_elem:
                continue
                
            link = link_elem['href']
            if not link.startswith('http'):
                link = f'https://www.crunchyroll.com{link}'
            
            try:
                article_response = requests.get(link, headers=HEADERS, timeout=10)
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                content_div = article_soup.select_one('div.content') or \
                              article_soup.select_one('div.article-body') or \
                              article_soup.select_one('div.article-content')
                
                if not content_div:
                    logger.warning(f"No content found for {link}")
                    continue
                
                # Simple text extraction
                content = '\n\n'.join(p.get_text(strip=True) for p in content_div.find_all('p') if p.get_text(strip=True))
                
                # Image
                images = []
                main_img = article_soup.select_one('img.article-hero__image') or \
                           article_soup.select_one('div.article-hero img') or \
                           article_soup.select_one('div.article-header img')
                
                if main_img and main_img.get('src'):
                    img_src = main_img['src']
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    images.append(img_src)
                
                articles.append({
                    'title': title,
                    'url': link,
                    'content': content,
                    'images': images,
                    'videos': [],
                    'youtube': [],
                    'source': 'Crunchyroll'
                })
            except Exception as e:
                logger.error(f"Error scraping Crunchyroll article: {str(e)}")
                continue
        
        logger.info(f"Found {len(articles)} Crunchyroll articles")
        return articles
    
    except Exception as e:
        logger.error(f"Crunchyroll scraping error: {str(e)}")
        return []
