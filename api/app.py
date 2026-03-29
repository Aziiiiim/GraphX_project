from flask import Flask, jsonify
from queries.rdd import *
from queries.dataframe import *
from queries.graphx import *
from queries.streaming import *
from utils.conf import client_minio, consumer_manager
from flask import request

app = Flask(__name__)

@app.route("/incidents/query", methods=["POST"])
def incidents_query():
    data = request.get_json()  # Get JSON instead of form data
    query_type = data.get('type') if data else None
    
    match query_type:
        case "rdd":
            d = get_metro_disruptions()
            return get_disruptions_per_line(d)
        case "dataframe":
            return most_stop_incident()
        case _:
            return {"error": "Unknown type"}, 400

@app.route("/incidents/live", methods=["GET"])
def incidents_live():
    return jsonify(get_live_incidents())

@app.route("/graph/query", methods=["POST"])
def graph_query():
    data = request.get_json()
    # Process graph query data
    return jsonify({"result": "Graph query result"})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)