"""
PURPOSE: To obtain the calendars of all conference rooms in the Broad. 
We can use their email addresses to look up the previous meetings that 
occurred in those rooms.
"""
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
# CREDENTIALS_FILE = 'credentials.json'
APPLICATION_NAME = 'IntelliBroad'


credential_path = os.path.join(CREDENTIALS_DIR, CLIENT_SECRET_FILE)

flow = client.flow_from_clientsecrets(credential_path, 
	scope = "https://www.googleapis.com/auth/admin.directory.resource.calendar",
	redirect_uri = "urn:ietf:wg:oauth:2.0:oob")

auth_uri = flow.step1_get_authorize_url()

webbrowser.open(auth_uri)

auth_code = raw_input('Enter the auth code: ')

credentials = flow.step2_exchange(auth_code)
http_auth = credentials.authorize(httplib2.Http())

service = discovery.build('admin', 'directory_v1', http = http_auth)

calendarListResource = service.resources().calendars().list(customer="my_customer").execute()

conference_room_emails = []

for calendar in calendarListResource["items"]:
	if calendar["resourceType"] == "Conference Room":
		conference_room_emails.append({"id": calendar["resourceEmail"],"name": calendar["resourceName"]})

string = json.dumps(conference_room_emails, indent=4, separators=(',', ':'))

print(string)

f = open("conference_room_emails.json", 'w')
f.write(string)
f.close()

