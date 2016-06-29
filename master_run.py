from master import *
import datetime

"""TIMING"""
start = datetime.datetime.now()
""""""""""""

credentials_dir = "/Users/alee/Documents/secret"
client_secret_file = 'client_secret.json'
credentials_file = 'credentials.json'
db_file = 'intellibroad.db'



# create_tables()

admin, calendar = create_api_service(credentials_dir, client_secret_file, credentials_file)

calendarList = update_calendars(admin, calendar)

eventList = []

# for i in calendarList:
# 	eventList += pull_calendar_events(calendar, i)
lastUpdated = get_last_update(db_file)
eventList = pull_calendar_events(calendar, calendarList[0], lastUpdated)

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