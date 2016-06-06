from os import getenv
import ppygis
import psycopg2
import psycopg2.extras
from datetime import datetime

def connectDB():
    connectionString = 'dbname=tracemysteps user=PedroFrancisco host=localhost'
    #print connectionString
    try:
      return psycopg2.connect(connectionString)
    except:
      print("Can't connect to database")