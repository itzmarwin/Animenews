import requests
from bs4 import BeautifulSoup
import re
import logging
import random
import time
from config import get_random_headers, REQUEST_TIMEOUT, SELENIUM_HEADLESS, USER_AGENTS  # Added USER_AGENTS import
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

logger = logging.getLogger(__name__)

def scrape_myanimelist():
    url = "https://myanimelist.net/news"
    try:
        logger.info("Scraping MyAnimeList...")
        headers = get_random_headers()
        res = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
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
    url = "https://www.crunchyroll.com/news"
    try:
        logger.info("Initializing Selenium for Crunchyroll...")
        
        # Configure Chrome options
        chrome_options = Options()
        chrome_options.binary_location = "/usr/bin/google-chrome"
        if SELENIUM_HEADLESS:
            chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument(f"user-agent={random.choice(USER_AGENTS)}")
        chrome_options.add_argument("--window-size=1920,1080")
        
        # Initialize WebDriver
        driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=chrome_options
        )
        
        try:
            logger.info(f"Loading Crunchyroll news page: {url}")
            driver.get(url)
            
            # Wait for the page to load completely
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            
            # Wait for any article container to appear (more generic)
            WebDriverWait(driver, 30).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "a[href*='/news/']"))
            )
            
            # Scroll to load all content
            logger.info("Scrolling to load all articles...")
            last_height = driver.execute_script("return document.body.scrollHeight")
            while True:
                driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                time.sleep(3)  # Wait longer to load
                new_height = driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height
            
            # Get all news links
            news_links = []
            for link in driver.find_elements(By.CSS_SELECTOR, "a[href*='/news/']"):
                href = link.get_attribute("href")
                if href and href not in news_links:
                    news_links.append(href)
            
            logger.info(f"Found {len(news_links)} Crunchyroll news links")
            
            news = []
            for link in news_links[:10]:  # Process first 10 articles
                try:
                    # Visit article page
                    logger.info(f"Fetching article: {link}")
                    driver.get(link)
                    
                    # Wait for article content to load
                    WebDriverWait(driver, 20).until(
                        EC.presence_of_element_located((By.CSS_SELECTOR, "h1, h2, h3, div.article-body, div.content"))
                    )
                    
                    # Get page source
                    article_html = driver.page_source
                    article_soup = BeautifulSoup(article_html, "html.parser")
                    
                    # Extract title - try multiple selectors
                    title = "No title"
                    for selector in ["h1", "h2", "h3"]:
                        title_elem = article_soup.select_one(selector)
                        if title_elem:
                            title = title_elem.text.strip()
                            break
                    
                    # Extract images
                    images = []
                    # Method 1: Open Graph image
                    og_image = article_soup.find("meta", property="og:image")
                    if og_image and og_image.get("content"):
                        images.append(og_image["content"])
                    
                    # Method 2: Any image in content
                    for img in article_soup.select("img"):
                        src = img.get("src") or img.get("data-src")
                        if src and "crunchyroll" in src and not src.startswith("data:image"):
                            if src.startswith("//"):
                                src = "https:" + src
                            images.append(src)
                    
                    # Extract content text
                    content = ""
                    content_div = article_soup.select_one("div.article-body, div.content")
                    if content_div:
                        # Remove unwanted elements
                        for element in content_div.select("script, style, iframe"):
                            element.decompose()
                        content = content_div.get_text(strip=True, separator='\n')
                    
                    # Extract YouTube videos
                    youtube_links = []
                    for iframe in article_soup.select("iframe"):
                        src = iframe.get("src", "")
                        if 'youtube.com' in src or 'youtu.be' in src:
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
            
            logger.info(f"Processed {len(news)} Crunchyroll articles")
            return news
        finally:
            driver.quit()
    except Exception as e:
        logger.error(f"Crunchyroll scraping error: {str(e)}")
        return []
