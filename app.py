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
    host = getenv('DB_HOST')
    name = getenv('DB_NAME')
    user = getenv('DB_USER')
    password = getenv('DB_PASS')
    try:
        if host != None and name != None and user != None and password != None:
            return psycopg2.connect("host=%s dbname=%s user=%s password=%s" % (host, name, user, password))
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')