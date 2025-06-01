from pathlib import Path
import instaloader, json, re, shutil
from django.conf import settings
from rest_framework.exceptions import APIException
from django.http import HttpRequest

def load_instaloader_session(username):
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
        return loader
    except FileNotFoundError as e:
        raise e
    except Exception as exception:
        raise exception

def download_highlight(request: HttpRequest, username: str, url: str):
    """
    Downloads Instagram highlights using the provided link.
    """
    try:
        loader = load_instaloader_session(username)
        match = re.search(r"story_media_id=(\d+)_(\d+)", url)
        if not match:
            raise ValueError("Invalid link format. Unable to extract highlight ID.")
        highlight_id = match.group(1)
        user_id = match.group(2)
        profile = instaloader.Profile.from_id(loader.context, int(user_id))
        highlights = loader.get_highlights(profile.userid)
        target_dir = Path(settings.MEDIA_ROOT) / 'downloads' / 'highlights'
        if target_dir.exists():
            shutil.rmtree(target_dir)
            print("Directory and its contents removed successfully.")
        target_dir.mkdir(parents=True, exist_ok=True)
        for highlight in highlights:
            try:
                items = list(highlight.get_items())
                print(f"Total items in highlight '{highlight.title}': {len(items)}")
                renamed_file = None
                for item in items:
                    print(f"Processing Item ID: {item.mediaid} (Type: {type(item.mediaid)})")
                    if str(highlight_id) == str(item.mediaid):
                        print("Match found. Downloading item...")
                        loader.download_storyitem(item, target_dir)
                        file_extension = "mp4" if item.is_video else "jpg"
                        file_pattern = f"*UTC.{file_extension}"
                        matching_files = list(target_dir.glob(file_pattern))
                        if matching_files:
                            file_path = matching_files[-1]
                            print(f"File downloaded: {file_path}")
                            media_url = request.build_absolute_uri(f'/media/downloads/highlights/{file_path.name}')
                            renamed_file = media_url
                            highlight_metadata = {
                                "media_url": renamed_file
                            }
                        return highlight_metadata  # Return after successful download
            except Exception as item_error:
                raise item_error
        return None
    except Exception as e:
        raise APIException(f"An error occurred: {e}")