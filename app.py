from os import getenv
import argparse
import json
import subprocess
import ppygis
import psycopg2
import psycopg2.extras
from flask import Response, Flask, request, abort, render_template
from flask import jsonify
from datetime import datetime
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps

app = Flask(__name__)
api = Api(app)


def connectDB():
    connectionString = 'dbname=tracemysteps user=PedroFrancisco host=localhost'
    #print connectionString
    try:
      return psycopg2.connect(connectionString)
    except:
      print("Can't connect to database")


@app.after_request
def after_request(response):
  response.headers.add('Access-Control-Allow-Origin', '*')
  response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
  response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE')
  return response


# toJSON example

# return {
#         'points': map(lambda point: point.toJSON(), self.points),
#         'transportationModes': self.transportation_modes,
#         'locationFrom': self.location_from.toJSON() if self.location_from != None else None,
#         'locationTo': self.location_to.toJSON() if self.location_to != None else None
#         }


@app.route("/")
def Home():
	return render_template("index.html")


class Hexbin_Places_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        return


class Hexbin_Tracks_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        return


class Calendar_Data(Resource):
  def get(self):
    return


class Area_Gradient_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        return


class GPS_Tracks(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        return


class BarChart_Frequency_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        return


class BarChart_TimeSpent_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        return


# MyList = list (dict(zip (tuple (query.keys()) ,i)) for i in query.cursor)
#         return jsonify ({'date_price':MyList})

class Chord_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        try:
          cur.execute("select json_build_object('from', start_location, 'to', end_location) from trips")
        except:
          print("Error executing select")
        ChordList = list (i[0] for i in cur.fetchall())
        return ChordList


class Arc_Edges_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        try:
          cur.execute("select json_build_object('source', start_location, 'target', end_location, 'frequency', TRIP_FREQUENCY) from trips")
        except:
          print("Error executing select")
        ArcList = list (i[0] for i in cur.fetchall())
        return ArcList


class Arc_Nodes_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        try:
          cur.execute("SELECT start_location FROM trips UNION SELECT end_location FROM trips")
        except:
          print("Error executing select")
        nodes = [{'id': i[0]} for i in cur.fetchall()]
        #NodeList = list (i[0] for i in cur.fetchall())
        return nodes


class Stays_Graph(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        return


api.add_resource(Hexbin_Places_Data, '/hexbinPlaces') # LAST
api.add_resource(Hexbin_Tracks_Data, '/hexbinTracks') # LAST
api.add_resource(Calendar_Data, '/calendar') # LAST
api.add_resource(Area_Gradient_Data, '/areagradient') # NEXT
api.add_resource(GPS_Tracks, '/gpstracks') # LAST
api.add_resource(BarChart_Frequency_Data, '/barchartFrequency') # NEXT
api.add_resource(BarChart_TimeSpent_Data, '/barchartTime') # NEXT
api.add_resource(Chord_Data, '/chord') # DONE
api.add_resource(Arc_Edges_Data, '/arcedges') # NEXT
api.add_resource(Arc_Nodes_Data, '/arcnodes') # DONE
api.add_resource(Stays_Graph, '/staysgraph') # LAST


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')