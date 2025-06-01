from django.http import JsonResponse
from api.serializers import LoginRequestSerializer
from api.utils.login import login_data
from rest_framework.views import APIView
from rest_framework.response import Response
from api.utils.get_followees import get_followees
from api.utils.get_followers import get_followers
from rest_framework.exceptions import APIException
from api.utils.profile_data import fetch_instagram_profile
from api.utils.download_highlights import download_highlight
from api.utils.download_posts import download_instagram_post
from api.utils.download_reels import download_instagram_reel
from api.utils.download_stories import download_instagram_stories
from pathlib import Path
from django.conf import settings
import os

# Create your views here.

class LoginView(APIView):
    def post(self, request):
        print("Request data:", request.data, request.POST)
        user_id = request.data.get("user_id")
        print("user_idddddddddddd", user_id)
        # session_file = request.FILES.get("session_file")
        # if not user_id or not session_file:
        #     return JsonResponse(
        #         {"status": "error", "message": "user_id or session file is missing."},
        #         status=400,
        #     )

        # response = login_data(user_id=user_id, session_file=session_file)
        if response.get("status") == "success":
            return JsonResponse(response, status=200)
        else:
            return JsonResponse(response, status=400)

class InstaDownload(APIView):
    
    def get(self, request):
        """
        Determines the appropriate download view based on the URL pattern in the query parameter.
        """
        url = request.query_params.get('url')
        username = request.query_params.get('username')

        if not url or not username:
            raise APIException("Both 'username' and 'url' are required.")

        try:
            if '/p/' in url:
                return self.PostDownloadView(request, username, url)
            elif '/reel/' in url:
                return self.ReelDownloadView(request, username, url)
            elif '/stories/' in url:
                return self.StoryDownloadView(request, username, url)
            elif '/s/' in url:
                return self.HighlightDownloadView(request, username, url)
            elif url:
                return self.ProfileView(request, username, url)
            else:
                raise APIException("Unsupported URL format. Provide a valid Instagram post, reel, or story URL.")
        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")
    
    def ProfileView(self, request, username, url):
        """
        Asynchronous view for fetching Instagram profile info.
        """
        if not username or not url:
            raise APIException("Both 'username' and 'url' are required.")
        try:
            profile_info = fetch_instagram_profile(request, username, url)
            return Response(profile_info)
        except Exception as e:
            raise APIException(str(e))
            
    def PostDownloadView(self, request, username, url):
        try:
            post_details = download_instagram_post(request, username, url)
            return Response(post_details)
        except APIException as api_exception:
            return Response({"error": str(api_exception)}, status=400)
        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")

    def ReelDownloadView(self, request, username, url):
        try:
            reel_detail = download_instagram_reel(request, username, url)
            return Response(reel_detail)
        except APIException as api_exception:
            return Response({"error": str(api_exception)}, status=400)
        except Exception as e:
            raise APIException(f"An error occurred while downloading the post: {str(e)}")

    def StoryDownloadView(self, request, username, url):
        try:
            story_detail = download_instagram_stories(request, username, url)
            return Response(story_detail)
        except APIException as api_exception:
            return Response({"error": str(api_exception)}, status=400)
        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")

    def HighlightDownloadView(self, request, username, url):
        try:
            highlight_detail = download_highlight(request, username, url)
            return Response(highlight_detail)
        except APIException as api_exception:
            return Response({"error": str(api_exception)}, status=400)
        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")
