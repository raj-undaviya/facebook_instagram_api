from rest_framework import serializers

class LoginRequestSerializer(serializers.Serializer):
    """
    Serializer for Instagram Login response.
    """
    username = serializers.CharField(max_length=100)
    password = serializers.CharField(max_length=100)

class FolloweesResponseSerializer(serializers.Serializer):
    """
    Serializer for Instagram Followings response.
    """
    username = serializers.CharField(max_length=100)
    full_name = serializers.CharField(max_length=100)
    profile_pic_url = serializers.URLField()
    
class FollowersResponseSerializer(serializers.Serializer):
    """
    Serializer for Instagram Followers response.
    """
    username = serializers.CharField(max_length=100)
    full_name = serializers.CharField(max_length=100)
    profile_pic_url = serializers.URLField()