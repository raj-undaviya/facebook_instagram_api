from django.urls import path, include
from api.views import *

urlpatterns = [
    path('auth/login', LoginView.as_view(), name='login'),
    path('download', InstaDownload.as_view(), name='downloads'),
    # path('profile', InstaDownload.ProfileView, name='profile'),
    # path('download-post', InstaDownload.PostDownloadView, name='download_posts'),
    # path('download-reel', InstaDownload.ReelDownloadView, name='download_reels'),
    # path('download-story', InstaDownload.StoryDownloadView, name='download_story'),
    # path('download-highlight', InstaDownload.HighlightDownloadView, name='download_highlights'),
    # path('followings', InstaDownload.FolloweingsView.as_view(), name='followees'),
    # path('followeers', InstaDownload.FollowersView.as_view(), name='followeers'),
]