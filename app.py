from os import getenv
import argparse
import os
import json
import subprocess
import ppygis
import psycopg2
import psycopg2.extras
import gpxpy
import gpxpy.gpx
from life_source import Life
from life_source import Day
from flask import Response, Flask, request, abort, render_template
from flask import jsonify
from datetime import datetime
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps

app = Flask(__name__)
api = Api(app)


############################################################################
################  LIFE and tracks direct manipulation  #####################
############################################################################

life = Life("MyTracks.life")
files_directory = 'MyTracks/'


def loadLatLon(gpx, vector):
  for track in gpx.tracks:
    for segment in track.segments:
      for point in segment.points:
        print 'Point at ({0},{1}) -> {2} {3}'.format(point.latitude, point.longitude, point.elevation, point.time)
        vector.append([point.longitude, point.latitude])


result = []
files =[]
for f in os.listdir(files_directory):
    files.append(f)
files.sort()

for f in files:
  if f.endswith(".gpx"):
    filename = os.path.join(files_directory, f)
    print filename
    gpx_file = open(filename, 'r')
    tracks = gpxpy.parse(gpx_file)
    loadLatLon(tracks, result)


############################################################################
################ Database connection and operations ########################
############################################################################

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
        return result


class Calendar_Data(Resource):
  def get(self):
    return


class Area_Gradient_Data(Resource):
  def get(self):
    result = []
    for day in life.days:
      d = {
        'date' : day.date,
        'price': day.moving()
      }
      result.append(d)
    return result


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
        try:
          cur.execute("select json_build_object('label', label, 'value', visit_frequency) from locations")
        except:
          print("Error executing select")
        FrequencyData = list (i[0] for i in cur.fetchall())
        return FrequencyData


class BarChart_TimeSpent_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        try:
          cur.execute("select json_build_object('label', location_label, 'value', time_spent) from stays")
          # function total_at in the life_source file is important for time_spent
        except:
          print("Error executing select")
        TimeData = list (i[0] for i in cur.fetchall())
        return TimeData


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
        return nodes


class Stays_Graph(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        return


############################################################################
######################### Endpoints and run ################################
############################################################################

api.add_resource(Hexbin_Places_Data, '/hexbinPlaces') # LAST  se no json aparecer a mesma lat/lon repetida (frequencia) 
                                                      #       para as localizacoes das stays, o hexbin escurece mais
api.add_resource(Hexbin_Tracks_Data, '/hexbinTracks')
api.add_resource(Calendar_Data, '/calendar') # LAST
api.add_resource(Area_Gradient_Data, '/areagradient')
api.add_resource(GPS_Tracks, '/gpstracks') # LAST
api.add_resource(BarChart_Frequency_Data, '/barchartFrequency')
api.add_resource(BarChart_TimeSpent_Data, '/barchartTime')
api.add_resource(Chord_Data, '/chord')
api.add_resource(Arc_Edges_Data, '/arcedges') # NEXT
api.add_resource(Arc_Nodes_Data, '/arcnodes')
api.add_resource(Stays_Graph, '/staysgraph') # LAST


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')