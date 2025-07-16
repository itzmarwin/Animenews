import feedparser
from .config import RSS_FEED_URL, LAST_GUID_FILE


def get_last_guid():
    """Read last posted GUID from file."""
    if not os.path.exists(LAST_GUID_FILE):
        return None
    with open(LAST_GUID_FILE, "r") as f:
        return f.read().strip()


def save_last_guid(guid):
    """Save last posted GUID to file."""
    with open(LAST_GUID_FILE, "w") as f:
        f.write(guid)


def fetch_latest_post():
    """Fetch latest item from RSS and check if it's new."""
    feed = feedparser.parse(RSS_FEED_URL)
    if not feed.entries:
        return None

    latest_entry = feed.entries[0]
    last_guid = get_last_guid()

    if latest_entry.id == last_guid:
        return None  # No new post

    save_last_guid(latest_entry.id)

    return {
        "title": latest_entry.title,
        "link": latest_entry.link,
        "summary": latest_entry.summary,
        "published": latest_entry.published,
    }
