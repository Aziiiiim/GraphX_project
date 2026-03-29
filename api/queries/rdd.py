import logging

from utils.kafka_utils import ConsumerManager, kafka_config
from utils.conf_spark import sc

logger = logging.getLogger(__name__)


def get_metro_disruptions():
    consumer_manager = ConsumerManager(kafka_config)

    consumer_manager.add_kafka_consumer("line_reports_metro")
    consumer_manager.add_kafka_consumer("disruptions_metro")

    line_reports_records = consumer_manager.consumers["line_reports_metro"].poll(
        timeout_ms=5000,
        max_records=1000
    )
    disruptions_records = consumer_manager.consumers["disruptions_metro"].poll(
        timeout_ms=5000,
        max_records=1000
    )

    line_reports_raw = [
        msg.value
        for partition in line_reports_records.values()
        for msg in partition
    ]

    disruptions_raw = [
        msg.value
        for partition in disruptions_records.values()
        for msg in partition
    ]

    line_reports = []
    for item in line_reports_raw:
        if isinstance(item, list):
            line_reports.extend(item)
        else:
            line_reports.append(item)

    disruptions = []
    for item in disruptions_raw:
        if isinstance(item, list):
            disruptions.extend(item)
        else:
            disruptions.append(item)

    logger.info(f"[RDD] {len(line_reports)} line reports read from Kafka")
    logger.info(f"[RDD] {len(disruptions)} disruptions read from Kafka")

    return {
        "line_reports": line_reports,
        "disruptions": disruptions
    }


def get_disruptions_per_line(data):
    line_reports_data = data.get("line_reports", [])
    disruptions_data = data.get("disruptions", [])

    if not line_reports_data or not disruptions_data:
        return {"error": "No data from Kafka"}

    line_reports = sc.parallelize(line_reports_data)
    disruptions = sc.parallelize(disruptions_data)

    disruptions_by_id = disruptions.map(lambda d: (d["id"], d))
    logger.info("[RDD] Disruptions RDD created with id as key")

    def extract_disruption(report):
        results = []

        for obj in report.get("pt_objects", []):
            embedded_type = obj.get("embedded_type")
            details = obj.get(embedded_type, {}) if embedded_type else {}

            for link in details.get("links", []):
                if link.get("type") == "disruption":
                    results.append((link["id"], report["line"]["id"]))

        return results

    links = line_reports.flatMap(extract_disruption).distinct()
    logger.info("[RDD] Links RDD created")

    joined = links.join(disruptions_by_id)
    logger.info("[RDD] Joined RDD created")

    def get_title_message(msg_list):
        for msg in msg_list:
            channel = msg.get("channel", {})
            if channel.get("name") == "titre":
                return msg.get("text", "No message available")
        return msg_list[0].get("text", "No message available") if msg_list else "No message available"

    traffic = joined.map(
        lambda x: (
            x[1][0],
            get_title_message(x[1][1].get("messages", []))
        )
    )

    result = traffic.groupByKey().mapValues(list).collect()

    return [
        {
            "line_id": line_id,
            "messages": messages
        }
        for line_id, messages in result
    ]