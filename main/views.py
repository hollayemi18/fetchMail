import os
import pickle
from PIL import Image
from io import BytesIO
import json
import pytesseract
import requests
from mimetypes import guess_extension
from pdf2image import convert_from_bytes
from base64 import urlsafe_b64decode, urlsafe_b64encode, b64encode, b64decode
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.auth import default
from google.oauth2.credentials import Credentials
from django.contrib.auth import logout as Logout
from django.shortcuts import render, HttpResponse, redirect
from django.conf import settings
from django.db import IntegrityError
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import generics
from rest_framework.renderers import JSONRenderer
from rest_framework import status
#from allauth.account.views import LoginView
#from allauth.socialaccount.providers.google.views import GoogleOAuth2Adapter
#from allauth.socialaccount.providers.oauth2.client import OAuth2Client
#from dj_rest_auth.registration.views import SocialLoginView
from drf_social_oauth2.views import AccessToken, ConvertTokenView
from drf_social_oauth2.serializers import ConvertTokenSerializer
from oauthlib.oauth2.rfc6749.errors import (
    InvalidClientError,
    UnsupportedGrantTypeError,
    AccessDeniedError,
    MissingClientIdError,
    InvalidRequestError,
)
from .serializers import AttachmentSerializers, UserSerializers
from .models import AttachmentDetails, GoogleTokens
from .email import read_message

SCOPES = ['https://mail.google.com/']
#our_email = 'davidakinfenwa2@gmail.com'


def gmail_service(request):
    try:
        token = request.user.google_tokens.access_token
        print("Access", token)
        print("Refresh", request.user.google_tokens.refresh_token)
        creds = Credentials(
            token, refresh_token=request.user.google_tokens.refresh_token,token_uri="https://oauth2.googleapis.com/token",client_id=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,client_secret=settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET)
        
        service = build('gmail', 'v1', credentials=creds)
        return service
    except:
        return Response({
            "error": "Gmail service error"
        }, status=status.HTTP_401_UNAUTHORIZED)


def gmail_authenticate():
    creds = None
    # the file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # if there are no (valid) credentials availablle, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)
    return build('gmail', 'v1', credentials=creds)


def get_all_email(service, numberOfMessages=10, next_page_token=''):
    if service:
        results = service.users().messages().list(
            userId='me', maxResults=numberOfMessages, pageToken=next_page_token).execute()
        messages = results.get('messages', [])
        return results
    else:
        return "ERROR"


def get_all_messages(request):
    service = gmail_service(request)
    print(service)
    emails = get_all_email(service)
    print(emails)
    messages = emails.get('messages')
    all_messages = []
    batch = service.new_batch_http_request()
    for index, item in enumerate(messages):
        msg = service.users().messages().get(
            userId='me', id=messages[index]['id'], format='full')
        batch.add(msg)
    executed = batch.execute()
    response = batch._responses
    for res in response:
        parsed_object = json.loads(response.get(res)[1])
        message = read_message(service, parsed_object)
        all_messages.append(message)
    return {'messages': all_messages,
            'nextPageToken': emails.get('nextPageToken')
            }


def get_next_messages(request, next_page_token, numberOfMsg=10):
    service = gmail_service(request)
    emails = get_all_email(service, numberOfMsg, next_page_token)
    messages = emails.get('messages')
    all_messages = []
    batch = service.new_batch_http_request()
    for index, item in enumerate(messages):
        msg = service.users().messages().get(
            userId='me', id=messages[index]['id'], format='full')
        batch.add(msg)
    executed = batch.execute()
    response = batch._responses
    for res in response:
        parsed_object = json.loads(response.get(res)[1])
        message = read_message(service, parsed_object)
        all_messages.append(message)
    return {'messages': all_messages,
            'nextPageToken': emails.get('nextPageToken')
            }


def all_messages():
    service = gmail_authenticate()
    emails = get_all_email()
    messages = emails.get('messages')
    all_messages = []
    batch = service.new_batch_http_request()
    for index, item in enumerate(messages):
        msg = service.users().messages().get(
            userId='me', id=messages[index]['id'], format='full')
        batch.add(msg)
    executed = batch.execute()
    response = batch._responses
    for res in response:
        parsed_object = json.loads(response.get(res)[1])
        all_messages.append(parsed_object)
    return {'messages': all_messages,
            'nextPageToken': emails.get('nextPageToken')
            }


@api_view(['GET'])
def next_messages_with_attachment(request, token):
    service = gmail_service(request)
    emails = get_all_email(service, 100, token)
    messages = emails.get('messages')
    all_messages = []
    batch = service.new_batch_http_request()
    for index, item in enumerate(messages):
        msg = service.users().messages().get(
            userId='me', id=messages[index]['id'], format='full')
        batch.add(msg)
    executed = batch.execute()
    response = batch._responses
    for res in response:
        parsed_object = json.loads(response.get(res)[1])
        message = read_message(service, parsed_object)
        if message.get('attachment'):
            all_messages.append(message)

    return Response({'messages': all_messages,
                     'nextPageToken': emails.get('nextPageToken')
                     })


