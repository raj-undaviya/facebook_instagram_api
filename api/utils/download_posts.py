from pathlib import Path
import instaloader
import shutil, time, random, json
from django.conf import settings
from django.http import JsonResponse
from api.models import UserSession

def download_instagram_post(request, url):
    
    sessionid = request.COOKIES.get('sessionid')
    
    if not sessionid:
        return JsonResponse({
            "error": "Session ID not provided",
            "requires_login": True
        }, status=401)

    user_session = UserSession.objects.filter(session_id=sessionid).first()
    if not user_session:
        return JsonResponse({
            "error": "No session found. Please log in again.",
            "requires_login": True
        }, status=401)

    try:
        session_data = json.loads(user_session.session_data)
        cookies = session_data['cookies']

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

        post_shortcode = url.split("/p/")[1].split("/")[0]
        post = instaloader.Post.from_shortcode(loader.context, post_shortcode)
        target_dir = Path(settings.MEDIA_ROOT) / 'downloads' / 'posts' / post_shortcode

        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)

        loader.download_post(post, target=target_dir)

        media_data = []
        for file in target_dir.iterdir():
            if file.suffix == ".jpg":
                media_url = request.build_absolute_uri(
                    f"/media/downloads/posts/{post_shortcode}/{file.name}"
                )
                media_data.append({"media_url": media_url})

        return JsonResponse({"status": "success", "media_data": media_data})
    except Exception as e:
        return JsonResponse({"error": str(e)}, status=500)