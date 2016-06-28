"""Contains all the imports and methods from the other test programs."""

import json
import webbrowser

import httplib2
import os
import datetime

from apiclient import discovery
import oauth2client
from oauth2client import client
from oauth2client import tools



import sqlite3
from sqlite3 import Error


try:
    import argparse
    flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
except ImportError:
    flags = None

CREDENTIALS_DIR = "/Users/alee/Documents/secret"
CLIENT_SECRET_FILE = 'client_secret.json'
CREDENTIALS_FILE = 'credentials.json'
DB_FILE = 'intellibroad.db'
APPLICATION_NAME = 'IntelliBroad'


"""API-RELATED METHODS"""

def create_api_service(): 
    """Fetches or creates credentials, initializes resource objects Google Apps Admin SDK and Google Calendar API resource 
        returns tuple of resource objects: (Admin SDK Object, Calendar API Object)
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

    http_auth = credentials.authorize(httplib2.Http())

    calendar_service = discovery.build("calendar", "v3", http = http_auth)

    admin_service = discovery.build('admin', 'directory_v1', http = http_auth) # NOTE: Different service 

    return (admin_service, calendar_service)

def update_calendars(admin_service, calendar_service):
    """Gets room email addresses from Google Apps Admin SDK, and adds them to own list of calendars.
        Returns a list containing the email addresses that were successfully added.

        admin_service and calendar_service are the resource objects for their respective APIs
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
            calendar_service.calendarList().insert(body = request_body).execute()
            added_room_emails.append(i['id'])
        except Exception, e:
            # print(e)
            # some of the calendars we don't have access to, API returns 404 errors when we attempt to add
            outputString = "\033[1m*404 error* \033[0m\t"
        outputString += i["name"]
        print(outputString)

    return added_room_emails

def pull_calendar_events(calendar_service, calendarId):
    """
    Pulls all events from one calendar. Returns list of events from API call ('items' field). Attempts to use updatedMin to only pull events since last updated\n
    calendar_service: resource object for Calendar API
    calendarId: email address for specific room calendar
    """

    # Edit to set the upper bound for start times for which events should be returned.
    # This prevents us from pulling events in the distant future, for which there are no invitees save the organizer.
    timeMax = (datetime.datetime.now() + datetime.timedelta(days=14)).isoformat('T')

    # Edit to determine what is returned by API 
    fieldString = "items(attendees(displayName,email,optional,resource,responseStatus),creator(displayName,email),description,htmlLink,id,location,organizer(displayName,email),start/dateTime,status,summary,updated),nextPageToken"

    # Edit to determine the upper bound of event start time that should be fetched
    timeString = timeMax + 'z' # for some reason the Google APIs really need that 'z'

    lastUpdated = get_last_update() # We know the last pull was later than the most recently-updated event in the database.
    eventList = [] # List of events returned by API.
    nextPageToken = ""
    while True:
        print("------NEW REQUEST------")

        response = calendar_service.events().list(calendarId=calendarId, updatedMin=lastUpdated,orderBy="updated", pageToken = nextPageToken, timeMax=timeString, fields = fieldString).execute()
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


"""DATABASE-RELATED METHODS"""

def create_connection(db_path):
	"""Creates and returns a database connection to a SQLite database\n
	db_path: path to database"""
	try:
		conn = sqlite3.connect(db_path)
		print("Created connection with " + db_path)
		return conn
	except Error as e:
		print(e)
	return None 

def create_tables():
	"""Creates tables if they don't already exist"""

	conn = create_connection(DB_FILE)
	c = conn.cursor()

	# Gonna start by hardcoding in the three tables we want.

	c.execute("CREATE TABLE IF NOT EXISTS events ( event_id text PRIMARY KEY, name text, start_time text, location text, last_update text )")
	c.execute("CREATE TABLE IF NOT EXISTS employees ( employee_id text PRIMARY KEY, name text )")
	c.execute("CREATE TABLE IF NOT EXISTS invitations ( event_id text, employee_id text, response text)")

	print("Tables written successfully")

	conn.commit()
	conn.close()

	print("Commited changes and closed connection to database")

def get_last_update():
    """Returns the most recent timestring at which an event in the database was updated, or None if the database is empty.
    """
    conn = create_connection(DB_FILE)

    c = conn.cursor()
    c.execute("SELECT max(last_update) FROM events")

    last_update = c.fetchall()[0][0] # for some reason the datestring is in a tuple inside a list

    conn.close() # close database
    print("Closed connection to database")
    print("Latest updated event was " + str(last_update))
    return last_update

def push_events_to_database(items):
	"""Takes calendar data and writes each event's details to database. \n
	\t items: List of events returned by API call 
	"""

	conn = create_connection(DB_FILE)
	c = conn.cursor()

	print("EXECUTING push_events_to_database")

	def make_row_writer(c, table_name, num_columns):
		"""Returns a method that writes to a specific table, taking only the correct 
		length tuple for that table. \n

		c: sqlite3 Cursor object
		table_name: string of the name of table
		num_columns: int, number of columns in the table
		"""
		def write_row(*args):
			assert len(args) == num_columns

			executeString = 'INSERT OR IGNORE INTO %s VALUES (' % table_name

			for i in range(0, num_columns):
				executeString += '?,'
			# so the goal here is to build the command string with the placeholders, 
			# e.g. INSERT INTO <name> VALUES (?, ?, ?)
			# and then insert the tuple of values via sqlite3 parameter substitution

			executeString = executeString[:-1] # clip the last comma
			executeString += ');' # close parens
			# print("executeString: " + executeString)

			c.execute(executeString, args)

		return write_row


	# need some help with abstraction!!!!

	write_events = make_row_writer(c, 'events', 5)
	write_employees = make_row_writer(c, 'employees', 2)
	write_invitations = make_row_writer(c, 'invitations', 3)

	for item in items:
		if item['status'] != 'cancelled':
			# print(json.dumps(item, indent=4, separators=(':',',')))
			try:
				write_events(item['id'], item['summary'], item['start']['dateTime'], item['location'], item['updated'])

				for attendee in item['attendees']:
					try:		
						write_employees(attendee['email'], attendee['displayName'])
						write_invitations(item['id'], attendee['email'], attendee['responseStatus'])
					except KeyError, e:
						# print('Key ' + str(e) + ' not found. Not writing person and invitation entry.')
						# print(item)

						# Now, if we don't have a displayName for a person, we use their email.
						write_employees(attendee['email'], attendee['email'])
						write_invitations(item['id'], attendee['email'], attendee['responseStatus'])

			except KeyError, e:
				print("Key " + str(e) + ' not found. Not writing event entry.')
				print(item)


	conn.commit()
	conn.close()

	print("Committed changes and closed database connection")


