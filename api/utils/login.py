from django.http import JsonResponse
from rest_framework import status
import json, instaloader, logging
from django.core.cache import cache
from api.models import UserSession

def login_data(request):
    try:
        loader = instaloader.Instaloader(
            download_pictures=False,
            download_videos=False,
            download_video_thumbnails=False,
            download_geotags=False,
            download_comments=False,
            post_metadata_txt_pattern="",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Safari/537.36",
        )

        if request.FILES.get("session_file"):
            session_file = request.FILES.get("session_file")
            content = session_file.read()
            if isinstance(content, bytes):
                content = content.decode("utf-8")
            cookies = json.loads(content)
        else:
            return JsonResponse(
                {"error": "No session file or cookies provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        session_user_id = None
        session_id = None

        for cookie in cookies["cookies"]:

            if cookie["name"] == "ds_user_id":
                session_user_id = cookie["value"]
                if session_user_id:
                    session_user_id = int(session_user_id)

            elif cookie["name"] == "sessionid":
                session_id = cookie["value"]
                if session_id:
                    session_id = str(session_id)

        if not session_user_id:
            return JsonResponse(
                {"error": "Session missing required ds_user_id cookie"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Set session cookies
        for cookie in cookies["cookies"]:
            if cookie:
                loader.context._session.cookies.set(
                    name=cookie["name"],
                    value=cookie["value"],
                    domain=cookie["domain"],
                    path=cookie["path"],
                    expires=cookie["expires"],
                    secure=cookie["secure"],
                )

        try:
            profile_self = instaloader.Profile.from_id(loader.context, session_user_id)
            auth_username = profile_self.username

            session_data_json = json.dumps(cookies)
            user_session, created = UserSession.objects.update_or_create(
                session_id=session_id,
                username=auth_username,
                defaults={"session_data": session_data_json},
            )

            session = user_session.username
            cache_key = f"instagram_session_{auth_username}"
            cache_data = {"username": auth_username, "session_data": cookies}
            request.session["cache_data"] = cache_data

            response = {
                "authenticated_as": auth_username,
                "status": "success",
                "session_saved": True,
                "cache_key": cache_key,
                "session_valid_for": "30 minutes",
            }

            return JsonResponse(response, status=status.HTTP_200_OK)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        error_message = str(e)
        return JsonResponse(
            {"error": error_message, "status": "error"},
            status=status.HTTP_400_BAD_REQUEST,
        )
