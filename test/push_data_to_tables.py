import sqlite3
from sqlite3 import Error
from create_tables import create_connection
import json



def push_events_to_database(items):
	"""Takes calendar data and writes each event's details to database. \n
	\t items: List of events returned by API call 
	\t c: the sqlite3 database cursor
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
			print("executeString: " + executeString)

			c.execute(executeString, args)

		return write_row


	# need some help with abstraction!!!!

	write_events = make_row_writer(c, 'events', 5)
	write_employees = make_row_writer(c, 'employees', 2)
	write_invitations = make_row_writer(c, 'invitations', 3)

	for item in items:
		if item['status'] != 'cancelled':
			print(json.dumps(item, indent=4, separators=(':',',')))
			try:
				write_events(item['id'], item['summary'], item['start']['dateTime'], item['location'], item['updated'])

				for attendee in item['attendees']:
					try:		
						write_employees(attendee['email'], attendee['displayName'])
						write_invitations(item['id'], attendee['email'], attendee['responseStatus'])
					except KeyError, e:
						print('Key ' + str(e) + ' not found. Not writing person and invitation entry.')
						print(item)


			except KeyError, e:
				print("Key " + str(e) + ' not found. Not writing event entry.')


	conn.commit()
	conn.close()

	print("Committed changes and closed database connection")







