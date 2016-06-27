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

from create_tables import create_connection

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
        client_secret_path = os.path.join(CREDENTIAL_DIR, CLIENT_SECRET_FILE)
        flow = client.flow_from_clientsecrets(client_secret_path, 
            scope='https://www.googleapis.com/auth/admin.directory.resource.calendar',
            redirect_uri='urn:ietf:wg:oauth:2.0:oob')

        if flags:
            credentials = tools.run_flow(flow, store, flags)
        else: # Needed only for compatibility with Python 2.6
            credentials = tools.run(flow, store)

        print("Storing credentials to: " + credentials_path)


    return credentials

def get_last_update(conn):
    """Returns the most recent timestring at which an event in the database was updated\n
    conn: an sqlite3 database connection object 
    """
    c = conn.cursor()
    c.execute("SELECT max(last_update) FROM events")

    last_update = c.fetchall()[0][0] # for some reason the datestring is in a tuple inside a list

    conn.close() # close database
    print("Closed connection")
    print("Latest updated event was " + str(last_update))
    return last_update


credentials = get_credentials()

http_auth = credentials.authorize(httplib2.Http())

service = discovery.build("calendar", "v3", http = http_auth)

calendarId = "broadinstitute.com_36393736333139393439@resource.calendar.google.com"

timeString = datetime.datetime.now().isoformat("T") + 'z' # get_last_update(create_connection('intellibroad.db')) #datetime.datetime.now().isoformat('T')

nextPageToken = ""

updatedMin = "2016-06-19T22:44:09.139z"

fieldString = "items(attendees(displayName,email,optional,resource,responseStatus),creator(displayName,email),description,htmlLink,id,location,organizer(displayName,email),start/dateTime,status,summary,updated),nextPageToken"

# response = service.events().list(calendarId=calendarId, orderBy="updated", pageToken = nextPageToken, timeMax=timeString, updatedMin = timeString,fields = fieldString).execute()

# print(json.dumps(response, indent=4, separators=(',', ':')))


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


def pull_data_from_google(credentials):
    """Adds all room calendars to own list, then pulls list of recent events from each.
    Returns a list of dicts, where each dict is one API response. \n
    credentials: Credentials object from Google Python SDK
    """
    pass

eventList = pull_calendar_events(calendarId)


from push_data_to_tables import push_events_to_database

push_events_to_database(eventList)






