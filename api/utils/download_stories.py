from pathlib import Path0
import instaloader, time, random, logging
import json, re, shutil
from django.conf import settings
from rest_framework.exceptions import APIException
from api.models import UserSession
from django.http import JsonResponse

logger = logging.getLogger(__name__)

def download_instagram_stories(request, url):
    """
    Downloads Instagram stories for a target user and returns metadata about the downloaded files.
    """
    
    try:
        # Extract username and story ID from URL
        match = re.search(r"stories/([^/]+)/(\d+)", url)
        if not match:
            return JsonResponse({
                "error": "Invalid Instagram story URL format",
            }, status=400)
        
        target_username = match.group(1)
        story_id = match.group(2)
        
        # Initialize loader for checking profile privacy
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
        
        # Check if profile is private
        try:
            profile = instaloader.Profile.from_username(loader.context, target_username)
            is_profile_private = profile.is_private
            logger.info(f"Is profile private: {is_profile_private}")
        except Exception as e:
            return JsonResponse({
                "error": f"Failed to fetch profile information: {str(e)}",
            }, status=404)
        
        # Handle private profiles
        if is_profile_private:
            # Check if the user is logged in
            if not request.user.is_authenticated:
                return JsonResponse({
                    "error": "You must be logged in to download stories from private accounts.",
                    "requires_login": True
                }, status=403)
            
            # Get session ID for authentication
            sessionid = request.COOKIES.get('sessionid')
            if not sessionid:
                return JsonResponse({
                    "error": "Session ID not provided",
                    "requires_login": True
                }, status=401)

            # Get user session data
            user_session = UserSession.objects.filter(session_id=sessionid).first()
            if not user_session:
                return JsonResponse({
                    "error": "No session found. Please log in again.",
                    "requires_login": True
                }, status=401)

            try:
                # Load session data and cookies
                session_data = json.loads(user_session.session_data)
                cookies = session_data.get('cookies', [])

                # Reinitialize loader with authentication
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
                
                # Set cookies for authentication
                for cookie in cookies:
                    if "name" in cookie and "value" in cookie:
                        loader.context._session.cookies.set(
                            cookie["name"], cookie["value"], domain=".instagram.com"
                        )

                # Add delay to avoid rate limiting
                time.sleep(random.uniform(1, 2))
                
                # Re-fetch profile with authentication
                profile = instaloader.Profile.from_username(loader.context, target_username)
                
            except json.JSONDecodeError:
                return JsonResponse({
                    "error": "Invalid session data format",
                    "requires_login": True
                }, status=401)
            except Exception as e:
                return JsonResponse({
                    "error": f"Authentication failed: {str(e)}",
                    "requires_login": True
                }, status=401)
        
        # Prepare download directory
        target_dir = Path(settings.MEDIA_ROOT) / 'downloads' / 'stories' / target_username
        if target_dir.exists():
            shutil.rmtree(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Download stories
        try:
            stories = loader.get_stories(userids=[profile.userid])
            
            for story in stories:
                for item in story.get_items():
                    if story_id == str(item.mediaid):
                        loader.download_storyitem(item, target=target_dir)
                        
                        # Find the downloaded file
                        file_extension = "mp4" if item.is_video else "jpg"
                        file_pattern = f"*UTC.{file_extension}"
                        matching_files = list(target_dir.glob(file_pattern))
                        
                        if matching_files:
                            file_path = matching_files[-1]
                            print("File found:", file_path)
                            media_url = request.build_absolute_uri(f'/media/downloads/stories/{target_username}/{file_path.name}')
                            
                            story_metadata = {
                                "media_url": media_url,
                                "username": target_username,
                                "story_id": story_id,
                                "is_video": item.is_video,
                                "file_name": file_path.name
                            }
                            return JsonResponse(story_metadata, status=200)
            
            # If no matching story found
            return JsonResponse({
                "error": "Story not found or may have expired",
            }, status=404)
            
        except Exception as e:
            return JsonResponse({
                "error": f"Failed to download story: {str(e)}",
            }, status=500)

    except Exception as e:
        return JsonResponse({
            "error": f"An unexpected error occurred: {str(e)}",
        }, status=500)