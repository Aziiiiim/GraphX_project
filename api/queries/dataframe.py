import pandas as pd
from utils.kafka_utils import ConsumerManager, kafka_config
from utils.conf_spark import sql_context

# Don't initialize at import time - move to functions

def most_stop_incident():
    # Initialize on demand
    consumer_manager = ConsumerManager(kafka_config)
    consumer_manager.add_kafka_consumer("line_reports")
    
    # Poller directement les messages depuis Kafka
    records = consumer_manager.consumers["line_reports"].poll(timeout_ms=5000, max_records=1000)
    
    # Extraire uniquement les valeurs (le JSON des messages)
    raw_data = [msg.value for partition in records.values() for msg in partition]
    
    # Supposons que ton JSON soit déjà chargé dans raw_data (liste de dicts)
    rows = []
    for i in raw_data:
        for entry in i:
            line = entry.get("line", {})
            line_name = line.get("name")
            line_links = line.get("links", [])
            line_incidents = len([l for l in line_links if l.get("type") == "disruption"])

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
                    stop_incidents = len([l for l in stop_links if l.get("type") == "disruption"])
                    rows.append({
                        "line_name": line_name,
                        "stop_name": stop_name,
                        "line_incidents": line_incidents,
                        "stop_incidents": stop_incidents
                    })

    # Créer le DataFrame pandas
    df = pd.DataFrame(rows)
    
    # Classement par stop_name en pandas
    df_grouped = df.groupby('stop_name', as_index=False)['stop_incidents'].sum()
    df_sorted = df_grouped.sort_values(by='stop_incidents', ascending=False)
    return df_sorted.head(10).to_dict()


def most_line_incident():
    # Initialize on demand
    consumer_manager = ConsumerManager(kafka_config)
    consumer_manager.add_kafka_consumer("line_reports")
    
    records = consumer_manager.consumers["line_reports"].poll(timeout_ms=5000, max_records=1000)
    raw_data = [msg.value for partition in records.values() for msg in partition]
    
    if not raw_data:
        return {"error": "No data from Kafka"}
    
    rows = []
    for i in raw_data:
        for entry in i:
            line = entry.get("line", {})
            line_name = line.get("name")
            line_links = line.get("links", [])
            line_incidents = len([l for l in line_links if l.get("type") == "disruption"])

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
                    stop_incidents = len([l for l in stop_links if l.get("type") == "disruption"])
                    rows.append({
                        "line_name": line_name,
                        "stop_name": stop_name,
                        "line_incidents": line_incidents,
                        "stop_incidents": stop_incidents
                    })

    # Créer le DataFrame pandas
    df = pd.DataFrame(rows)
    
    # Use pandas groupby instead of Spark SQL to avoid Py4J compatibility issues
    result_df = df.groupby('line_name', as_index=False)['stop_incidents'].sum()
    result_df.columns = ['line_name', 'total_incidents']
    result_df = result_df.sort_values(by='total_incidents', ascending=False)
    
    return result_df.to_dict()