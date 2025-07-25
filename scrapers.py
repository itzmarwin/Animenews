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

def scrape_crunchyroll():
    url = 'https://www.crunchyroll.com/news'
    try:
        response = requests.get(url, headers=HEADERS)
        logger.info(f"Crunchyroll status: {response.status_code}")
        
        # Check for blocking
        if response.status_code != 200:
            logger.error(f"Crunchyroll blocked with status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Updated selector for Crunchyroll
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
                
            # Get full article content
            try:
                article_response = requests.get(link, headers=HEADERS)
                article_soup = BeautifulSoup(article_response.content, 'html.parser')
                
                # Find content area - try multiple selectors
                content_div = article_soup.select_one('div.content') or \
                              article_soup.select_one('div.article-body') or \
                              article_soup.select_one('div.article-content')
                
                if not content_div:
                    logger.warning(f"No content found for {link}")
                    continue
                    
                content_data = extract_content(content_div)
                
                # Crunchyroll specific: get main image
                main_image = article_soup.select_one('img.article-hero__image') or \
                             article_soup.select_one('div.article-hero img') or \
                             article_soup.select_one('div.article-header img')
                
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
    
    except Exception as e:
        logger.error(f"Crunchyroll scraping error: {str(e)}")
        return []

def scrape_myanimelist():
    url = 'https://myanimelist.net/news'
    try:
        response = requests.get(url, headers=HEADERS)
        logger.info(f"MyAnimeList status: {response.status_code}")
        
        # Check for blocking
        if response.status_code != 200:
            logger.error(f"MyAnimeList blocked with status {response.status_code}")
            return []
        
        soup = BeautifulSoup(response.content, 'html.parser')
        articles = []
        
        # Updated selector for MyAnimeList
        for item in soup.select('div.news-unit'):
            title_elem = item.select_one('a.title')
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
                
                # Find content area - try multiple selectors
                content_div = article_soup.select_one('div.news-content') or \
                             article_soup.select_one('div#content') or \
                             article_soup.select_one('div.content')
                
                if not content_div:
                    logger.warning(f"No content found for {link}")
                    continue
                    
                content_data = extract_content(content_div)
                
                # MAL specific: get main image
                main_image = article_soup.select_one('img.news-unit-image') or \
                            article_soup.select_one('div.news-unit-image img') or \
                            article_soup.select_one('div.news-header img')
                
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
    
    except Exception as e:
        logger.error(f"MyAnimeList scraping error: {str(e)}")
        return []
