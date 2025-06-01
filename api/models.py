# In your models.py
from django.db import models

class UserSession(models.Model):
    username = models.CharField(max_length=100, unique=False, default='')
    session_id = models.CharField(max_length=100, unique=True, default='', primary_key=True)
    session_data = models.TextField()  # For storing the JSON string
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Session for {self.username}"
