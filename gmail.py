from __future__ import print_function
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import re

pattern='(\d{2}):(\d{2}):(\d{2})'

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']

def main():
    """Shows basic usage of the Gmail API.
    Lists the user's Gmail labels.
    """
    global msg
    creds = None
    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.json'):
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.json', 'w') as token:
            token.write(creds.to_json())

    service = build('gmail', 'v1', credentials=creds)

    # Call the Gmail API
    results = service.users().messages().list(userId='me',maxResults=1,labelIds=['INBOX'],q="from:edis@cdslindia.co.in is:unread").execute()
    message = results.get('messages', [])[0]

    if not message:
        print('No messages from CDSL found.')
    else:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        print("Your latest message from CDSL :")
        email_data=msg['payload']['headers']
        for values in email_data:
            name=values["name"]
            if name == "From":
                from_name = values["value"]
                print(msg['snippet'])
                matchOTP = re.search('(\d{6})', str(msg['snippet']))
                print(matchOTP.group())

if __name__ == '__main__':
    main()