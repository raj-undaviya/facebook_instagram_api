from django.http import JsonResponse, HttpResponse
from api.serializers import LoginRequestSerializer
from api.utils.login import login_data
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from api.utils.profile_data import fetch_instagram_profile
from api.utils.download_highlights import download_highlight
from api.utils.download_posts import download_instagram_post
from api.utils.download_reels import download_instagram_reel
from api.utils.download_stories import download_instagram_stories

class LoginView(APIView):
    def post(self, request):
        print("Login request received --------------------------> :", request.data)
        login_result = login_data(request)
        print("Login response:", login_result)
        return login_result
        # else:
        #     return Response(
        #         {"status": "error", "message": "Login failed."}, status=400
        #     )
 
class InstaDownload(APIView):

    def get(self, request):
        """
        Determines the appropriate download view based on the URL pattern in the query parameter.
        """
        url = request.query_params.get('url')

        if not url:
            raise APIException(url, "Both 'username' and 'url' are required.")

        try:
            if '/p/' in url:
                return self.PostDownloadView(request, url)
            elif '/reel/' in url:
                return self.ReelDownloadView(request, url)
            elif '/stories/' in url:
                return self.StoryDownloadView(request, url)
            elif '/s/' in url:
                return self.HighlightDownloadView(request, url)
            elif url:
                return self.ProfileView(request, url)
            else:
                raise APIException("Unsupported URL format. Provide a valid Instagram post, reel, or story URL.")
        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")

    def ProfileView(self, request, url):
        try:
            profile_info = fetch_instagram_profile(request, url)
            return profile_info
        except Exception as e:
            raise APIException(str(e))

    def PostDownloadView(self, request, url):
        try:
            post_details = download_instagram_post(request, url)
            return post_details
        except APIException as api_exception:
            return Response({"error": str(api_exception)}, status=400)
        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")

    def ReelDownloadView(self, request, url):
        try:
            reel_detail = download_instagram_reel(request, url)
            return reel_detail
        except APIException as api_exception:
            return Response({"error": str(api_exception)}, status=400)
        except Exception as e:
            raise APIException(f"An error occurred while downloading the post: {str(e)}")

    def StoryDownloadView(self, request, url):
        try:
            story_detail = download_instagram_stories(request, url)
            return story_detail
        except APIException as api_exception:
            return Response({"error": str(api_exception)}, status=400)
        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")

    def HighlightDownloadView(self, request, url):
        try:
            highlight_detail = download_highlight(request, url)
            return highlight_detail
        except APIException as api_exception:
            return Response({"error": str(api_exception)}, status=400)
        except Exception as e:
            raise APIException(f"An unexpected error occurred: {str(e)}")
