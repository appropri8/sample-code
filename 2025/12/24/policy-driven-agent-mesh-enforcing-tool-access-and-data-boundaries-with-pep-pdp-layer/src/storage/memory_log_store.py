"""In-memory log store for audit logs."""
from typing import Dict, Any, List


class MemoryLogStore:
    """In-memory log store for audit logs."""
    
    def __init__(self):
        """Initialize memory log store."""
        self.logs = []
    
    def write(self, log_entry: Dict[str, Any]):
        """Write a log entry.
        
        Args:
            log_entry: Log entry dictionary
        """
        self.logs.append(log_entry)
    
    def get_all(self) -> List[Dict[str, Any]]:
        """Get all log entries.
        
        Returns:
            List of all log entries
        """
        return self.logs.copy()
    
    def get_by_trace_id(self, trace_id: str) -> List[Dict[str, Any]]:
        """Get log entries by trace ID.
        
        Args:
            trace_id: Trace ID
            
        Returns:
            List of log entries for the trace
        """
        return [
            log for log in self.logs
            if log.get("trace_id") == trace_id
        ]
    
    def clear(self):
        """Clear all log entries."""
        self.logs.clear()

