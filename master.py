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


# try:
#     import argparse
#     flags = argparse.ArgumentParser(parents=[tools.argparser]).parse_args()
# except ImportError:
#     flags = None

# credentials_dir = "/Users/alee/Documents/secret"
# client_secret_file = 'client_secret.json'
# credentials_file = 'credentials.json'
# db_file = 'intellibroad.db'

"""API-RELATED METHODS"""

def create_api_service(credentials_dir, client_secret_file, credentials_file): 
	"""Fetches or creates credentials, initializes resource objects Google Apps Admin SDK and Google Calendar API resource returns tuple of resource objects: (Admin SDK Object, Calendar API Object)
	\n
	credentials_dir: string, path to directory where credential and client secret files reside
	client_secret_file: string, name of client secret file
	credentials_file: string, name of credentials file
	"""
	credentials_path = os.path.join(credentials_dir, credentials_file)
	store = oauth2client.file.Storage(credentials_path)
	credentials = store.locked_get()

	if not credentials or credentials.invalid:
		client_secret_path = os.path.join(credentials_dir, client_secret_file)
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

def update_calendars(admin_service, calendar_service, excluded_calendars = []):
	"""Gets room email addresses from Google Apps Admin SDK, and adds them to own list of calendars.
		Returns a list of dicts (keys: 'id', 'summary') for calendars that were successfully added.

		admin_service and calendar_service are the resource objects for their respective APIs
		excluded_calendars: list of calendar emails which will not be pulled (place buggy/irrelevant calendars here)
	"""

	calendarListResource = admin_service.resources().calendars().list(customer="my_customer").execute()

	print("Requesting list of resources from Google Apps Admin SDK")

	conference_room_emails = [] # list containing all room emails and names

	# First, we add all conference rooms from the API
	for calendar in calendarListResource["items"]:
		if calendar["resourceType"] == "Conference Room":
			conference_room_emails.append({"id": calendar["resourceEmail"],"summary": calendar["resourceName"]})

	print("Getting and adding new calendars from Admin API...")

	for i in conference_room_emails:
		request_body = {
			'id': i["id"]
		}

		outputString = "add success \t"
		try:
			calendar_service.calendarList().insert(body = request_body).execute()
			added_rooms.append(i)
		except Exception, e:
			# some of the calendars we don't have access to, API returns 404 errors when we attempt to add
			outputString = "\033[1m*" + str(e) + " error* \033[0m\t"
		outputString += i["summary"]
		# print(outputString)

	print("LIST OF ADDED CALENDARS:")

	listFromApi = calendar_service.calendarList().list(showHidden=True,fields='items(id,summary),nextPageToken').execute()['items']

	added_rooms = [] # rooms that have been added, we will be pulling from these

	for i in listFromApi:
		if 'resource.calendar.google.com' in i['id'] and i['id'] not in excluded_calendars:
			print(i['summary'])
			added_rooms.append(i)

	return added_rooms

def pull_calendar_events(calendar_service, calendarId, lastUpdated):
	"""
	Pulls all events from one calendar. Returns list of events from API call ('items' field). Attempts to use updatedMin to only pull events since last updated\n
	calendar_service: resource object for Calendar API
	calendarId: email address for specific room calendar
	lastUpdated: Time of previous update, in RFC 3339 timestring format (per Google API requirements)
	"""

	# Edit to set the upper bound for start times for which events should be returned.
	# This prevents us from pulling events in the distant future, for which there are no invitees save the organizer.
	timeMax = (datetime.datetime.now() + datetime.timedelta(days=14)).isoformat('T')

	# Edit to determine what is returned by API 
	fieldString = """items(attendees(displayName,email,optional,resource,responseStatus),creator(displayName,email),description,htmlLink,id,location,organizer(displayName,email),recurrence,start/dateTime,status,summary,updated),nextPageToken"""

	# Edit to determine the upper bound of event start time that should be fetched
	timeString = timeMax + 'z' # for some reason the Google APIs really need that 'z'

	eventList = [] # List of events returned by API.
	nextPageToken = ""
	while True:
		print("------NEW REQUEST------")
		try:
			response = calendar_service.events().list(calendarId=calendarId, updatedMin=lastUpdated,orderBy="updated", pageToken = nextPageToken, timeMax=timeString, fields = fieldString).execute()
		except Exception, e:
			raise e
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

def create_connection(db_file):
	"""Creates and returns a database connection to a SQLite database\n
	db_file: string, database location"""
	conn = sqlite3.connect(db_file)
	print("Created connection with " + db_file)
	return conn

def create_tables(db_file):
	"""Creates tables if they don't already exist\n
	db_file: string, database location
	"""

	conn = create_connection(db_file)
	c = conn.cursor()

	# Gonna start by hardcoding in the three tables we want.

	c.execute("CREATE TABLE IF NOT EXISTS events ( event_id text PRIMARY KEY, name text, description text, start_time text, recurrence text, location text, last_update text, htmlLink text)")
	c.execute("CREATE TABLE IF NOT EXISTS employees ( employee_id text PRIMARY KEY, name text )")
	c.execute("CREATE TABLE IF NOT EXISTS invitations ( event_id text, employee_id text, response text, UNIQUE (event_id, employee_id))")

	conn.commit()
	conn.close() 


