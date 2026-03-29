import pandas as pd
from utils.kafka_utils import ConsumerManager, kafka_config

def most_stop_incident():
    consumer_manager = ConsumerManager(kafka_config)
    consumer_manager.add_kafka_consumer("line_reports")
    records = consumer_manager.consumers["line_reports"].poll(timeout_ms=5000, max_records=1000)

    raw_data = [
        msg.value
        for partition in records.values()
        for msg in partition
    ]

    rows = []

    for i in raw_data:
        entries = i if isinstance(i, list) else [i]

        for entry in entries:
            line = entry.get("line", {})
            line_name = line.get("name")
            line_links = line.get("links", [])
            line_incidents = len([
                l for l in line_links if l.get("type") == "disruption"
            ])

            pt_objects = entry.get("pt_objects", [])

            if not pt_objects:
                rows.append({
                    "line_name": line_name,
                    "stop_name": None,
                    "line_incidents": line_incidents,
                    "stop_incidents": 0
                })
            else:
                for pt in pt_objects:
                    stop_area = pt.get("stop_area", {})
                    stop_name = stop_area.get("name")
                    stop_links = stop_area.get("links", [])
                    stop_incidents = len([
                        l for l in stop_links if l.get("type") == "disruption"
                    ])

                    rows.append({
                        "line_name": line_name,
                        "stop_name": stop_name,
                        "line_incidents": line_incidents,
                        "stop_incidents": stop_incidents
                    })

    if not rows:
        return {"error": "No data from Kafka"}

    df = pd.DataFrame(rows)
    df_grouped = df.groupby("stop_name", as_index=False)["stop_incidents"].sum()
    df_sorted = df_grouped.sort_values(by="stop_incidents", ascending=False)

    return df_sorted.head(10).to_dict(orient="records")