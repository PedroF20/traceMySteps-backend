from os import getenv
import collections
import argparse
import itertools
import os
import json
import subprocess
import ppygis
import psycopg2
import psycopg2.extras
import gpxpy
import gpxpy.gpx
import datetime
import life_source
from life_source import Life
from life_source import Day
from flask import Response, Flask, request, abort, render_template
from flask import jsonify
from flask_restful import Resource, Api
from json import dumps

app = Flask(__name__)
api = Api(app)


############################################################################
################      LIFE and tracks manipulation      ####################
############################################################################

life = Life("MyTracks.life")

# We use the RDP-simplified tracks to show information on the 
# hexbins and the tracks themselves more quickly.
# It lowers the quantity of data sent through the endpoints,
# allowing more speed and responsiveness.
# We will lose little to no quality of the visual information.
files_directory = 'MyTracks/ProcessedTracks/'


# def loadLatLon(gpx, vector):
#   for track in gpx.tracks:
#     for segment in track.segments:
#       for point in segment.points:
#         print 'Point at ({0},{1}) -> {2} {3}'.format(point.latitude, point.longitude, point.elevation, point.time)
#         # Hexbin library works with (lon, lat) instead of (lat, lon)
#         vector.append([point.longitude, point.latitude])


# result = []
# files =[]
# for f in os.listdir(files_directory):
#     files.append(f)
# files.sort()

# for f in files:
#   if f.endswith(".gpx"):
#     filename = os.path.join(files_directory, f)
#     print filename
#     gpx_file = open(filename, 'r')
#     tracks = gpxpy.parse(gpx_file)
#     loadLatLon(tracks, result)


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


@app.route("/")
def Home():
	return render_template("index.html")


class Hexbin_Places_Data(Resource):
  def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        try:
          #Centroids cannot be null, we need them to show the coordinates
          cur.execute("SELECT ST_X(centroid::geometry), ST_Y(centroid::geometry), visit_frequency FROM locations WHERE centroid NOTNULL")
        except:
          print("Error executing select")
        response = cur.fetchall()
        array = []
        for datum in response:
          for _ in range(datum[2]):
            # Hexbin library works with (lon, lat) instead of (lat, lon)
            array.append([datum[1], datum[0]])
        return array


class Hexbin_Tracks_Data(Resource):
  def get(self):
        return result


class Calendar_Data(Resource):
  def get(self):
    result = []
    # Times are converted to seconds
    for day in life.days:
      details_array = []
      for span in day.spans:
        if type(span.place) is str:
          real_date = datetime.datetime.strptime("%s %s" % (day.date, life_source.minutes_to_military(span.start)), "%Y_%m_%d %H%M")
          details = {
            'name': span.place,
            'date': str(real_date),
            'value': (span.length() * 60),
          }
          details_array.append(details)
      data = {
        'date': datetime.datetime.strptime(day.date, '%Y_%m_%d').strftime('%Y-%m-%d'),
        'total': (day.somewhere() * 60),
        'details': details_array
      }
      result.append(data)
    return result


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
      files =[]
      for f in os.listdir(files_directory):
        if f.endswith(".gpx"):
          files.append(f)
      files.sort()
      return files


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
        except:
          print("Error executing select")
        TimeData = list (i[0] for i in cur.fetchall())
        return TimeData


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
          cur.execute("select json_build_object('source', start_location, 'target', end_location, 'frequency', 1) from trips")
        except:
          print("Error executing select")
        ArcList = list (i[0] for i in cur.fetchall())
        counter = collections.Counter()
        for datum in ArcList:
          if (datum['source'] == datum['target']):
            # Ignore trips with the same source and target
            pass
          else:
            counter[(datum['source'], datum['target'])] += datum['frequency']
        processed_ArcList = [{
            'source': k[0],
            'target': k[1],
            'frequency': v,
        } for k, v in counter.items()]
        return processed_ArcList


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
        result = []
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        try:
          cur.execute("SELECT EXTRACT (DOW FROM start_date) from stays")
        except:
          print("Error executing select")
        day_of_week = cur.fetchall()
        try:
          cur.execute("SELECT location_label from stays")
        except:
          print("Error executing select")
        locations = cur.fetchall()
        for day in range(1, 8):
          for hour in range (1, 25):
            print day
            print hour
        for dow_datum, location_datum in itertools.izip_longest(day_of_week, locations):
          d = {
            'day' : dow_datum,
            'label': location_datum
          }
          result.append(d)
        return result

        

# cur.execute("SELECT start_date::timestamp AT TIME ZONE 'UTC' from trips")

# maybe construct answer only using LIFE?
# day and hour will be combination of all days of week and hours of the day
# which is a matrix ([0][0], [0][1],...) -> for days inside of for hours or vice-versa

# {  
#   day:2, // day 1: sunday, day 2: monday, etc.
#   hour:1, // // 1-1 ate 1-1.59 -> corresponde ao intervalo 0 ate 0.59
#   // "primeira hora do dia" - fazer esta associacao no backend
#   // ex: if 00<=hour<=00.59 -> hour=1
#   time_spent:57,// in minutes - maximo de 60 pois o bloco e de 1 hr
#   label: "home" // sitio onde aconteceu a stay ou a stay "mais importante"
#   // no caso de haver varias stays para um bloco, mostrar a maior
# }

# For each row of the stays table, construct a response
# as shown below and return the JSON with the set of
# responses. If a stay uses more than a one-hour block,
# multiply the same response for each of the hours,
# adjusting the time_spent on each one

class Slider_Min_Date(Resource):
  def get(self):
        result = []
        for day in life.days:
          d = day.date
          result.append(d)
        return result[0]


class Slider_Max_Date(Resource):
  def get(self):
        result = []
        for day in life.days:
          d = day.date
          result.append(d)
        return result[-1]


############################################################################
######################### Endpoints and run ################################
############################################################################

api.add_resource(Hexbin_Places_Data, '/hexbinPlaces')
api.add_resource(Hexbin_Tracks_Data, '/hexbinTracks')
api.add_resource(Calendar_Data, '/calendar')
api.add_resource(Area_Gradient_Data, '/areagradient')
api.add_resource(GPS_Tracks, '/gpstracklist')
api.add_resource(BarChart_Frequency_Data, '/barchartFrequency')
api.add_resource(BarChart_TimeSpent_Data, '/barchartTime')
api.add_resource(Chord_Data, '/chord')
api.add_resource(Arc_Edges_Data, '/arcedges')
api.add_resource(Arc_Nodes_Data, '/arcnodes')
api.add_resource(Stays_Graph, '/staysgraph') # LAST
api.add_resource(Slider_Min_Date, '/slidermin')
api.add_resource(Slider_Max_Date, '/slidermax')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')