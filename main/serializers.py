from rest_framework import serializers
from .models import AttachmentDetails
from django.contrib.auth.models import User

class UserSerializers(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name','last_name', 'email')
class AttachmentSerializers(serializers.ModelSerializer):
    user = UserSerializers(required=False)
    class Meta:
        model = AttachmentDetails
        fields = '__all__'

