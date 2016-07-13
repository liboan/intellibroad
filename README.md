# IntelliBroad
Database application for employee expertise/responsibility at the Broad Institute

## Setup
- This program runs on Python 2.
- Clone the repository into your directory of choice
- Install dependencies with `pip install -r requirements.txt`
- To download data from Google Calendar:
  - Setting up everything on Google's end:
    - Register an application at [console.developers.google.com](console.developers.google.com)
    - Activate the Google Calendar and Google Apps Admin APIs
    - Go to Credentials and create an OAuth client ID
    - Download the Client ID JSON file (aka client secret)
  - Place the client secret file in your directory of choice
  - Run the downloading program with: 
  ```
  python master_run.py --cred_dir <path to client secret directory> --secret <name of client secret file>
  ```
  - This will create a new database file in the project directory called `intellibroad.db`. Alternatively, you can specify a path to an existing database file with `-db <path>`
- To run the Flask server & frontend:
  `python intellibroad_server.py -db <path to database>`
