import json
import webbrowser

import httplib2

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools

import os

import datetime

try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

CREDENTIALS_DIR = "/Users/alee/Documents/secret"
CLIENT_SECRET_FILE = 'client_secret.json'
CREDENTIALS_FILE = 'credentials.json'
APPLICATION_NAME = 'IntelliBroad'



# Working off Google's own Calendar API example

def get_credentials(): 
    credentials_path = os.path.join(CREDENTIALS_DIR, CREDENTIALS_FILE)
    store = oauth2client.file.Storage(credentials_path)
    credentials = store.locked_get()

    if not credentials or credentials.invalid:
        client_secret_path = os.path.join(CREDENTIAL_DIR, CLIENT_SECRET_FILE)
        flow = client.flow_from_clientsecrets(client_secret_path, 
            scope='https://www.googleapis.com/auth/admin.directory.resource.calendar',
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')

        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)

        print("Storing credentials to: " + credentials_path)

    print(credentials.get_access_token())

    return credentials



credentials = get_credentials()

http_auth = credentials.authorize(httplib2.Http())

service = discovery.build("calendar", "v3", http = http_auth)

calendarList = service.calendarList().list().execute()

for i in calendarList['items']:
    print(i["id"])






