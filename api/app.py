from flask import Flask
from queries.rdd import *
from queries.dataframe import *
from queries.graphx import *
from queries.streaming import *
from utils.conf import client_minio, consumer_manager

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/dataframe")
def dataframe():
    most_stop_incident()
    most_line_incident()
    return "dataframe : ok"

@app.route("/graph")
def graph_request():
    return request()

@app.route("/rdd")
def get_rdd_data():
    d = get_metro_disruptions() # USE KAFKA INSTEAD
    return get_disruptions_per_line(d)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)