from django.db import models
from django.contrib.auth.models import User
# Create your models here.
class AttachmentDetails(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="attachment_details")
    Full_Name = models.CharField(max_length=500)
    Address = models.CharField(max_length=500)
    Email = models.EmailField()
    Phone_number = models.CharField(max_length=500)
    DOB = models.CharField(max_length=500)
    dates = models.CharField(max_length=500)
    urls = models.URLField()

class GoogleTokens(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE,related_name="google_tokens")
    access_token = models.CharField(max_length=1000)
    refresh_token = models.CharField(max_length=1000)
