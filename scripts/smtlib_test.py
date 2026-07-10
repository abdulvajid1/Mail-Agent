# import base64
# import os.path
# from email.message import EmailMessage

# from google.auth.transport.requests import Request
# from google.oauth2.credentials import Credentials
# from google_auth_oauthlib.flow import InstalledAppFlow
# from googleapiclient.discovery import build

# SCOPES = ["https://www.googleapis.com/auth/gmail.send"]


# def get_gmail_service():
#     creds = None
#     if os.path.exists("token.json"):
#         creds = Credentials.from_authorized_user_file("token.json", SCOPES)
#     if not creds or not creds.valid:
#         if creds and creds.expired and creds.refresh_token:
#             creds.refresh(Request())
#         else:
#             flow = InstalledAppFlow.from_client_secrets_file(
#                 "credentials.json", SCOPES
#             )
#             creds = flow.run_local_server(port=0)
#         with open("token.json", "w") as token:
#             token.write(creds.to_json())
#     return build("gmail", "v1", credentials=creds)


# def send_gmail(to: str, subject: str, body: str) -> dict:
#     service = get_gmail_service()
#     msg = EmailMessage()
#     msg["To"] = to
#     msg["Subject"] = subject
#     msg.set_content(body)
#     raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
#     return (
#         service.users()
#         .messages()
#         .send(userId="me", body={"raw": raw})
#         .execute()
#     )


# send_gmail(
#     "ops@example.com",
#     "Daily import finished",
#     "The 2026-05-21 import completed successfully.",
# )



###################################

# Source - https://stackoverflow.com/a/77486905
# Posted by Linda Lawton - DaImTo
# Retrieved 2026-07-10, License - CC BY-SA 4.0

#   To install the Google client library for Python, run the following command:
#   pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib


# from __future__ import print_function

import base64
import os.path
import smtplib
from email.mime.text import MIMEText

import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError



def getToken() -> str: # type: ignore
    """ Gets a valid Google access token with the mail scope permissions. """
    # If modifying these scopes, delete the file token.json.
    SCOPES = ['https://mail.google.com/']
    USER_TOKENS = 'token.json'
    CREDENTIALS = 'credentials.json'

    creds = None

    # The file token.json stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists(USER_TOKENS):
        try:
            creds = Credentials.from_authorized_user_file(USER_TOKENS, SCOPES)
            creds.refresh(Request())
        except google.auth.exceptions.RefreshError as error:
            # if refresh token fails, reset creds to none.
            creds = None
            print(f'An error occurred: {error}')
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                CREDENTIALS, SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(USER_TOKENS, 'w') as token:
            token.write(creds.to_json())

    try:
        return creds.token # type: ignore
    except HttpError as error:
        # TODO(developer) - Handle errors from authorization request.
        print(f'An error occurred: {error}')


def generate_oauth2_string(username, access_token, as_base64=False) -> str:

    # creating the authorization string needed by the auth server.
    #auth_string = 'user=%s\1auth=Bearer %s\1\1' % (username, access_token)

    auth_string = 'user=' + username + '\1auth=Bearer ' + access_token + '\1\1'
    if as_base64:
        auth_string = base64.b64encode(auth_string.encode('ascii')).decode('ascii')
    return auth_string


def send_email(host, port, subject, msg, sender, recipients):
    access_token = getToken()
    auth_string = generate_oauth2_string(sender, access_token, as_base64=True)

    msg = MIMEText(msg)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    server = smtplib.SMTP(host, port)
    server.starttls()
    server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
    server.sendmail(sender, recipients, msg.as_string())
    server.quit()


def main():
    host = "smtp.gmail.com"
    port = 587

    user = "bbad48882@gmail.com"

    subject = "Test email Oauth2"
    msg = "Hello world"
    sender = user
    recipients = [user]
    send_email(host, port, subject, msg, sender, recipients)


if __name__ == '__main__':
    main()
