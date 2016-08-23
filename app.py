from os import getenv
import collections
import argparse
import itertools
import os
import json
import numpy as np
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


def loadLatLon(gpx, vector):
  for track in gpx.tracks:
    for segment in track.segments:
      for point in segment.points:
        print 'Point at ({0},{1}) -> {2} {3}'.format(point.latitude, point.longitude, point.elevation, point.time)
        # Hexbin library works with (lon, lat) instead of (lat, lon)
        vector.append([point.longitude, point.latitude, point.time.strftime("%Y-%m-%d")])


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
          cur.execute("SELECT ST_X(centroid::geometry), ST_Y(centroid::geometry), visit_frequency, label FROM locations WHERE centroid NOTNULL")
        except:
          print("Error executing select")
        response = cur.fetchall()
        array = []
        for datum in response:
          for _ in range(datum[2]):
            # Hexbin library works with (lon, lat) instead of (lat, lon)
            array.append([datum[1], datum[0], datum[3], datum[2]])
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
        'date' : datetime.datetime.strptime(day.date, '%Y_%m_%d').strftime('%Y-%m-%d'),
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
          cur.execute("select json_build_object('label', location_label, 'value', time_spent, 'date', ddmmyy) from stays")
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
          cur.execute("select json_build_object('from', start_location, 'to', end_location, 'start', start_of_trip) from trips")
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
          cur.execute("SELECT start_location, start_of_trip FROM trips UNION SELECT end_location FROM trips")
        except:
          print("Error executing select")
        nodes = [{'id': i[0]} for i in cur.fetchall()]
        return nodes


def checkEqual(iterator):
  try:
     iterator = iter(iterator)
     first = next(iterator)
     return all(first == rest for rest in iterator)
  except StopIteration:
     return True


def moreTimeSpent (day_number, hour_number):
  result = []
  monday_list = []
  tuesday_list = []
  wednesday_list = []
  thursday_list = []
  friday_list = []
  saturday_list = []
  sunday_list = []
  day_list = []

  for day in life.days:
    date_object = datetime.datetime.strptime(day.date, '%Y_%m_%d')
    day_list.append(date_object)

  for date in day_list:
    # For the datetime.weekday() function, Monday is 0 and Sunday is 6
    # We need to convert to a date object in order to use the weekday()
    # Then it is converted again to the LIFE format
    if (date.weekday() == 0):
      monday_list.append(date.strftime('%Y_%m_%d'))
    elif (date.weekday() == 1):
      tuesday_list.append(date.strftime('%Y_%m_%d'))
    elif (date.weekday() == 2):
      wednesday_list.append(date.strftime('%Y_%m_%d'))
    elif (date.weekday() == 3):
      thursday_list.append(date.strftime('%Y_%m_%d'))
    elif (date.weekday() == 4):
      friday_list.append(date.strftime('%Y_%m_%d'))
    elif (date.weekday() == 5):
      saturday_list.append(date.strftime('%Y_%m_%d'))
    elif (date.weekday() == 6):
      sunday_list.append(date.strftime('%Y_%m_%d'))

  # Convert the hour number to military format
  if (hour_number == 1):
    hour_number = "0000"
  elif (hour_number == 2):
    hour_number = "0100"
  elif (hour_number == 3):
    hour_number = "0200"
  elif (hour_number == 4):
    hour_number = "0300"
  elif (hour_number == 5):
    hour_number = "0400"
  elif (hour_number == 6):
    hour_number = "0500"
  elif (hour_number == 7):
    hour_number = "0600"
  elif (hour_number == 8):
    hour_number = "0700"
  elif (hour_number == 9):
    hour_number = "0800"
  elif (hour_number == 10):
    hour_number = "0900"
  elif (hour_number == 11):
    hour_number = "1000"
  elif (hour_number == 12):
    hour_number = "1100"
  elif (hour_number == 13):
    hour_number = "1200"
  elif (hour_number == 14):
    hour_number = "1300"
  elif (hour_number == 15):
    hour_number = "1400"
  elif (hour_number == 16):
    hour_number = "1500"
  elif (hour_number == 17):
    hour_number = "1600"
  elif (hour_number == 18):
    hour_number = "1700"
  elif (hour_number == 19):
    hour_number = "1800"
  elif (hour_number == 20):
    hour_number = "1900"
  elif (hour_number == 21):
    hour_number = "2000"
  elif (hour_number == 22):
    hour_number = "2100"
  elif (hour_number == 23):
    hour_number = "2200"
  elif (hour_number == 24):
    hour_number = "2300"

  # Operate the day and hour numbers
  if (day_number == 1):
    tmp = []
    for day in sunday_list:
      response = life.where_when(day, hour_number)
      tmp.append(response)
      # We ll calculate in the half hour, as a rough estimate
      plus_half = '%04d' % (int(hour_number) + 30)
      half_hour_later = life.where_when(day, plus_half)
      tmp.append(half_hour_later)
      print tmp
      if (half_hour_later == None):
        pass
      else:  
        result.append(half_hour_later)
        if (len(result) == 1):
          time_spent = life.when_at(result[0])[0].length()
          result.append(time_spent)
          return result
        else:
          pass

  elif (day_number == 2):
    comparing_day = []
    tmp = []
    for day in monday_list:
      # We ll calculate in the half hour, as a rough estimate
      plus_half = '%04d' % (int(hour_number) + 30)
      half_hour_later = life.where_when(day, plus_half)
      comparing_day.append(day)
      if (half_hour_later == None):
        pass
      else:
        tmp.append(half_hour_later)
    print tmp
    if (checkEqual(tmp) == True):
      pass
    elif (len(tmp) == 1):
      temp_date_vector = []
      for x in xrange(0,len(life.when_at(tmp[0]))):
        temp_date_vector.append(life.when_at(tmp[0])[x].day)
      #if(set(tmp) == set(life.when_at(tmp[0])[x].day)):
      true_date = np.intersect1d(temp_date_vector, comparing_day)
      time_spent = life.when_at(tmp[0])[x].length()
      tmp.append(time_spent)
      return tmp
    elif (not tmp):
      result.append("No place")
      result.append(0)
      return result

  elif (day_number == 3):
    tuesday_list
  elif (day_number == 4):
    wednesday_list
  elif (day_number == 5):
    thursday_list
  elif (day_number == 6):
    friday_list
  elif (day_number == 7):
    saturday_list





class Stays_Graph(Resource):
  def get(self):
        result = []
        time_label = moreTimeSpent(2, 1)
        #print time_label
        for day in range(1, 8):
          for hour in range (1, 25):
            #time_label = moreTimeSpent(day, hour)
            d = {
              'day': day,
              'hour': hour
              # 'time_spent': time_label[1],
              # 'label': time_label[0]
            }
            result.append(d)
        return result
        

# cur.execute("SELECT start_date::timestamp AT TIME ZONE 'UTC' from trips")

# maybe construct answer only using LIFE?
# day and hour will be combination of all days of week and hours of the day
# which is a matrix ([0][0], [0][1],...) -> for days inside of for hours or vice-versa

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