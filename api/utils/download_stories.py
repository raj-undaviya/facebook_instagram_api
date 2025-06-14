import urllib.parse
import re
import json
import time
import random
import shutil
from pathlib import Path
from django.http import JsonResponse
from django.conf import settings
import instaloader
from api.models import UserSession


def download_instagram_stories(request, url):
    """
    Downloads Instagram stories using igsh parameter as primary identifier.
    """
    sessionid = request.COOKIES.get("sessionid")
    user_session = UserSession.objects.filter(session_id=sessionid).first()

    try:
        # Decode the URL first
        decoded_url = urllib.parse.unquote(url)

        # Extract username, story ID, and igsh parameter
        match = re.search(r"stories/([^/]+)/(\d+)", decoded_url)
        igsh_match = re.search(r"igsh=([^&&#]+)", decoded_url)

        if not match:
            return JsonResponse(
                {"error": "Invalid Instagram story URL format"}, status=400
            )

        target_username = match.group(1)
        story_id = match.group(2)
        igsh = igsh_match.group(1) if igsh_match else None

        if not igsh:
            return JsonResponse({"error": "No igsh parameter found in URL"}, status=400)

        session_data = json.loads(user_session.session_data)
        cookies = session_data.get("cookies", [])

        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=True,
            download_geotags=False,
            download_comments=False,
            post_metadata_txt_pattern="",
            max_connection_attempts=3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        )

        # FIXED: Convert cookies to proper format and load session once
        cookies_dict = {}
        for cookie in cookies:
            if "name" in cookie and "value" in cookie:
                cookies_dict[cookie["name"]] = cookie["value"]

        # Load session with all cookies at once
        if cookies_dict:
            loader.load_session(
                username=user_session.username, session_data=cookies_dict
            )
            print(f"Session loaded successfully for {user_session.username}")
        else:
            print("No valid cookies found")

        time.sleep(random.uniform(1, 2))

        # Get profile
        profile = instaloader.Profile.from_username(loader.context, target_username)

        # Setup target directory
        target_dir = Path(settings.MEDIA_ROOT) / 'downloads' / 'stories' / target_username
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        # Get stories
        stories = loader.get_stories(userids=[profile.userid])

        # Try multiple approaches to match using igsh
        story_found = False
        matched_item = None

        for story in stories:
            for item in story.get_items():

                # Log all available attributes for debugging
                item_attrs = [attr for attr in dir(item) if not attr.startswith("_")]

                # Approach 1: Try to match igsh with various item properties
                potential_matches = [
                    str(item.mediaid),
                    getattr(item, "shortcode", ""),
                    getattr(item, "pk", ""),
                    str(getattr(item, "taken_at_timestamp", "")),
                ]

                # Also check if the item has any URL-related attributes
                if hasattr(item, "video_url"):
                    potential_matches.append(str(item.video_url))
                if hasattr(item, "display_url"):
                    potential_matches.append(str(item.display_url))

                # Check if igsh matches any of these identifiers
                for potential_match in potential_matches:
                    if igsh in potential_match or potential_match in igsh:
                        story_found = True
                        matched_item = item
                        break

                # Approach 2: If primary story_id matches, use it as fallback
                if not story_found and story_id == str(item.mediaid):
                    story_found = True
                    matched_item = item

                if story_found:
                    break
            if story_found:
                break

        if not story_found or not matched_item:
            # Try alternative approach: download all current stories and find by timestamp/order
            all_items = []
            for story in stories:
                all_items.extend(list(story.get_items()))

            # Sort by timestamp and try to find the story that might correspond to the igsh
            all_items.sort(
                key=lambda x: getattr(x, "taken_at_timestamp", 0), reverse=True
            )

            # For now, let's try to decode the igsh to see if it contains useful info
            try:
                import base64

                decoded_igsh = base64.b64decode(igsh + "==").decode(
                    "utf-8", errors="ignore"
                )
                print(f"Decoded igsh: {decoded_igsh}")
            except:
                print("Could not decode igsh")

            return JsonResponse(
                {"error": "Story not found using igsh parameter"}, status=404
            )

        # Download the matched item
        loader.download_storyitem(matched_item, target=target_dir)

        # Find the downloaded file
        file_extension = "mp4" if matched_item.is_video else "jpg"
        file_pattern = f"*UTC.{file_extension}"
        matching_files = list(target_dir.glob(file_pattern))

        if matching_files:
            file_path = matching_files[-1]

            media_url = request.build_absolute_uri(
                f"/media/downloads/stories/{target_username}/{file_path.name}"
            )

            story_metadata = {"media_url": media_url}
            return JsonResponse({"status": "success", "media_data": story_metadata})
        else:
            return JsonResponse({"error": "Downloaded file not found"}, status=500)

    except instaloader.exceptions.ProfileNotExistsException:
        return JsonResponse({"error": "Profile does not exist"}, status=404)
    except instaloader.exceptions.PrivateProfileNotFollowedException:
        return JsonResponse({"error": "Private profile - not following"}, status=403)
    except instaloader.exceptions.LoginRequiredException:
        return JsonResponse({"error": "Login required"}, status=401)
    except Exception as e:
        return JsonResponse(
            {"error": f"An error occurred while downloading stories: {str(e)}"},
            status=500,
        )
