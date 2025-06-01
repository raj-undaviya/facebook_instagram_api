from django.db import models

class UserSession(models.Model):
    username = models.CharField(max_length=100, unique=True)
    cookies = models.JSONField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)