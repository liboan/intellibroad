import os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory
from flask_bootstrap import Bootstrap

import datetime
import master_run
from querys import *

app = Flask(__name__)

app.config.from_object(__name__)

app.config.update(dict(
	DATABASE=os.path.join(app.root_path, 'intellibroad.db')
	))

Bootstrap(app) # Load Bootstrap for templates!

@app.route('/')
def home():
	return render_template('home_bs.html')

@app.route('/js/<path:path>')
def send_js(path):
	return send_from_directory("js", path)

""" Retrieve row given an ID """

@app.route('/item')
def get_item_by_id():
	"""
	We are expecting a query string with arguments itemType (person or meeting)
	and id (the id)
	"""
	print(request.query_string)

	item_type = request.args.get('itemType')
	item_id = request.args.get('id')

	if item_type == 'person':
		response = {
			'info': curate_person_row(query_person_by_id(app.config['DATABASE'], item_id)), # own information
			'nearbyMeetings': curate_meeting_list(query_person_meetings(app.config['DATABASE'], item_id)), # meetings in +/- 30 days
			'similarPeople': curate_person_list(query_person_similar_people(app.config['DATABASE'], item_id)) # similar people
		}
		return render_template('people_bs.html', response=response)
	elif item_type == 'meeting':
		response = {
			'info': curate_meeting_row(query_meeting_by_id(app.config['DATABASE'], item_id)), # own info
			'meetingAttendees': curate_person_list(query_meeting_people(app.config['DATABASE'], item_id)), # attendees
			'similarMeetings': curate_meeting_list(query_meeting_similar_meetings(app.config['DATABASE'], item_id)) # similar meetings
		}
		return render_template('meeting_bs.html', response=response)
	else:
		return redirect(url_for('home'))

""" Retrieve list of matching rows given a search term """
@app.route('/form')
def parse_request():
	# form passes in GET requests- use request.args
	if request.args['searchOption'] == 'person':
		return search_person(request.args['search'])
	elif request.args['searchOption'] == 'meeting':
		return search_meeting(request.args['search'])
	elif request.args['searchOption'] == 'topic':
		return search_topic(request.args['search'])
	else:
		return render_template('home_bs.html')

def search_person(term):
	"""responds to a search request for a person, renders home page with search results included\n
	term: string
	"""
	list_from_db = query_person_search(app.config['DATABASE'], term)

	response = {
		'personList': curate_person_list(list_from_db),
	}

	return render_template('home_bs.html', response=response)

def search_meeting(term):
	"""responds to a search request for a meeting, renders home page with search results included\n
	term: string
	"""
	list_from_db = query_meeting_search(app.config['DATABASE'], term)

	response = {
		'meetingList': curate_meeting_list(list_from_db),
	}
	return render_template('home_bs.html', response=response)

def search_topic(term, lower_bound_days=30, upper_bound_days=30):
	"""responds to a search request for a topic and returns a table of search results\n
	request: passed from Flask
	lower_bound_days and upper_bound_days: number of days to search in past and future (all > 0!), an integer
	"""
	
	employees_from_db = query_topic_employees(app.config['DATABASE'], term)
	meetings_from_db = query_topic_meetings(app.config['DATABASE'], term, lower_bound_days, upper_bound_days)

	return render_template('topic_bs.html', response = {
		'personList': curate_person_list(employees_from_db), 
		'meetingList': curate_meeting_list(meetings_from_db)})

""""""

"""Query Data Curation"""

def curate_person_row(row):
	"""Converts row object from query functions to something that looks better on the frontend.

	- Converts row to dicts
	"""
	new_row = dict(row)
	return new_row

def curate_meeting_row(row):
	"""Converts row object from query functions to something that looks better on the frontend.
	
	- Converts row to dicts
	- Converts RFC 3339 timestamps to more readable date format
	"""
	new_row = dict(row)

	# convert to a readable timestring
	date_string = new_row['start_time']
	date_format = '%Y-%m-%dT%H:%M'
	date_string = datetime.datetime.strptime(date_string[:-9], date_format)

	new_row['start_time'] = date_string

	return new_row

def curate_person_list(data):
	new_data = []
	for row in data:
		new_data.append(curate_person_row(row))
	return new_data

def curate_meeting_list(data):
	new_data = []
	for row in data:
		new_data.append(curate_meeting_row(row))
	return new_data

@app.route('/update')
def update():
	return str(master_run.update(app.config['DATABASE']))

"""TESTING BOOTSTRAP"""

@app.route('/bootstrap')
def home_bs():
	return render_template('layout_bs.html')

if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)



