from __future__ import division
from create_tables import create_connection
import sqlite3
import argparse
import datetime


parser = argparse.ArgumentParser(description='Test script for database query methods')
# parser.add_argument('queryString', metavar='search', type=str, help='Search term')
parser.add_argument('-db')

args = parser.parse_args()


"""TOPIC QUERYING"""

def query_topic_employees(db_file, term):
	"""Searches database and returns list of sqlite3.Row objects for each employee who showed up in a relevant event, ordered from most to least frequent. \n 
	db_file: path to database, a string
	term: search term, a string"""

	term = str(term) # convert search term, just to be sure
	print(term)
	term = '%' + term + '%' # so that SQLite will return all strings containing term

	conn = create_connection(db_file)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()

	"""SQLite commands for associated people"""

	queryString = """
	SELECT name, employees.employee_id, count(*) FROM invitations 
	INNER JOIN employees ON employees.employee_id = invitations.employee_id 
	WHERE invitations.event_id IN (SELECT event_id FROM events WHERE name LIKE ?)
	GROUP BY invitations.employee_id ORDER BY -count(*);
	"""


	c.execute(queryString, (term,))
	return c.fetchall()

def query_topic_meetings(db_file, term, lower_bound_days=30, upper_bound_days=30):
	"""Searches database and returns list of sqlite3.Row objects for meetings whose title contains term.
	To be helpful, we return relevant meetings occurring within a given time range of search.\n
	db_file: path to database, a string
	term: search term, a string
	lower_bound_days and upper_bound_days: number of days to search in past and future (all > 0!), an integer
	"""

	term = str(term) # convert search term, just to be sure
	print(term)
	term = '%' + term + '%' # so that SQLite will return all strings containing term

	conn = create_connection(db_file)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()

	pastBound = (datetime.datetime.now() + datetime.timedelta(days=-abs(lower_bound_days))).isoformat('T')
	futureBound = (datetime.datetime.now() + datetime.timedelta(days=abs(upper_bound_days))).isoformat('T')
	# time bounds, we will plug these into SQLite and search between them

	queryString = """
	SELECT * FROM events WHERE name LIKE ? AND start_time > ? AND start_time < ?"""

	c.execute(queryString, (term, pastBound, futureBound))
	return c.fetchall()


"""PERSON QUERYING"""

def query_person_meetings(db_file, employee_id, lower_bound_days=30, upper_bound_days=30):
	"""Searches database and returns list of sqlite3.Row objects for meetings person was invited to.
	We only return meetings occurring within a given time range of search. \n
	db_file: path to database, a string
	employee_id: person's id (email address), a string
	lower_bound_days and upper_bound_days: number of days to search in past and future (all > 0!), an integer
	"""
	if '@' not in employee_id:
		print("NOT AN EMAIL ADDRESS")
		return None

	conn = create_connection(db_file)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()

	pastBound = (datetime.datetime.now() + datetime.timedelta(days=-abs(lower_bound_days))).isoformat('T')
	futureBound = (datetime.datetime.now() + datetime.timedelta(days=abs(upper_bound_days))).isoformat('T')
	# time bounds, we will plug these into SQLite and search between them
	queryString = """
	SELECT * FROM events WHERE event_id IN 
	(SELECT event_id FROM invitations WHERE employee_id LIKE ?) AND
	start_time > ? AND start_time < ? ORDER BY event_id;
	"""

	c.execute(queryString, (employee_id,pastBound,futureBound))
	return c.fetchall()

def query_person_similar_people(db_file, employee_id):
	"""Searches database and returns list of sqlite3.Row objects for people the searched person share
	meetings with, in order of most shared meetings. \n
	db_file: path to database, a string
	employee_id: person's id (email address), a string"""
	if '@' not in employee_id:
		print("NOT AN EMAIL ADDRESS")
		return None

	conn = create_connection(db_file)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()

	queryString = """
	SELECT name, employees.employee_id, count(*) FROM invitations 
	INNER JOIN employees ON employees.employee_id = invitations.employee_id 
	WHERE invitations.event_id IN (SELECT event_id FROM invitations WHERE employee_id LIKE ?)
	GROUP BY invitations.employee_id ORDER BY -count(*);"""

	c.execute(queryString, (employee_id,))
	return c.fetchall()

