import requests
import re

ANILIST_API_URL = "https://graphql.anilist.co"

def clean_title_for_search(title: str) -> str:
    """Clean title for better AniList search matching"""
    # Remove special characters and year information
    cleaned = re.sub(r'[^\w\s]', '', title)
    cleaned = re.sub(r'\b\d{4}\b', '', cleaned)
    # Remove common prefixes
    cleaned = re.sub(r'^(new|the|anime|manga|game|trailer|teaser)\s', '', cleaned, flags=re.IGNORECASE)
    return cleaned.strip()

def get_anime_info(title):
    query = '''
    query ($search: String) {
      Media(search: $search, type: ANIME) {
        title {
          romaji
          english
        }
        coverImage {
          large
        }
        trailer {
          site
          id
        }
        startDate {
          year
          month
          day
        }
        studios(isMain: true) {
          nodes {
            name
          }
        }
      }
    }
    '''

    # Clean the title for better search results
    search_title = clean_title_for_search(title)
    variables = {"search": search_title}

    try:
        response = requests.post(
            ANILIST_API_URL,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"},
            timeout=10
        )
        
        # Handle non-200 responses
        if response.status_code != 200:
            print(f"❌ AniList API error: {response.status_code}")
            return None

        data = response.json()
        
        # Handle GraphQL errors or missing data
        if "errors" in data:
            print(f"❌ AniList query error: {data['errors'][0]['message']}")
            return None
            
        if "data" not in data or data["data"]["Media"] is None:
            print(f"ℹ️ No anime found for: {search_title}")
            return None

        data = data["data"]["Media"]

        # Use the most available title
        english_title = data["title"]["english"] or data["title"]["romaji"] or title

        image = data["coverImage"]["large"] if data["coverImage"] else None

        # Trailer URL construction
        trailer_link = ""
        if data.get("trailer") and data["trailer"].get("site") and data["trailer"].get("id"):
            site = data["trailer"]["site"]
            vid = data["trailer"]["id"]
            if site.lower() == "youtube":
                trailer_link = f"https://youtu.be/{vid}"
            elif site.lower() == "dailymotion":
                trailer_link = f"https://dailymotion.com/video/{vid}"

        # Studio name
        studio = data["studios"]["nodes"][0]["name"] if data["studios"]["nodes"] else "Unknown"

        # Release date format
        date = data["startDate"]
        release = "Unknown"
        if date["year"]:
            release = f"{date['year']}-{date.get('month', '??'):02}-{date.get('day', '??'):02}"

        return {
            "title": english_title,
            "studio": studio,
            "trailer": trailer_link,
            "release_date": release,
            "image": image
        }

    except Exception as e:
        print(f"❌ AniList fetch error: {e}")
        return None
