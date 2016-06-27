import sqlite3
from sqlite3 import Error




def create_connection(db_file):
	"""Creates and returns a database connection to a SQLite database\n
	db_file: path to database"""
	try:
		conn = sqlite3.connect(db_file)
		print("Created connection with " + db_file)
		return conn
	except Error as e:
		print(e)
	return None 

def main():
	db_file = "intellibroad.db"

	conn = create_connection(db_file)

	c = conn.cursor()

	# Gonna start by hardcoding in the three tables we want.

	c.execute("CREATE TABLE IF NOT EXISTS events ( event_id text PRIMARY KEY, name text, start_time text, location text, last_update text )")
	c.execute("CREATE TABLE IF NOT EXISTS employees ( employee_id text PRIMARY KEY, name text )")
	c.execute("CREATE TABLE IF NOT EXISTS invitations ( event_id text, employee_id text, response text)")

	print("Tables written successfully")

	conn.commit()
	conn.close()

if __name__ == '__main__':
	main()