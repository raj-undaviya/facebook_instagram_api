from pathlib import Path
import json, requests, instaloader, re
from django.conf import settings
from django.http import HttpRequest

def load_instaloader_session_for_profile(username):
    """
    Loads an Instaloader session from a saved cookie file.
    """
    session_dir = settings.BASE_DIR / "sessions"
    session_file = session_dir / f"instagram_cookies_{username}.json"
    try:
        loader = instaloader.Instaloader()
        with open(session_file, "r") as file:
            cookies = {cookie["name"]: cookie["value"] for cookie in json.load(file)}
        loader.load_session(username=username, session_data=cookies)
        print(f"Session loaded successfully for {username}.")
        return loader
    except FileNotFoundError:
        print("Session file not found. Please ensure you have logged in and saved cookies.")
        raise
    except Exception as e:
        print(f"Error loading session: {e}")
        raise

def fetch_instagram_profile(request: HttpRequest,username: str, url: str):
    """
    Downloads the Instagram profile picture and returns profile data.
    """
    try:
        print("IN Profile picture download file --->")
        loader = load_instaloader_session_for_profile(username)
        match = re.match(r"https?://(?:www\.)?instagram\.com/([a-zA-Z0-9_.-]+)", url)
        if not match:
            raise ValueError(f"Invalid Instagram URL: {url}")
        target_username = match.group(1)
        profile_data = instaloader.Profile.from_username(loader.context, target_username)
        target_dir = Path(settings.MEDIA_ROOT) / 'downloads' / 'profile_pictures'
        target_dir.mkdir(parents=True, exist_ok=True)
        profile_pic_url = profile_data.profile_pic_url
        response = requests.get(profile_pic_url, stream=True)
        renamed_file = None
        if response.status_code == 200:
            filename = target_dir / f"{profile_data.username}_profile_picture.jpg"
            with open(filename, "wb") as file:
                for chunk in response.iter_content(1024):
                    file.write(chunk)
            media_url = request.build_absolute_uri(f'/media/downloads/profile_pictures/{filename.name}')
            renamed_file = media_url
            response_data = {
                    "media_url": renamed_file
                }
            return response_data
        else:
            return {"message": "Failed to download profile picture."}
    except Exception as e:
        raise e