@api_view(['GET'])
def all_messages_with_attachment(request):
    service = gmail_service(request)
    emails = get_all_email(service, 100)
    messages = emails.get('messages')
    all_messages = []
    batch = service.new_batch_http_request()
    for index, item in enumerate(messages):
        msg = service.users().messages().get(
            userId='me', id=messages[index]['id'], format='full')
        batch.add(msg)
    executed = batch.execute()
    response = batch._responses
    for res in response:
        parsed_object = json.loads(response.get(res)[1])
        message = read_message(service, parsed_object)
        if message.get('attachment'):
            all_messages.append(message)

    return Response({'messages': all_messages,
                     'nextPageToken': emails.get('nextPageToken')
                     })


"""
class MyAccountAdapter(GoogleOAuth2Adapter):

    def get_login_redirect_url(self, request):
        print(request.method)
        print(request.GET)
        return "/test/?token="

"""


@api_view(['GET'])
def test_view(request):
    return HttpResponse("")


def logout(request):
    Logout(request)
    return redirect('/')


class ConverttokenView(ConvertTokenView):
    def post(self, request: Request, *args, **kwargs):
        code = request.data.get("code")
        res = requests.post(url="https://oauth2.googleapis.com/token", data={
        "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
        "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
        "redirect_uri": "postmessage",
        "grant_type": 'authorization_code',
        "code": code
        })
        response = res.json()
        data={
        "client_id": "JzgrLAbac0aWaElmiSH2Afx5R2VAwBE7epiFV91o",
        "client_secret": "9CgTFPwM2R0RUJPwxCGKeEqRCaCqfcSB9ArO1OfQvd3JHHO1B1O734j1VrzCIGsUm8py0BkayaYuwJAU91ImhXSTRm8wMpl09zwRhUjuUeLwnR3JYb0bdsmVbAopgmer",
        "backend": "google-oauth2",
        "grant_type": 'convert_token',
        "token": response.get('access_token')
    }
        serializer = ConvertTokenSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        # Use the rest framework `.data` to fake the post body of the django request.
        request._request.POST = request._request.POST.copy()
        for key, value in serializer.validated_data.items():
            request._request.POST[key] = value

        try:
            url, headers, body, status = self.create_token_response(request._request)
        except InvalidClientError:
            return Response(
                data={'invalid_client': 'Missing client type.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except MissingClientIdError as ex:
            return Response(
                data={'invalid_request': ex.description},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InvalidRequestError as ex:
            return Response(
                data={'invalid_request': ex.description},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except UnsupportedGrantTypeError:
            return Response(
                data={'unsupported_grant_type': 'Missing grant type.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except AccessDeniedError:
            return Response(
                {'access_denied': f'The token you provided is invalid or expired.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except IntegrityError as e:
            if 'email' in str(e) and 'already exists' in str(e):
                return Response(
                    {'error': 'A user with this email already exists.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                return Response(
                    {'error': 'Database error.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        fetchmail = json.loads(body)
        user = AccessToken.objects.get(
        token=convert_response.get("access_token")).user

        # Save google tokens
        if user.google_tokens:
            gt = user.google_tokens
            gt.access_token = response.get("access_token")
            gt.refresh_token = response.get("refresh_token")
            gt.save()
        else:
            gt = GoogleTokens.objects.create(access_token=response.get("access_token"), refresh_token=response.get("refresh_token"), user=user)
        return Response({"google": response, "fetch_mail": fetchmail})


@api_view(['GET'])
def get_token(request):
    res = requests.post(url="https://oauth2.googleapis.com/token", data={
        "client_id": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_KEY,
        "client_secret": settings.SOCIAL_AUTH_GOOGLE_OAUTH2_SECRET,
        "redirect_uri": "postmessage",
        "grant_type": 'authorization_code',
        "code": request.GET.get('code')
    })
    response = res.json()
    convert_res = requests.post(url=f"{settings.CUSTOM_HOST}/auth/convert-token/", data={
        "client_id": "JzgrLAbac0aWaElmiSH2Afx5R2VAwBE7epiFV91o",
        "client_secret": "9CgTFPwM2R0RUJPwxCGKeEqRCaCqfcSB9ArO1OfQvd3JHHO1B1O734j1VrzCIGsUm8py0BkayaYuwJAU91ImhXSTRm8wMpl09zwRhUjuUeLwnR3JYb0bdsmVbAopgmer",
        "backend": "google-oauth2",
        "grant_type": 'convert_token',
        "token": response.get('access_token')
    })

    convert_response = convert_res.json()
    user = AccessToken.objects.get(
        token=convert_response.get("access_token")).user
    print("Access token user")
    # Save google tokens
    if user.google_tokens:
        gt = user.google_tokens
        gt.access_token = response.get("access_token")
        gt.refresh_token = response.get("refresh_token")
        gt.save()
    else:
        gt = GoogleTokens.objects.create(access_token=response.get(
            "access_token"), refresh_token=response.get("refresh_token"), user=user)
    return Response({"google": response, "fetch_mail": convert_response})


# Create your views here.
@api_view(['GET'])
def home(request):
    return Response(get_all_messages(request))


@api_view(['GET'])
def next_page(request, token):
    return Response(get_next_messages(request, token))


class CreateAttachmentDetails(generics.CreateAPIView):
    serializer_class = AttachmentSerializers

    def perform_create(self, serializer):
        return serializer.save(user=self.request.user)


class ListAttachmentDetails(generics.ListAPIView):
    serializer_class = AttachmentSerializers

    def get_queryset(self):
        return AttachmentDetails.objects.filter(user=self.request.user)


@api_view(['GET'])
def get_user(request):
    user = request.user
    serializer = UserSerializers(user)
    return Response(serializer.data)


@api_view(['GET'])
def message_obj_view(request):
    return Response(all_messages())


def convert_to_text(attachment, attachment_type):
    print("Starting conversion to text")

    file = urlsafe_b64decode(attachment)
    print("attachment decoded")

    if 'pdf' in attachment_type:
        images = convert_from_bytes(file)
        print("Converted to image")

        #text = pytesseract.image_to_string(images[0]).encode("utf-8")
        text = ""
        for page_number, page_data in enumerate(images):
            print("Start pdf tesseract")
            text += pytesseract.image_to_string(page_data)
            print("End pdf tesseract")


    elif 'image' in attachment_type:
        print("Start image ")

        image = Image.open(BytesIO(file))
        print("Image Opened")
        text = pytesseract.image_to_string(image)
        print("Image converted")

    else:
        text = file
    
    print("Text Converted")

    return text


@api_view(['GET'])
def process_attachment_with_eden_ai(request, id):
    service = gmail_service(request)
    
    msg = service.users().messages().get(userId='me', id=id, format='full').execute()
    data = read_message(service, msg)
    # Get attachment and convert
    attachment = data.get('attachment')
    attachment = attachment.replace("_", '/')
    attachment = attachment.replace("-", '+')
    attachment_type = data.get('attachment_type')

    #Decode attachment
    attachment_list = []
    results = []

    file = b64decode(attachment)
     
    if 'pdf' in attachment_type:
        #Convert pdf to iamge and save in temp file
        images = convert_from_bytes(file)
        for page_number, page_data in enumerate(images):
            file_path = settings.BASE_DIR / f"{id}{len(attachment_list)}.jpg"
            page_data.save(file_path)
            attachment_list.append(file_path)

    elif 'image' in attachment_type:
        extension = guess_extension(attachment_type)
        file_path = settings.BASE_DIR / f"{id}{len(attachment_list)}{extension}"

        #Write to temp file
        with open(file_path, "wb") as f:
            f.write(file)
        #Add path to list
        attachment_list.append(file_path)
    else:
        text = file
        return Response({"value": text})


    for path in attachment_list:
        print("Stated eden ai")
        headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZTQxYmNlMGItNGFmMi00Y2Y5LWIzOWYtZTQ0ZGRjM2RlYzc3IiwidHlwZSI6ImFwaV90b2tlbiJ9.HXix9uWIZybb1uJP5JnBxHzasJci4hPUezDAFGaxOKs"}

        url = "https://api.edenai.run/v2/ocr/identity_parser"
        data = {"providers": "amazon"}
        files = {'file': open(path, 'rb')}
        response = requests.post(url, data=data, files=files, headers=headers)

        result = response.json()
        results.append(result)
        os.remove(path)
        print("Finished Eden ai")


    return Response({"info": results, 
    "value": convert_to_text(attachment, attachment_type)
    })


@api_view(['GET'])
def process_attachment_test(request, id):
    service = gmail_service(request)
    msg = service.users().messages().get(userId='me', id=id, format='full').execute()
    data = read_message(service, msg)
    attachment = data.get('attachment')
    attachment = attachment.replace("_", '/')
    attachment = attachment.replace("-", '+')
    attachment_type = data.get('attachment_type')
    
    file = b64decode(attachment)
    
    images = convert_from_bytes(file)
    for page_number, page_data in enumerate(images):
        try:
            page_data.save(settings.BASE_DIR / f"file{page_number}.jpg")
        except:
            raise

    try:
        f = b64decode(attachment)
        with open(settings.BASE_DIR / "file.jpg", "wb") as file:
            file.write(f)
    except:
        raise    

    return HttpResponse("Success")


    headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoiZTQxYmNlMGItNGFmMi00Y2Y5LWIzOWYtZTQ0ZGRjM2RlYzc3IiwidHlwZSI6ImFwaV90b2tlbiJ9.HXix9uWIZybb1uJP5JnBxHzasJci4hPUezDAFGaxOKs"}

    url = "https://api.edenai.run/v2/ocr/identity_parser"
    data = {"providers": "amazon"}
    files = {'file': open(settings.BASE_DIR / "file.jpg", 'rb')}
    response = requests.post(url, data=data, files=files, headers=headers)

    result = response.json()
    print(result['amazon'])

    return Response(result)

