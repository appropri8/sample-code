from dataclasses import dataclass

@dataclass
class ConfidenceMonitor:
    min_conf: float = 0.65

    def should_fallback(self, conf: float) -> bool:
        return conf < self.min_conf
