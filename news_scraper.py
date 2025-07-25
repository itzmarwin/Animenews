# news_scraper.py

import requests
from bs4 import BeautifulSoup
import re

def fetch_mal_news():
    url = "https://myanimelist.net/news"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.select(".news-unit.clearfix")

    news = []
    for a in articles[:3]:  # Only latest 3 news
        title = a.select_one(".title").text.strip()
        link = a.select_one("a")["href"]
        img = a.select_one("img")
        image_url = img["src"] if img else None

        news.append({
            "title": title,
            "link": link,
            "image": image_url,
            "video": None,  # MAL doesn't usually have embedded video
            "source": "MyAnimeList"
        })
    return news


def fetch_crunchyroll_news():
    url = "https://www.crunchyroll.com/news"
    res = requests.get(url)
    soup = BeautifulSoup(res.text, "html.parser")
    articles = soup.select("a.news-card__link")

    news = []
    for a in articles[:3]:
        title_tag = a.select_one(".news-card__title")
        title = title_tag.text.strip() if title_tag else "No title"
        link = "https://www.crunchyroll.com" + a["href"]

        # Visit article page to extract image and video
        article_res = requests.get(link)
        article_soup = BeautifulSoup(article_res.text, "html.parser")

        # Image
        og_image = article_soup.find("meta", property="og:image")
        image_url = og_image["content"] if og_image else None

        # YouTube link
        iframe = article_soup.find("iframe")
        video_url = None
        if iframe and "youtube.com" in iframe.get("src", ""):
            video_url = iframe["src"]
            # Normalize embedded link to watchable format
            match = re.search(r"embed/([a-zA-Z0-9_-]{11})", video_url)
            if match:
                video_url = f"https://www.youtube.com/watch?v={match.group(1)}"

        news.append({
            "title": title,
            "link": link,
            "image": image_url,
            "video": video_url,
            "source": "Crunchyroll"
        })

    return news
