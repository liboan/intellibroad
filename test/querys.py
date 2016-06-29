from create_tables import create_connection
import sqlite3
import argparse

parser = argparse.ArgumentParser(description='Test script for database query methods')
parser.add_argument('queryString', metavar='search', type=str, help='Search term')
parser.add_argument('-db', default="../intellibroad.db")

args = parser.parse_args()


"""QUERYING"""

def query_topic_employees(db_file, term):
       """Searches database and returns list of sqlite3.Row objects for each employee who showed up in a relevant event, ordered from most to least frequent. 
       \n
       term: search term, a string"""

       term = str(term) # convert search term, just to be sure
       print(term)
       term = '%' + term + '%'


       conn = create_connection(db_file)
       conn.row_factory = sqlite3.Row
       c = conn.cursor()

       """SQLite commands for associated people"""
       
       queryString = """
       SELECT name, employees.employee_id, count(*) FROM invitations INNER JOIN employees ON 
       employees.employee_id = invitations.employee_id WHERE invitations.event_id IN (SELECT 
       event_id FROM events WHERE name LIKE ?) GROUP BY invitations.employee_id
       ORDER BY -count(*);
       """

       c.execute(queryString, (term,))
       return c.fetchall()

""""""""""""""



"""TEST PORTION"""

results = query_topic_employees(args.db, args.queryString)

for i in results:
       print i


"""""""""""""" 




