from os import getenv
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


@app.route("/")
def Home():
	return render_template("index.html")


class Example(Resource):
    def get(self):
        #Connect to databse
        conn = connectDB()
        cur = conn.cursor()
        #Perform query and return JSON data
        try:
          cur.execute("select trip_id from trips")
        except:
          print("Error executing select")
        MyList = list (i[0] for i in cur.fetchall())
        return jsonify ({'trip_id':MyList})


class Hexbin_Data(Resource):
  def get(self):
    return


class Calendar_Data(Resource):
  def get(self):
    return


class Area_Gradient_Data(Resource):
  def get(self):
    return


class GPS_Tracks(Resource):
  def get(self):
    return


class BarChart_Frequency_Data(Resource):
  def get(self):
    return


class BarChart_TimeSpent_Data(Resource):
  def get(self):
    return


class Chord_Data(Resource):
  def get(self):
    return


class Arc_Edges_Data(Resource):
  def get(self):
    return


class Arc_Nodes_Data(Resource):
  def get(self):
    return


class Ranged_Bar(Resource):
  def get(self):
    return


api.add_resource(Example, '/example')
api.add_resource(Hexbin_Data, '/hexbin')
api.add_resource(Calendar_Data, '/calendar')
api.add_resource(Area_Gradient_Data, '/areagradient')
api.add_resource(GPS_Tracks, '/gpstracks')
api.add_resource(BarChart_Frequency_Data, '/barchartFrequency')
api.add_resource(BarChart_TimeSpent_Data, '/barchartTime')
api.add_resource(Chord_Data, '/chord')
api.add_resource(Arc_Edges_Data, '/arcedges')
api.add_resource(Arc_Nodes_Data, '/arcnodes')
api.add_resource(Ranged_Bar, '/rangedbar')


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')