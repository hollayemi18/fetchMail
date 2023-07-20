from base64 import urlsafe_b64decode
from email.message import Message
import re

# utility functions
def get_size_format(b, factor=1024, suffix="B"):
    """
    Scale bytes to its proper byte format
    e.g:
        1253656 => '1.20MB'
        1253656678 => '1.17GB'
    """
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if b < factor:
            return f"{b:.2f}{unit}{suffix}"
        b /= factor
    return f"{b:.2f}Y{suffix}"


def clean(text):
    # clean text for creating a folder
    return "".join(c if c.isalnum() else "_" for c in text)

def parse_parts(service, parts,msg_id=None):
    message_value = ''
    attachment_type = ''
    attachment_name = ''
    attachment = None
    if parts:
        for part in parts:
            filename = part.get("filename")
            mimeType = part.get("mimeType")
            body = part.get("body")
            data = body.get("data")
            file_size = body.get("size")
            part_headers = part.get("headers")
            if isinstance(data,bytes):
                message_value += data.decode()
            
            if part.get("parts"):
                # recursively call this function when we see that a part
                # has parts inside
                parts_message = parse_parts(service, part.get("parts")).get('message')
                if parts_message:
                    message_value += parts_message        
                
            if mimeType == "text/plain":
                # if the email part is text plain
                if data:
                    text = urlsafe_b64decode(data).decode()
                    message_value = text
            elif mimeType == "text/html":
                message_value = (urlsafe_b64decode(data)).decode()
                
            else:
                # attachment other than a plain text or HTML
                for part_header in part_headers:
                    part_header_name = part_header.get("name")
                    part_header_value = part_header.get("value")
                    
                    if part_header_name == "Content-Type":
                        temp_email = Message()
                        temp_email['content-type'] =  part_header_value
                        params = temp_email.get_params()
                        try:
                            attachment_type = params[0][0]
                            attachment_name = params[1][1]
                        except IndexError:
                            pass


                    if part_header_name == "Content-Disposition":
                        if "attachment" in part_header_value:
                            #Try to get content type 
                            attachment_id = body.get("attachmentId")
                            attachment = service.users().messages().attachments().get(id=attachment_id, userId='me', messageId=msg_id).execute()
                            data = attachment.get("data")
                            attachment = data
                            #attachment = re.sub(r"_","/",data)
                            #attachment = re.sub(r"-","+",attachment)
                            #attachment = urlsafe_b64decode(attachment.encode('UTF-8'))

    return {
        'message' : message_value,
        'attachment': attachment,
        'attachment_type': attachment_type
    }

def read_message(service, msg):
    """
    This function takes Gmail API `service` and the given `message_id` and does the following:
        - Downloads the content of the email
        - Prints email basic information (To, From, Subject & Date) and plain/text parts
        - Creates a folder for each email based on the subject
        - Downloads text/html content (if available) and saves it under the folder created as index.html
        - Downloads any file that is attached to the email and saves it in the folder created
    """
    #msg = service.users().messages().get(userId='me', id=message_id, format='full').execute()
    # parts can be the message body, or attachments
    payload = msg['payload']
    headers = payload.get("headers")
    parts = payload.get("parts")
    subject = "email"
    snippet = msg.get('snippet')
    from_email = ''
    date = None
    has_subject = False

    if headers:
        # this section prints email basic info & creates a folder for the email
        for header in headers:
            name = header.get("name")
            value = header.get("value")
            if name.lower() == 'from':
                # we print the From address
                from_email = value
 
            if name.lower() == "to":
                # we print the To address
                to = value
            if name.lower() == "subject":
                # make our boolean True, the email has "subject"
                has_subject = True
                # make a directory with the name of the subject
                subject = value
                # we will also handle emails with the same subject name
               
            if name.lower() == "date":
                # we print the date when the message was sent
                date=value
    parts = parse_parts(service, parts, msg.get('id'))
    return {
        'message': parts.get('message'),
        'attachment': parts.get('attachment'),
        'attachment_type': parts.get('attachment_type'),
        'subject': subject,
        'id' : msg.get('id'),
        'snippet' : snippet ,
        'from': from_email
    }
    