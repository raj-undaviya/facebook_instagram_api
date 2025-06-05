import instaloader
from pathlib import Path
import json, re, shutil, time, random
from django.conf import settings
from django.http import JsonResponse
from api.models import UserSession

def download_instagram_stories(request, url):
    """
    Downloads Instagram stories for a target user using the same pattern as reel download.
    """
    sessionid = request.COOKIES.get("sessionid")

    if not sessionid:
        return JsonResponse(
            {"error": "Session ID not provided", "requires_login": True}, status=401
        )

    user_session = UserSession.objects.filter(session_id=sessionid).first()
    if not user_session:
        return JsonResponse(
            {"error": "No session found. Please log in again.", "requires_login": True},
            status=401,
        )

    try:
        # Extract username and story ID from URL
        match = re.search(r"stories/([^/]+)/(\d+)", url)
        if not match:
            return JsonResponse(
                {
                    "error": "Invalid Instagram story URL format",
                },
                status=400,
            )

        target_username = match.group(1)
        print(f"Target username ===========================> : {target_username}")
        story_id = match.group(2)

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

        for cookie in cookies:
            if "name" in cookie and "value" in cookie:
                loader.context._session.cookies.set(
                    cookie["name"], cookie["value"], domain=".instagram.com"
                )

        time.sleep(random.uniform(1, 2))

        # Get profile
        profile = instaloader.Profile.from_username(loader.context, target_username)
        target_dir = Path(settings.MEDIA_ROOT) / 'downloads' / 'stories' / target_username
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        stories = loader.get_stories(userids=[profile.userid])
        print(f"Stories for {stories} fetched successfully.")
        renamed_file = None
        for story in stories:
            for item in story.get_items():
                if story_id == str(item.mediaid):
                    loader.download_storyitem(item, target=target_dir)
                    file_extension = "mp4" if item.is_video else "jpg"
                    file_pattern = f"*UTC.{file_extension}"
                    matching_files = list(target_dir.glob(file_pattern))
                    if matching_files:
                        file_path = matching_files[-1]
                        print("File found:", file_path)
                        media_url = request.build_absolute_uri(
                            f"/media/downloads/stories/{target_username}/{file_path.name}"
                        )
                        renamed_file = media_url
                        story_metadata = {"media_url": renamed_file}

                        return JsonResponse(
                            {
                                "status": "success",
                                "media_data": {"media_url": story_metadata},
                            }
                        )

        raise FileNotFoundError("Story not found or may have expired.")

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)
