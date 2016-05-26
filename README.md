# traceMySteps - back-end

A visualization that allows users to understand and analyze their spatio-temporal information, with focus on personal semantics.

Python development of the back-end for traceMySteps. Connects with AngularJS front-end also provided in another repository.

### TODO List:

1) Test data insertion on the DB.

2) Test querying.

3) Complete `app.py`.

4) Batch load of multiple GPX files into DB.

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

7) Run the app:
`python app.py`

8) Stop server:
`pg_ctl stop`

I strongly advise the use of the pgAdmin3 tool as a visual aid and complement to the shell commands.
This Readme will be updated, whenever possible, with the progress on the development and with new instructions.


## Dependencies

Available on `setup.py`
