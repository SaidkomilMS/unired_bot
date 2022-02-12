from django.db import models
from asgiref.sync import sync_to_async


class User(models.Model):
    chat_id = models.IntegerField(unique=True)
    unired_id = models.IntegerField(blank=True, null=True)
    last_otp_token = models.TextField(blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    expires_at = models.DateTimeField(blank=True, null=True)
    phone_number = models.CharField(max_length=12, blank=True, null=True)
    phone_number_is_contact = models.BooleanField(default=False)
    language = models.CharField(max_length=10, blank=True, null=True)
    is_registered = models.BooleanField(default=False, blank=True, null=True)
    password = models.IntegerField(blank=True, null=True)
    name = models.CharField(max_length=40, null=True)
    last_name = models.CharField(max_length=40, null=True)
    
    @classmethod
    async def exists(cls, chat_id) -> bool:
        try:
            await sync_to_async(cls.objects.get, thread_sensitive=True)(chat_id=chat_id)
        except Exception:
            return False
        return True
