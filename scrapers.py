import requests
from bs4 import BeautifulSoup
import re
import logging
import random
import time
from config import get_random_headers, REQUEST_TIMEOUT

logger = logging.getLogger(__name__)

def extract_content(element):
    """Extract text and media from content element"""
    content = []
    images = []
    videos = []
    youtube_links = []
    
    # Process all elements
    for elem in element.find_all(recursive=True):
        # Handle text content
        if elem.name in ['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6']:
            text = elem.get_text(strip=True)
            if text:  # Skip empty text
                content.append(text)
        
        # Handle images
        elif elem.name == 'img':
            img_src = elem.get('src') or elem.get('data-src')
            if img_src and not img_src.startswith('data:image'):
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                images.append(img_src)
        
        # Handle YouTube embeds
        elif elem.name == 'iframe' and elem.get('src'):
            src = elem['src']
            if 'youtube.com' in src or 'youtu.be' in src:
                if src.startswith('//'):
                    src = 'https:' + src
                youtube_links.append(src)
    
    return {
        'text': '\n\n'.join(content),
        'images': images,
        'videos': videos,
        'youtube': youtube_links
    }

def scrape_anime_corner():
    url = "https://animecorner.me/category/news/anime-news/"
    try:
        logger.info("Scraping Anime Corner...")
        headers = get_random_headers()
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(res.text, "html.parser")
        
        articles = []
        
        # Find news items - updated selector
        for item in soup.select('article.type-post'):
            try:
                # Extract title
                title_elem = item.select_one('h2.entry-title a') or item.select_one('h3.entry-title a')
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # Extract link
                link = title_elem['href']
                
                # Extract image
                img = item.select_one('img')
                image_url = img['src'] if img and 'src' in img.attrs else None
                if image_url and image_url.startswith('/'):
                    image_url = 'https://animecorner.me' + image_url
                
                # Get article content
                logger.info(f"Fetching article: {link}")
                article_res = requests.get(link, headers=headers, timeout=REQUEST_TIMEOUT)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                
                # Extract content - updated selector
                content_div = article_soup.select_one('div.entry-content') or article_soup.select_one('div.post-content')
                if content_div:
                    content_data = extract_content(content_div)
                else:
                    content_data = {'text': '', 'images': [], 'videos': [], 'youtube': []}
                
                # Add main image if exists
                if image_url and image_url not in content_data['images']:
                    content_data['images'].insert(0, image_url)
                
                articles.append({
                    "title": title,
                    "url": link,
                    "content": content_data['text'],
                    "images": content_data['images'],
                    "videos": content_data['videos'],
                    "youtube": content_data['youtube'],
                    "source": "Anime Corner"
                })
            except Exception as e:
                logger.error(f"Error processing Anime Corner article: {str(e)}")
        
        logger.info(f"Found {len(articles)} Anime Corner articles")
        return articles
    
    except Exception as e:
        logger.error(f"Anime Corner scraping error: {str(e)}")
        return []

def scrape_ann():
    url = "https://www.animenewsnetwork.com/"
    try:
        logger.info("Scraping Anime News Network...")
        headers = get_random_headers()
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        soup = BeautifulSoup(res.text, "html.parser")
        
        articles = []
        
        # Find news items - updated selector
        for item in soup.select('div.herald-box.news, div.herald-box.news-feature'):
            try:
                # Extract title
                title_elem = item.select_one('h2 a') or item.select_one('h3 a')
                if not title_elem:
                    continue
                title = title_elem.text.strip()
                
                # Extract link
                link = title_elem['href']
                if not link.startswith('http'):
                    link = f'https://www.animenewsnetwork.com{link}'
                
                # Extract image
                img = item.select_one('img')
                image_url = img['src'] if img and 'src' in img.attrs else None
                if image_url and image_url.startswith('/'):
                    image_url = 'https://www.animenewsnetwork.com' + image_url
                
                # Get article content
                logger.info(f"Fetching article: {link}")
                article_res = requests.get(link, headers=headers, timeout=REQUEST_TIMEOUT)
                article_soup = BeautifulSoup(article_res.text, "html.parser")
                
                # Extract content - updated selector
                content_div = article_soup.select_one('div#content-main') or article_soup.select_one('div.main-content')
                if content_div:
                    content_data = extract_content(content_div)
                else:
                    content_data = {'text': '', 'images': [], 'videos': [], 'youtube': []}
                
                # Add main image if exists
                if image_url and image_url not in content_data['images']:
                    content_data['images'].insert(0, image_url)
                
                articles.append({
                    "title": title,
                    "url": link,
                    "content": content_data['text'],
                    "images": content_data['images'],
                    "videos": content_data['videos'],
                    "youtube": content_data['youtube'],
                    "source": "Anime News Network"
                })
            except Exception as e:
                logger.error(f"Error processing ANN article: {str(e)}")
        
        logger.info(f"Found {len(articles)} ANN articles")
        return articles
    
    except Exception as e:
        logger.error(f"ANN scraping error: {str(e)}")
        return []
