from django.urls import path, include
from api.views import *

urlpatterns = [
    path("auth/login", LoginView.as_view(), name="login"),
    path("download", InstaDownload.as_view(), name="downloads"),
]
