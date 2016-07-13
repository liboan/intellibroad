from __future__ import division

import os
from flask import Flask, request, session, g, redirect, url_for, abort, render_template, flash, send_from_directory
from flask_bootstrap import Bootstrap


import datetime
import master_run
from querys import *
from people_graph import *

import argparse

parser = argparse.ArgumentParser(description='IntelliBroad flask server. Need to specify location of database.')

parser.add_argument('-db', help='Path to database file.', default='intellibroad.db')

args = parser.parse_args()

print("DATABASE LOCATION: " + args.db)

app = Flask(__name__)

app.config.from_object(__name__)

app.config.update(dict(
	DATABASE=args.db
	))

Bootstrap(app) # Load Bootstrap for templates!

def time_cutoff(days=90):
	"""returns timestamp of one year ago (default) to serve as a cutoff for 'noactivity' employees"""
	return (datetime.datetime.now() + datetime.timedelta(days=-days)).isoformat('T')

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
			'similarPeople': curate_person_list(query_person_similar_people(app.config['DATABASE'], item_id)), # similar people
			'time': time_cutoff()
		}
		return render_template('people_bs.html', response=response)
	elif item_type == 'meeting':
		response = {
			'info': curate_meeting_row(query_meeting_by_id(app.config['DATABASE'], item_id)), # own info
			'meetingAttendees': curate_person_list(query_meeting_people(app.config['DATABASE'], item_id)), # attendees
			'similarMeetings': curate_meeting_list(query_meeting_similar_meetings(app.config['DATABASE'], item_id)), # similar meetings
			'time': time_cutoff()
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
		'time': time_cutoff()
	}

	return render_template('home_bs.html', response=response)

def search_meeting(term):
	"""responds to a search request for a meeting, renders home page with search results included\n
	term: string
	"""
	list_from_db = query_meeting_search(app.config['DATABASE'], term)

	response = {
		'meetingList': curate_meeting_list(list_from_db),
		'time': time_cutoff()
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
		'meetingList': curate_meeting_list(meetings_from_db),
		'time': time_cutoff()
	})

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

""" GRAPH for similar people """

def generate_employee_graph(employee_row):
	"""Given an SQLite3.Row object for an employee, returns graph showing connections to similar employees"""
	employee_graph = make_graph()

	add_node(employee_graph, employee_row['name']) # Add employee's row as a node.

	first_order_connections = query_person_similar_people(app.config['DATABASE'], employee_row['employee_id'])
	first_order_connections = first_order_connections[0:15]
	# Add all 20 1st-order connections to graph.
	for connection in first_order_connections:
		add_node(employee_graph, connection['name'])
		add_edge(employee_graph, employee_row['name'], connection['name'])

	# Now that they're all in, search the connections of each for any existing ones and link 'em up.
	# NO NEW NODES, just extra connections.
	for connection in first_order_connections:
		second_order_connections = query_person_similar_people(app.config['DATABASE'], connection['employee_id'],max_results=10)
		for connection2 in second_order_connections:
			if connection2['name'] in get_nodes(employee_graph):
				# If any of the 2nd order connections are also 1st order connections to the original,
				# we can draw an edge between them.
				add_edge(employee_graph, connection['name'], connection2['name'])

	return employee_graph

@app.route('/graph')
def display_graph():
	row = query_person_by_id(app.config['DATABASE'], request.args['employee_id'])
	graph = generate_employee_graph(row)
	return json.dumps(graph)

""""""

""" WORDCLOUD for common keywords """

def generate_employee_keywords(employee_row):
	"""Given an employee row, returns a list of tuples [word, frequency]"""
	keywords = query_person_keywords(app.config['DATABASE'], employee_row['employee_id'])

	total = sum([word[1] for word in keywords]) # add up
	freqs = [word[1]/total for word in keywords] # get frequencies

	keywordFreqs = zip([word[0] for word in keywords], freqs) # zip each word with its frequency
	return keywordFreqs

@app.route('/wordcloud')
def display_wordcloud():
	row = query_person_by_id(app.config['DATABASE'], request.args['employee_id'])
	keywords = generate_employee_keywords(row)
	return json.dumps(keywords)

""""""

@app.route('/about')
def about():
	return render_template('about_bs.html')

@app.route('/update')
def update():
	return str(master_run.update(app.config['DATABASE']))


if __name__ == '__main__':
	app.run(host='0.0.0.0', debug=True)



