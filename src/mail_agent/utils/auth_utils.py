import base64
import os.path

import google.auth.exceptions
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.errors import HttpError
from mail_agent.config import CREDENTIALS

# If modifying these scopes, delete the file token.json.
SCOPES = ['https://mail.google.com/']
USER_TOKENS = 'token.json'

def authorize_google_mail() -> str: # type: ignore
    """ Gets a valid Google access token with the mail scope permissions. """

    creds = check_user_authentication()

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("Your auth expired")
            creds.refresh(Request())
        else:
            print("Authenticating for first time")
            flow = InstalledAppFlow.from_client_config(
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

def check_user_authentication():
    creds =  None
    if os.path.exists(USER_TOKENS):
        try:
            creds = Credentials.from_authorized_user_file(USER_TOKENS, SCOPES)
            creds.refresh(Request())
        except google.auth.exceptions.RefreshError as error:
            # if refresh token fails, reset creds to none.
            creds = None
            print(f'An error occurred: {error}')
    
    return creds # this can act as both if authentiation, and as cred if there is any cre

