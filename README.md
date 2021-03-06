# traceMySteps - back-end

A visualization that allows users to understand and analyze their spatio-temporal information, with focus on personal semantics.

Python development of the back-end for traceMySteps. Connects with AngularJS front-end also provided in another repository.

### TODO List:

<s>1) Test data insertion on the DB.</s>

<s>2) Test querying.</s>

<s>3) Parsing and batch load of multiple GPX files into DB.</s>

<s>4) Complete `app.py` with the front-end required resources/routes and queries, having in mind the JSON formats needed on the frontend.</s>


### Minor bugs:

### Steps to run:

1) Install Postgresql and Postgis:
```
brew install postgres
brew install postgis
```
2) If that’s a fresh installation, initialize database cluster:
`initdb /usr/local/var/postgres`

3) Configure PATH environment variable (if needed):
```
export PATH=$PATH:'/usr/local/var/postgres'
export PGDATA='/usr/local/var/postgres'
```
4) Start Postgresql server:
`pg_ctl start`

5) Check status:
`pg_ctl status`

6) Enter postgres default database at start, to run schema to create our database:
```
psql postgres
\i PATH_TO/schema.sql
```

7) To quit the created tracemysteps DB:
`\q`
  
8) To re-access the tracemysteps DB:
`psql tracemysteps`

While on the project folder:

9) Make sure to have a `MyTracks.life` file, containing the semantic information about your trips and stays.

10) Also make sure to have a `MyTracks`folder, containing all your `.gpx`files.

11) Run the Ramer–Douglas–Peucker algorithm in order to simplify dataset:
`python process_gpx.py`

12) Run the `parse_load.py`file in order to populate the database:
`python parse_load.py`

13) Run the app (click "Allow" when prompted):
`python app.py`

14) Stop server:
`pg_ctl stop`

I strongly advise the use of the pgAdmin3 tool as a visual aid and complement to the shell commands.
This Readme will be updated, whenever possible, with the progress on the development and with new instructions.


## Dependencies

Available on `setup.py`
