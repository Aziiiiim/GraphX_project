from flask import Flask
from queries.rdd import *
from queries.dataframe import *
from queries.graphx import *
from queries.streaming import *
from utils.conf import sql_context, client_minio

app = Flask(__name__)

@app.route("/")
def hello_world():
    return "<p>Hello, World!</p>"

@app.route("/dataframe")
def dataframe():
    most_stop_incident()
    most_line_incident()
    return "dataframe : ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)