from pathlib import Path
import instaloader
import shutil, time, random, json
from django.conf import settings
from django.http import JsonResponse
from api.models import UserSession

def download_instagram_reel(request, url):
    """
    Downloads a single Instagram reel using Instaloader and renames the file.
    """
    sessionid = request.COOKIES.get('sessionid')
    
    if not sessionid:
        return JsonResponse({
            "error": "Session ID not provided",
            "requires_login": True
        }, status=401)

    user_session = UserSession.objects.filter(session_id=sessionid).first()  # sessionid used as username
    if not user_session:
        return JsonResponse({
            "error": "No session found. Please log in again.",
            "requires_login": True
        }, status=401)

    try:
        session_data = json.loads(user_session.session_data)
        cookies = session_data.get('cookies', [])

        loader = instaloader.Instaloader(
            download_pictures=True,
            download_videos=True,
            download_video_thumbnails=True,
            download_geotags=False,
            download_comments=False,
            post_metadata_txt_pattern="",
            max_connection_attempts=3,
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36"
        )

        for cookie in cookies:
            if "name" in cookie and "value" in cookie:
                loader.context._session.cookies.set(
                    cookie["name"], cookie["value"], domain=".instagram.com"
                )

        time.sleep(random.uniform(1, 2))

        reel_shortcode = url.split("/")[-2]
        reel = instaloader.Post.from_shortcode(loader.context, reel_shortcode)
        target_dir = Path(settings.MEDIA_ROOT) / 'downloads' / 'reel' / reel_shortcode

        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        loader.download_post(reel, target=target_dir)

        for file in target_dir.iterdir():
            if file.suffix == ".mp4":
                new_name = f"{reel_shortcode}.mp4"
                new_file_path = target_dir / new_name
                file.rename(new_file_path)
                media_url = request.build_absolute_uri(
                    f'/media/downloads/reel/{reel_shortcode}/{new_file_path.name}'
                )
                return JsonResponse({"status": "success", "media_data": {"media_url": media_url}})

        raise FileNotFoundError("Reel file (.mp4) not found in the download directory.")

    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)