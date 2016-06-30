import datetime
import argparse
from oauth2client import tools

parser = argparse.ArgumentParser(parents=[tools.argparser], description='Runs the methods in master.py. \nWill soon do one whole update cycle.')
# we need to add the oauth2 argparser in order for it to play game with our own
parser.add_argument('-db', help='database file path', default="intellibroad.db")
parser.add_argument('--cred_dir', help='credentials directory', default='/Users/alee/Documents/secret')
parser.add_argument('--secret', help='secrets file', default='client_secret.json')
parser.add_argument('--credentials', help='credentials file', default='credentials.json')

args = parser.parse_args()

print("####ARGS####")
print(args)

from master import *

"""TIMING"""
start = datetime.datetime.now()
""""""""""""

credentials_dir = args.cred_dir # "/Users/alee/Documents/secret"
client_secret_file = args.secret # 'client_secret.json'
credentials_file = args.credentials # 'credentials.json'
db_file = args.db # 'intellibroad.db'



# create_tables()

admin, calendar = create_api_service(credentials_dir, client_secret_file, credentials_file)

calendarList = update_calendars(admin, calendar)

eventList = []



# eventList = pull_calendar_events(calendar, calendarList[0], lastUpdated)
for i in calendarList:
	lastUpdated = get_last_update(db_file, i['name'])
	print(i['name'] + ' last updated: ' + lastUpdated)
	eventList += pull_calendar_events(calendar, i['id'], lastUpdated)

print(len(eventList))

push_events_to_database(db_file, eventList)

# results = query_topic_employees('achilles')

# for i in results:
# 	print i

"""TIMING"""
finish = datetime.datetime.now()
delta = finish - start
print("TOTAL EXECUTION TIME: %d sec" % (delta.seconds))
""""""""""""