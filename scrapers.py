import requests
from bs4 import BeautifulSoup
import logging
import re
from config import HEADERS

logger = logging.getLogger(__name__)

def extract_content(element):
    """Extract text and media from content element"""
    content = []
    images = []
    videos = []
    youtube_links = []
    
    # Process all elements
    for elem in element.find_all(recursive=True):
        if elem.name == 'p':
            text = elem.get_text(strip=True)
            if text:  # Skip empty paragraphs
                content.append(text)
        elif elem.name == 'img' and elem.get('src'):
            img_src = elem['src']
            if not img_src.startswith('data:image'):  # Skip data URIs
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                images.append(img_src)
        elif elem.name == 'video' and elem.get('src'):
            video_src = elem['src']
            if not video_src.startswith('data:'):
                if video_src.startswith('//'):
                    video_src = 'https:' + video_src
                videos.append(video_src)
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

# Updated Crunchyroll scraper
def scrape_crunchyroll():
    url = 'https://www.crunchyroll.com/news'
    try:
        response = requests.get(url, headers=HEADERS)
        logger.info(f"Crunchyroll status: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # New selector - get all news cards
        for item in soup.select('a.erc-browse-card'):
            title_elem = item.select_one('h3.erc-browse-card__title')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            link = item['href']
            if not link.startswith('http'):
                link = f'https://www.crunchyroll.com{link}'
                
            # Skip non-article links
            if "/news/" not in link:
                continue
                
            # Get full article content
            try:
                article_response = requests.get(link, headers=HEADERS)
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # New content selectors
                content_div = article_soup.select_one('div.article-body')
                if not content_div:
                    content_div = article_soup.select_one('div.content')
                    
                if not content_div:
                    logger.warning(f"No content found for {link}")
                    continue
                    
                content_data = extract_content(content_div)
                
                # Get main image
                main_image = article_soup.select_one('div.article-hero img')
                if main_image and main_image.get('src'):
                    img_src = main_image['src']
                    if img_src.startswith('//'):
                        img_src = 'https:' + img_src
                    content_data['images'].insert(0, img_src)
                
                articles.append({
                    'title': title,
                    'url': link,
                    'content': content_data['text'],
                    'images': content_data['images'],
                    'videos': content_data['videos'],
                    'youtube': content_data['youtube'],
                    'source': 'Crunchyroll'
                })
            except Exception as e:
                logger.error(f"Error scraping Crunchyroll article: {str(e)}")
                continue
            
        return articles
    # ... error handling ...
    
    except Exception as e:
        logger.error(f"Crunchyroll scraping error: {str(e)}")
        return []

# Updated MyAnimeList scraper
def scrape_myanimelist():
    url = 'https://myanimelist.net/news'
    try:
        response = requests.get(url, headers=HEADERS)
        logger.info(f"MyAnimeList status: {response.status_code}")
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # New selector - get all news units
        for item in soup.select('div.news-unit.clearfix'):
            title_elem = item.select_one('p.title a')
            if not title_elem:
                continue
                
            title = title_elem.text.strip()
            link = title_elem['href']
            if not link.startswith('http'):
                link = f'https://myanimelist.net{link}'
                
            # Get full article content
            try:
                article_response = requests.get(link, headers=HEADERS)
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # New content selector
                content_div = article_soup.select_one('div.news-content')
                if not content_div:
                    logger.warning(f"No content found for {link}")
                    continue
                    
                content_data = extract_content(content_div)
                
                # Get main image
                main_image = item.select_one('div.thumb a img')
                if main_image:
                    img_src = main_image.get('data-src') or main_image.get('src')
                    if img_src:
                        if img_src.startswith('//'):
                            img_src = 'https:' + img_src
                        content_data['images'].insert(0, img_src)
                
                articles.append({
                    'title': title,
                    'url': link,
                    'content': content_data['text'],
                    'images': content_data['images'],
                    'videos': content_data['videos'],
                    'youtube': content_data['youtube'],
                    'source': 'MyAnimeList'
                })
            except Exception as e:
                logger.error(f"Error scraping MyAnimeList article: {str(e)}")
                continue
            
        return articles
    # ... error handling ...
    
    except Exception as e:
        logger.error(f"MyAnimeList scraping error: {str(e)}")
        return []
