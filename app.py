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
          cur.execute("select trip_id from trips_transportation_modes")
        except:
          print("Error executing select")
        MyList = list (i[0] for i in cur.fetchall())
        return jsonify ({'trip_id':MyList})


api.add_resource(Example, '/example')

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')