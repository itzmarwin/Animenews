import requests
from bs4 import BeautifulSoup
import logging
import re
from config import HEADERS
import os

logger = logging.getLogger(__name__)

def save_debug_html(url, content, filename):
    """Save HTML content for debugging"""
    debug_dir = "debug_html"
    os.makedirs(debug_dir, exist_ok=True)
    path = os.path.join(debug_dir, filename)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(f"<!-- URL: {url} -->\n")
        f.write(content)
    logger.debug(f"Saved debug HTML: {path}")

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
        if elem.name == 'img':
            img_src = elem.get('src') or elem.get('data-src')
            if img_src and not img_src.startswith('data:image'):  # Skip data URIs
                if img_src.startswith('//'):
                    img_src = 'https:' + img_src
                elif img_src.startswith('/'):
                    img_src = 'https://www.crunchyroll.com' + img_src
                images.append(img_src)
        
        # Handle videos
        elif elem.name == 'video' and elem.get('src'):
            video_src = elem['src']
            if not video_src.startswith('data:'):
                if video_src.startswith('//'):
                    video_src = 'https:' + video_src
                videos.append(video_src)
        
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

def scrape_crunchyroll():
    url = 'https://www.crunchyroll.com/news'
    try:
        logger.info("Scraping Crunchyroll...")
        response = requests.get(url, headers=HEADERS)
        logger.info(f"Crunchyroll status: {response.status_code}")
        
        # Save HTML for debugging
        save_debug_html(url, response.text, "crunchyroll_main.html")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Try multiple selectors for news items
        news_items = soup.select('a.erc-browse-card')  # New selector
        if not news_items:
            news_items = soup.select('li.article-card')  # Old selector
        if not news_items:
            news_items = soup.select('div.article-card')  # Alternative
            
        logger.info(f"Found {len(news_items)} potential news items")
        
        for item in news_items[:5]:  # Just process first 5 for testing
            try:
                # Get title
                title_elem = item.select_one('h3.title') or item.select_one('h3.erc-browse-card__title')
                if not title_elem:
                    logger.debug("No title element found, skipping item")
                    continue
                    
                title = title_elem.text.strip()
                logger.debug(f"Processing: {title}")
                
                # Get link
                link = item.get('href')
                if not link:
                    logger.debug("No link found, skipping")
                    continue
                    
                if not link.startswith('http'):
                    link = f'https://www.crunchyroll.com{link}'
                
                # Skip non-news links
                if "/news/" not in link:
                    logger.debug(f"Skipping non-news link: {link}")
                    continue
                
                # Get full article content
                logger.debug(f"Fetching article: {link}")
                article_response = requests.get(link, headers=HEADERS)
                save_debug_html(link, article_response.text, f"crunchyroll_article_{len(articles)}.html")
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # Find content area
                content_div = article_soup.select_one('div.article-body')
                if not content_div:
                    content_div = article_soup.select_one('div.content')
                if not content_div:
                    content_div = article_soup.select_one('div.article-content')
                    
                if not content_div:
                    logger.warning(f"No content found for {link}")
                    continue
                    
                content_data = extract_content(content_div)
                
                # Get main image
                main_image = article_soup.select_one('div.article-hero img') or \
                            article_soup.select_one('img.article-hero__image')
                if main_image:
                    img_src = main_image.get('src') or main_image.get('data-src')
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
                    'source': 'Crunchyroll'
                })
                logger.info(f"Added article: {title}")
                
            except Exception as e:
                logger.error(f"Error processing Crunchyroll item: {str(e)}")
                continue
            
        return articles
    
    except Exception as e:
        logger.error(f"Crunchyroll scraping error: {str(e)}", exc_info=True)
        return []

def scrape_myanimelist():
    url = 'https://myanimelist.net/news'
    try:
        logger.info("Scraping MyAnimeList...")
        response = requests.get(url, headers=HEADERS)
        logger.info(f"MyAnimeList status: {response.status_code}")
        
        # Save HTML for debugging
        save_debug_html(url, response.text, "myanimelist_main.html")
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        # Find news items
        news_items = soup.select('div.news-unit')
        logger.info(f"Found {len(news_items)} news units")
        
        for item in news_items[:5]:  # Just process first 5 for testing
            try:
                title_elem = item.select_one('a.title')
                if not title_elem:
                    logger.debug("No title element found, skipping item")
                    continue
                    
                title = title_elem.text.strip()
                logger.debug(f"Processing: {title}")
                
                link = title_elem['href']
                if not link.startswith('http'):
                    link = f'https://myanimelist.net{link}'
                
                # Get full article content
                logger.debug(f"Fetching article: {link}")
                article_response = requests.get(link, headers=HEADERS)
                save_debug_html(link, article_response.text, f"myanimelist_article_{len(articles)}.html")
                article_soup = BeautifulSoup(article_response.text, 'html.parser')
                
                # Find content area
                content_div = article_soup.select_one('div.news-content')
                if not content_div:
                    content_div = article_soup.select_one('div#content > div:nth-child(2) > div:last-child')
                if not content_div:
                    content_div = article_soup.select_one('div.article-content')
                    
                if not content_div:
                    logger.warning(f"No content found for {link}")
                    continue
                    
                content_data = extract_content(content_div)
                
                # Get main image
                main_image = item.select_one('img.news-unit-image') or \
                            article_soup.select_one('div.news-unit-image img')
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
                logger.info(f"Added article: {title}")
                
            except Exception as e:
                logger.error(f"Error processing MyAnimeList item: {str(e)}")
                continue
            
        return articles
    
    except Exception as e:
        logger.error(f"MyAnimeList scraping error: {str(e)}", exc_info=True)
        return []
