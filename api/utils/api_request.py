import aiohttp
import json
from django.conf import settings

async def make_authenticated_request(username: str, target_username: str):
    """
    Makes an authenticated API request to fetch profile info.
    """
    session_dir = settings.BASE_DIR / "sessions"
    session_file = session_dir / f"instagram_cookies_{username}.json"
    try:
        with open(session_file, "r") as file:
            cookies = {cookie["name"]: cookie["value"] for cookie in json.load(file)}

        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
            "x-ig-app-id": "936619743392459",  # Static Instagram app ID for web
            "Accept": "/",
            "Accept-Language": "en-US,en;q=0.9",
        }

        url = f"https://i.instagram.com/api/v1/users/web_profile_info/?username={target_username}"
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers, cookies=cookies) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    text = await response.text()
                    raise Exception(f"Error fetching profile: {text}")
    except Exception as e:
        raise Exception(f"Error in API request: {str(e)}")