"""MEETING QUERYING"""

def query_meeting_people(db_file, event_id):
	"""Returns a list of sqlite3.Row objects for people attending a given event.\n
	db_file: path to database, a string
	event_id: ID of event, a string
	"""
	conn = create_connection(db_file)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()

	queryString = """SELECT name, employees.employee_id FROM 
	invitations INNER JOIN employees ON employees.employee_id = invitations.employee_id WHERE event_id = ?"""

	c.execute(queryString, (event_id,))

	return c.fetchall()

def query_meeting_similar_meetings(db_file, event_id, max_results=10, no_duplicate_names=True):
	"""Returns a list of sqlite3.Row objects for events, ordered from most to least similar to
	the searched event by Jaccard index of their attendees.\n
	db_file: path to database, a string
	event_id: ID of event, a string
	max_results: however many results are wanted, an integer
	no_duplicate_names: whether or not to filter out events that share the same name as the original"""
	conn = create_connection(db_file)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()

	# Get name of searched event for curating
	c.execute('SELECT name FROM events WHERE event_id = ?', (event_id,))
	name = c.fetchone()[0] # first member in row tuple

	scores = calculate_meeting_similarity(db_file, event_id) # returns sorted list of tuples (id, score)

	rowList = []

	i = 0
	while i < max_results:
		# look through slice of list (if max_results is too big, will do entire list)
		c.execute('SELECT * FROM events WHERE event_id = ?', (scores[i][0],)) # event ID is first member of tuple
		row = c.fetchone()
		if no_duplicate_names and row['name'] == name:
			# if we ARE curating, and the names match...
			max_results += 1 # we increment max_results bc we now need one more!
		else:
			# otherwise, append!
			rowList.append(row)
		i += 1 

	return rowList


def calculate_meeting_similarity(db_file, event_id):
	"""Searches database for events that are potentially similar to the specified event. 
	Similarity is obtained by finding the Jaccard index of the two events' attendee lists.
	Returns list of tuples (event id, Jaccard index) sorted from highest score to lowest.

	DOES NOT CALCULATE FOR ALL EVENTS. Uses hashes to determine when there is no overlap between
	event's attendees (score of 0). Only returns list of event ids for which there is a chance
	of overlap.

	db_file: path to database, a string
	event_id: ID of event, a string.
	"""
	conn = create_connection(db_file)
	conn.row_factory = sqlite3.Row
	c = conn.cursor()

	# Get IDs events we're going to be comparing (check hashes)
	eventQueryString = """SELECT event_id FROM event_hashes WHERE 
	((SELECT hash FROM event_hashes WHERE event_id = ?) & hash) <> 0 
	AND event_id <> ?"""
	# this obtains all lists whose hashes share bits with the queried event's; that is, they
	# have at least a chance of containing matching attendees

	c.execute(eventQueryString, (event_id,event_id)) # pass it twice, second param is to make sure
													# we don't get the same event
	event_list = [i[0] for i in c.fetchall()] # rows will have tuples, first element is event_id

	####################################

	# Get the attendees of the event that was passed in

	c.execute('SELECT employee_id FROM invitations WHERE event_id = ?', (event_id,))
	attendees = [i[0] for i in c.fetchall()]

	####################################

	# Loop through each other event, get the attendees of each, and score

	scores = [] # dict to return, key is event id, value is score.

	for x in event_list:
		c.execute('SELECT employee_id FROM invitations WHERE event_id = ?', (x,))
		x_attendees = [i[0] for i in c.fetchall()] # rows will have tuples, first element is employee_id
		x_score = jaccard(attendees, x_attendees)
		scores.append((x, x_score))

	scores.sort(key=lambda x: x[1],reverse=True) # sort list by scores (second member of the tuple)

	conn.close()

	return scores
	

def jaccard(list1, list2):
	"""Calculates Jaccard index of two lists. Returns integer between 0 and 1
	list1, list2: lists of strings or integers
	"""
	set1 = set(list1)
	set2 = set(list2)
	return len(set.intersection(set1, set2))/len(set.union(set1,set2))

""""""""""""""""""




