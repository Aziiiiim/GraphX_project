import threading
import time
from collections import defaultdict
from datetime import datetime, timedelta

from utils.kafka_utils import ConsumerManager, kafka_config


class LiveStreamingService:
    def __init__(self):
        self.lock = threading.Lock()
        self.started = False
        self.thread = None
        self.stop_event = threading.Event()

        # Buffer glissant des événements récents
        self.recent_events = []
        self.window_minutes = 30
        self.aggregation_minutes = 5

        self.cache = {
            "status": "stopped",
            "severity": [],
            "last_timestamp": None
        }

    def _safe_parse_event_time(self, value: str):
        if not value:
            return None

        for fmt in ("%Y%m%dT%H%M%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(value, fmt)
            except Exception:
                pass

        return None

    def _round_window(self, dt: datetime, window_minutes: int):
        minute = (dt.minute // window_minutes) * window_minutes
        return dt.replace(minute=minute, second=0, microsecond=0)

    def _extract_events(self, disruptions_raw):
        events = []

        for item in disruptions_raw:
            entries = item if isinstance(item, list) else [item]

            for entry in entries:
                event_time = datetime.now()
                if not event_time:
                    continue

                severity = (entry.get("severity") or {}).get("name")
                if not severity:
                    continue

                event_id = entry.get("id")
                if not event_id:
                    continue

                events.append({
                    "event_id": event_id,
                    "event_time": event_time,
                    "severity_name": severity
                })

        return events

    def _merge_recent_events(self, new_events):
        now = datetime.now()
        cutoff = now - timedelta(minutes=self.window_minutes)

        # On ajoute les nouveaux au buffer existant
        merged = self.recent_events + new_events

        # Déduplication par event_id :
        # si un même event revient, on garde la version la plus récente
        unique_events = {}
        for event in merged:
            event_id = event["event_id"]
            existing = unique_events.get(event_id)

            if existing is None or event["event_time"] >= existing["event_time"]:
                unique_events[event_id] = event

        # On filtre pour ne garder que les événements récents
        self.recent_events = [
            event for event in unique_events.values()
            if event["event_time"] >= cutoff
        ]

    def _compute_severity_from_buffer(self):
        if not self.recent_events:
            return {
                "severity": [],
                "last_timestamp": None
            }

        severity_counts = defaultdict(int)

        for event in self.recent_events:
            win_start = self._round_window(event["event_time"], self.aggregation_minutes)
            win_end = win_start + timedelta(minutes=self.aggregation_minutes)

            key = (
                win_start.isoformat(),
                win_end.isoformat(),
                event["severity_name"]
            )
            severity_counts[key] += 1

        severity_result = [
            {
                "window_start": k[0],
                "window_end": k[1],
                "severity_name": k[2],
                "nb_events": v
            }
            for k, v in severity_counts.items()
        ]

        severity_result.sort(
            key=lambda x: (x["window_end"], x["nb_events"]),
            reverse=True
        )

        last_timestamp = max(
            event["event_time"] for event in self.recent_events
        ).isoformat()

        return {
            "severity": severity_result,
            "last_timestamp": last_timestamp
        }

    def _loop(self):
        consumer_manager = ConsumerManager(kafka_config)
        consumer_manager.add_kafka_consumer("disruptions")

        with self.lock:
            self.cache["status"] = "running"

        while not self.stop_event.is_set():
            try:
                records = consumer_manager.consumers["disruptions"].poll(
                    timeout_ms=3000,
                    max_records=1000
                )

                raw_data = [
                    msg.value
                    for partition in records.values()
                    for msg in partition
                ]

                new_events = self._extract_events(raw_data)

                with self.lock:
                    self._merge_recent_events(new_events)
                    computed = self._compute_severity_from_buffer()

                    self.cache["severity"] = computed["severity"]
                    self.cache["last_timestamp"] = computed["last_timestamp"]
                    self.cache["status"] = "running"

            except Exception as e:
                with self.lock:
                    self.cache["status"] = f"error: {str(e)}"

            time.sleep(2)

    def start(self):
        if self.started:
            return

        self.stop_event.clear()
        self.thread = threading.Thread(target=self._loop, daemon=True)
        self.thread.start()
        self.started = True

        with self.lock:
            self.cache["status"] = "starting"

    def stop(self):
        if not self.started:
            return

        self.stop_event.set()
        if self.thread:
            self.thread.join(timeout=5)

        self.started = False

        with self.lock:
            self.cache["status"] = "stopped"

    def get_latest_results(self):
        if not self.started:
            self.start()

        with self.lock:
            return dict(self.cache)


streaming_service = LiveStreamingService()


def get_live_incidents():
    return streaming_service.get_latest_results()