def get_last_update(db_file, cal_id):
	"""Returns the most recent timestring at which an event in the given calendar was updated in the database, or None if the database is empty. \n
	db_file: string, database location
	cal_id: string, email address of calendar"""
	conn = create_connection(db_file)
	c = conn.cursor()

	queryString = """
	SELECT max(last_update) FROM events WHERE event_id IN 
	(SELECT event_id FROM invitations WHERE employee_id = ?)
	"""

	c.execute(queryString, (cal_id,))

	last_update = c.fetchall()[0][0] # for some reason the datestring is in a tuple inside a list

	conn.close() # close database
	print("Closed connection to database")
	print("Latest updated event was " + str(last_update))
	return last_update

def push_events_to_database(db_file, items):
	"""Takes calendar data and writes each event's details to database. \n
	db_file: string, database location
	items: List of events returned by API call 
	"""

	conn = create_connection(db_file)
	c = conn.cursor()

	print("EXECUTING push_events_to_database")

	def make_row_writer(c, table_name, num_columns, replace = False):
		"""Returns a method that writes to a specific table, taking only the correct 
		length tuple for that table. \n

		c: sqlite3 Cursor object
		table_name: string of the name of table
		num_columns: int, number of columns in the table
		replace: bool, if row id already exists, replace or ignore?
		"""
		behaviorString = "IGNORE" 

		if replace:
			behaviorString = "REPLACE"

		def write_row(*args):
			assert len(args) == num_columns

			executeString = 'INSERT OR %s INTO %s VALUES (' % (behaviorString, table_name)

			executeString += ','.join(["?"] * num_columns)
			# so the goal here is to build the command string with the placeholders, 
			# e.g. INSERT INTO <name> VALUES (?, ?, ?)
			# and then insert the tuple of values via sqlite3 parameter substitution

			executeString += ');' # close parens

			c.execute(executeString, args)

		return write_row
	
	write_events = make_row_writer(c, 'events', 8) # in cases of recurring events, we want the earliest to stay
	write_employees = make_row_writer(c, 'employees', 2, replace=True) # but in case of employees, we want newest name in database
	write_invitations = make_row_writer(c, 'invitations', 3)

	for item in items:
		if item['status'] != 'cancelled' and 'attendees' in item and 'summary' in item and 'start' in item:
			# we don't want cancelled events, we don't want private events for which we can't see
			# attendees, we don't want events without start times (because what would those be anyways)

			# IDs of recurring instances have an _ after them with a timestamp. Removing that makes 
			# all recurrences have identical IDs. The database will only accept the first one added,
			# and will ignore all others.
			item['id'] = item['id'].split('_')[0]

			# MAKE SURE THESE MATCH THE ORDER OF THE event TABLE COLUMNS!!!
			# Fields will get a space if they do not exist

			event_values = [
				item.get('id', ''),
				item.get('summary', ''), 
				item.get('description', ''), 
				item.get('start').get('dateTime', ''), 
				' '.join(item.get('recurrence', '')), 
				item.get('location', ''), 
				item.get('updated', ''), 
				item.get('htmlLink', '')
			]

			write_events(*event_values)

			# Now we add employees and invitations. If no screen name, use their email instead.

			for attendee in item['attendees']:
				write_employees(attendee['email'], attendee.get('displayName', attendee['email']))
				write_invitations(item['id'], attendee['email'], attendee['responseStatus'])	

	conn.commit()
	conn.close()

	# Lastly, before leaving, we create the hashes for the new events.
	create_event_hashes(db_file)

	print("Committed changes and closed database connection")

"""HASHING"""

def hash_event(attendees):
	"""Create a hash of an event based on its attendees. 
	Returns an integer, the result of the hash. \n
	attendees: List of strings to hash, should be employee_ids
	"""
	event_hash = 0 # Start out with an empty bitstring

	for i in attendees:
		index = hash(i) # We hash every ID to get a unique, random integer
		event_hash |= (1 << index % 32) 
		# Inside the parentheses essentially tells us which position in a chunk of 32 the event
		# hash would take (bc we're essentially dividing by 32, which in the 'large bitstring')
		# setup means pulling down chunks of 32 until the bit is at the last chunk
	return event_hash

def create_event_hashes(db_file):
	"""Creates a table with columns for event_id and hash. The hash is created based off of attendees. 
	If table is already created, update the table for new events.\n
	db_file: String, path to database
	"""
	print("Creating event hashes")

	conn = create_connection(db_file)
	conn.row_factory = lambda cursor, row: row[0] # returns first element from each row
	c = conn.cursor()

	# Create the table if it ain't there yet
	c.execute("CREATE TABLE IF NOT EXISTS event_hashes (event_id text PRIMARY KEY, hash integer)")

	# Get all events that are not already in event_hashes
	queryString = """SELECT event_id FROM events EXCEPT SELECT event_id FROM event_hashes"""
	c.execute(queryString)
	eventList = c.fetchall()
	
	for i in eventList:
		c.execute('SELECT employee_id FROM invitations WHERE event_id = ?', (i,))
		event_hash = hash_event(c.fetchall())
		c.execute('INSERT INTO event_hashes VALUES (?,?)', (i, event_hash))


	conn.commit()
	conn.close()

	# return employee_list





