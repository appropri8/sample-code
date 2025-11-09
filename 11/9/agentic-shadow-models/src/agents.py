from dataclasses import dataclass
from typing import Dict, Any
import re

@dataclass
class Executor:
    """Simulates a backend tool-using agent with templated outputs."""
    def handle(self, query: str) -> str:
        # Very simple rule-based executor for demo purposes
        m = re.search(r"#(\d+)", query)
        order_id = m.group(1) if m else "N/A"
        query_l = query.lower()
        if "status" in query_l:
            return f"order #{order_id} is in transit"
        if "cancel" in query_l:
            return f"order #{order_id} has been cancelled"
        if "change address" in query_l:
            return f"address updated for #{order_id}"
        if "estimated delivery" in query_l or "eta" in query_l:
            return f"order #{order_id} arrives tomorrow"
        if "refund" in query_l:
            return f"refund initiated for #{order_id}"
        return f"acknowledged request for #{order_id}"

@dataclass
class Planner:
    shadow: Any  # ShadowModel
    executor: Executor

    def ask(self, query: str, min_conf: float = 0.65) -> Dict[str, Any]:
        pred, conf = self.shadow.predict(query)
        if conf >= min_conf:
            return {"source":"shadow", "answer": pred, "confidence": conf}
        # Fallback to live executor and update shadow
        live = self.executor.handle(query)
        self.shadow.partial_fit([query], [live])
        return {"source":"live", "answer": live, "confidence": conf}
