"""fetchMail URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path,include
from main.views import home,message_obj_view, all_messages_with_attachment,next_page,next_messages_with_attachment, CreateAttachmentDetails, ListAttachmentDetails,test_view,gmail_service, get_token, get_user,process_attachment_with_eden_ai, process_attachment_test,ConverttokenView

urlpatterns = [
    path('admin/', admin.site.urls),
    path('',home,name="home"),
    path('get_token/',get_token,name="token"),
    path('test/',test_view,name="test"),
    path('test_gmail_service/',gmail_service,name="test_service"),
    path('with_attachment/',all_messages_with_attachment,name="with_attachment"),
    path('next_page/<token>/',next_page,name="next_page"),
    path('next_page_with_attachment/<token>/',next_messages_with_attachment,name="next_page"),
    path('message_view/',message_obj_view,name="message_view"),
    #path('attachment/<id>/', process_attachment),
    path('attachment/<id>/', process_attachment_with_eden_ai),
    path('attachment_test/<id>/', process_attachment_test),
    path('create_attachment/', CreateAttachmentDetails.as_view() ),
    path('list_attachment/', ListAttachmentDetails.as_view() ),
    path('auth/convert-tokens/', ConverttokenView.as_view() ),
    path('get_user/',get_user),
    path('auth/', include('drf_social_oauth2.urls',namespace='drf'))
    #path('user_login/',LogIn.as_view()),
    #path('',include('allauth.urls')),
]
