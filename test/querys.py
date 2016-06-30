from create_tables import create_connection
import sqlite3
import argparse
import datetime

parser = argparse.ArgumentParser(description='Test script for database query methods')
parser.add_argument('queryString', metavar='search', type=str, help='Search term')
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


""""""""""""""

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

""""""""""""""""""








