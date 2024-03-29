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
    """get OAauth2 credentials from local storage OR create new credentials\n
        returns Credentials object
    """
    credentials_path = os.path.join(CREDENTIALS_DIR, CREDENTIALS_FILE)
    store = oauth2client.file.Storage(credentials_path)
    credentials = store.locked_get()

    if not credentials or credentials.invalid:
        client_secret_path = os.path.join(CREDENTIALS_DIR, CLIENT_SECRET_FILE)
        flow = client.flow_from_clientsecrets(client_secret_path, 
            scope='https://www.googleapis.com/auth/admin.directory.resource.calendar https://www.googleapis.com/auth/calendar',
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')

        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)

        print("Storing credentials to: " + credentials_path)

    return credentials


credentials = get_credentials()

http_auth = credentials.authorize(httplib2.Http())

service = discovery.build("calendar", "v3", http = http_auth)

admin_service = discovery.build('admin', 'directory_v1', http = http_auth) # NOTE: Different service 

def update_calendars():
    """Gets room email addresses from Google Apps Admin SDK, and adds them to own list of calendars.
        Returns a list containing the email addresses that were successfully added.
    """

    calendarListResource = admin_service.resources().calendars().list(customer="my_customer").execute()

    print("Requesting list of resources from Google Apps Admin SDK")

    conference_room_emails = [] # list containing all room emails and names

    for calendar in calendarListResource["items"]:
        if calendar["resourceType"] == "Conference Room":
            conference_room_emails.append({"id": calendar["resourceEmail"],"name": calendar["resourceName"]})

    # print(json.dumps(conference_room_emails, indent=4, separators=(',', ':')))

    print("Begin adding calendars to list")

    added_room_emails = [] # the list of calendar emails that were successfully added, that we will be puliing data from

    for i in conference_room_emails:
        request_body = {
            'id': i["id"]
        }

        outputString = "add success \t"
        try:
            service.calendarList().insert(body = request_body).execute()
            added_room_emails.append(i['id'])
        except Exception, e:
            # print(e)
            # some of the calendars we don't have access to, API returns 404 errors when we attempt to add
            outputString = "\033[1m*404 error* \033[0m\t"
        outputString += i["name"]
        print(outputString)

    return added_room_emails


def pull_calendar_events(calendarId, timeMax=datetime.datetime.now().isoformat('T')):
    """
    Pulls all events from one calendar. Returns list of events from API call ('items' field)
    timeMax: Timestring for upper bound of item start time (to prevent pulling distant-future events)
    """

    # NOTE: Pulling events since last update time will be implemented later!


    eventList = [] # List of events returned by API.
    nextPageToken = ""
    while True:
        print("------NEW REQUEST------")

        response = service.events().list(calendarId=calendarId, orderBy="updated", pageToken = nextPageToken, timeMax=timeString,fields = fieldString).execute()
        if 'items' in response:
            eventList += response['items'] # if the response has events, add them

        if "nextPageToken" not in response:
            print("DONE")
            break 
            # If there's no nextPageToken in response body, we break out and return what we have
        else:
            print("NEXT PAGE TOKEN: " + response['nextPageToken'])
            nextPageToken = response['nextPageToken'] # Otherwise, make another request for next page

    return eventList





