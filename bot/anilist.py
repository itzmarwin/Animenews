import requests

ANILIST_API_URL = "https://graphql.anilist.co"

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

    variables = {"search": title}

    try:
        response = requests.post(
            ANILIST_API_URL,
            json={"query": query, "variables": variables},
            headers={"Content-Type": "application/json"}
        )
        if response.status_code != 200:
            print(f"❌ AniList API error: {response.status_code}")
            return None

        data = response.json()["data"]["Media"]

        english_title = data["title"]["english"] or data["title"]["romaji"]
        image = data["coverImage"]["large"]

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
            release = f"{date['year']}-{date['month']:02}-{date['day']:02}"

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
