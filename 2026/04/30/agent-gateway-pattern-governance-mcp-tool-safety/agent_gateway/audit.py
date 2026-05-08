import json
from datetime import datetime, timezone
from pathlib import Path


class AuditStore:
    def __init__(self, path=None):
        self.records = []
        self.path = Path(path) if path else None

    def log(self, **record):
        record.setdefault("timestamp", datetime.now(timezone.utc).isoformat())
        self.records.append(record)

        if self.path:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with self.path.open("a", encoding="utf-8") as file:
                file.write(json.dumps(record, sort_keys=True) + "\n")

        return record

