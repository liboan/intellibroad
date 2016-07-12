import datetime
import argparse
from oauth2client import tools

parser = argparse.ArgumentParser(parents=[tools.argparser], description='Runs the methods in master.py. \nWill soon do one whole update cycle.')
# we need to add the oauth2 argparser in order for it to play game with our own

# arguments for specific file locations
parser.add_argument('-db', help='database file path', default="intellibroad.db")
parser.add_argument('--cred_dir', help='credentials directory', default='/Users/alee/Documents/secret')
parser.add_argument('--secret', help='secrets file', default='client_secret.json')
parser.add_argument('--credentials', help='credentials file', default='credentials.json')

# argument for grabbing a specific calendar
parser.add_argument('-c', metavar = 'calendar', help='calendar email address, will pull all events from calendar')

parser.add_argument('--get-all', help='get all events since beginning of time', action='store_true') # arg to force get all events, instead of most recently updated
parser.add_argument('--get-from', default=0, help='get all events from 1 to 20 days back') # arg to force get last 14 days, instead of most recently updated

args = parser.parse_args()

print("####ARGS####")
print(args)

credentials_dir = args.cred_dir # "/Users/alee/Documents/secret"
client_secret_file = args.secret # 'client_secret.json'
credentials_file = args.credentials # 'credentials.json'
# db_file = args.db # 'intellibroad.db'

from master import *

def update(db_file = args.db):
	"""Master update function, should be called regularly to pull event data and push it to database.\n
	Returns 0 if no error, 1 if there is an error.
	"""

	# List of excluded calendars- maybe this should be moved somewhere else
	excludeList = ['broadinstitute.com_2d3837373534343233373531@resource.calendar.google.com']
	# Instrument-RealTimePCR forces a full update every time, stretching out the update process.

	try:

		"""TIMING"""
		start = datetime.datetime.now()
		""""""""""""

		create_tables(db_file)

		admin_service, calendar_service = create_api_service(args, credentials_dir, client_secret_file, credentials_file)

		eventList = []

		if args.c:
			# if a specific calendar email is specified, pull all events from that calendar
			eventList += pull_calendar_events(calendar_service, args.c, None)
		else:
			calendarList = update_calendars(admin_service, calendar_service, excludeList)

			for i in calendarList:
				lastUpdated = get_last_update(db_file, i['id'])

				if args.get_all:
					lastUpdated = None # for force grabbing all events
				if args.get_from:
					lastUpdated = (datetime.datetime.now() - datetime.timedelta(days=int(args.get_from))).isoformat('T') + 'z'
					# for getting the last 14 days worth of events
				print(i['summary'] + ' last updated: ' + str(lastUpdated))
				try:
					eventList += pull_calendar_events(calendar_service, i['id'], lastUpdated)
				except Exception, e:
					print("lastUpdated error, pulling all events")
					eventList += pull_calendar_events(calendar_service, i['id'], None)

		push_events_to_database(db_file, eventList)


		"""TIMING"""
		finish = datetime.datetime.now()
		delta = finish - start
		print("update() complete in %d sec" % (delta.seconds))
		""""""""""""
		# no error!
		return 0
	except Exception, e:
		print(e)
		"""TIMING"""
		finish = datetime.datetime.now()
		delta = finish - start
		print("update() complete in %d sec" % (delta.seconds))
		""""""""""""


		# error :(
		return 1

if __name__ == '__main__':
	update()

