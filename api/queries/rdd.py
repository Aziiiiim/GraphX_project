import requests
import os 
import logging

from utils.kafka_utils import ConsumerManager, kafka_config
from utils.conf_spark import sc

logger = logging.getLogger(__name__)


def get_metro_disruptions():
    info_trafic_metro_url = "https://prim.iledefrance-mobilites.fr/marketplace/v2/navitia/line_reports/physical_modes/physical_mode:Metro/line_reports?"
    
    query_params = {
        # "count": 100,
        # "start_page": 0
    }

    response = requests.get(info_trafic_metro_url,
                            headers={"apiKey": f"{os.getenv('PRIM_API_KEY')}"},
                            params=query_params
    )
    response.raise_for_status()  # Check if the request was successful

    data = response.json()
    logger.info("[RDD] Data retrieved from API")
    return data


def get_disruptions_per_line(data):
    # Get RDDs
    line_reports = sc.parallelize(data["line_reports"])
    disruptions = sc.parallelize(data["disruptions"])

    # RDD Key -> Value for disruptions
    disruptions_by_id = disruptions.map(lambda d: (d["id"], d)) # id and not disruption_id
    # print("Disruptions by id : ", disruptions_by_id.take(5))
    logger.info("[RDD] Disruptions RDD created with id as key")

    # RDD Key -> Value for line reports (same key as disruption links)
    def extract_disruption(report):
        results = []

        for obj in report.get("pt_objects", []):
            details = obj.get(obj["embedded_type"], {})

            for link in details.get("links", []):
                if link["type"] == "disruption":
                    results.append((link["id"], report["line"]["id"]))

        return results

    links = line_reports.flatMap(extract_disruption)
    links = links.distinct() # remove duplicates (stop + line can be linked to the same disruption, for instance)
    # print("Links : ", links.take(5))
    logger.info("[RDD] Links RDD created")

    # Join disruptions with line reports (thanks to the same key : disruption id)
    joined = links.join(disruptions_by_id)
    # print("Joined : ", joined.take(5))
    logger.info("[RDD] Joined RDD created")


    def get_title_message(msg_list):
        for msg in msg_list:
            if msg["channel"]["name"] == "titre":
                return msg["text"]
        return msg_list[0]["text"] if msg_list else "No message available"

    # Extract disruption message
    traffic = joined.map(
        lambda x: (
            x[1][0],  # line id
            get_title_message(x[1][1]["messages"]) # We could retrieve a more detailed message by getting the one for channel "moteur" or other
        )
    )
    traffic_by_line = traffic.groupByKey().mapValues(list)
    # print("Traffic by line : ", traffic_by_line.take(5))
    logger.info("[RDD] Traffic by line RDD created")

    return traffic_by_line.collect()

    ### NEXT STEPS ###
    # Make sure 'application_periods' attribute matches the current time
    # Get impacted stations information
