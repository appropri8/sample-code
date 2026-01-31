"""Checkpoint storage implementation."""
import json
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, List
from .events import Checkpoint, StepEvent


class CheckpointStore:
    """Store checkpoints in SQLite + JSON files."""
    
    def __init__(self, db_path: str = "checkpoints/checkpoints.db", 
                 blob_dir: str = "checkpoints/blobs"):
        self.db_path = db_path
        self.blob_dir = Path(blob_dir)
        self.blob_dir.mkdir(parents=True, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        """Initialize database schema."""
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS checkpoints (
                run_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                step_number INTEGER NOT NULL,
                timestamp TEXT NOT NULL,
                agent_version TEXT NOT NULL,
                run_type TEXT DEFAULT 'normal',
                PRIMARY KEY (run_id, step_id)
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS events (
                run_id TEXT NOT NULL,
                step_id TEXT NOT NULL,
                step_number INTEGER NOT NULL,
                tool_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                duration_ms REAL NOT NULL,
                PRIMARY KEY (run_id, step_id)
            )
        """)
        conn.commit()
        conn.close()
    
    def save_checkpoint(self, checkpoint: Checkpoint):
        """Save checkpoint to DB + blob store."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO checkpoints 
            (run_id, step_id, step_number, timestamp, agent_version)
            VALUES (?, ?, ?, ?, ?)
        """, (
            checkpoint.run_id,
            checkpoint.step_id,
            checkpoint.step_number,
            checkpoint.timestamp.isoformat(),
            checkpoint.agent_version
        ))
        conn.commit()
        conn.close()
        
        # Save payloads to blob store
        blob_path = self.blob_dir / checkpoint.run_id / f"{checkpoint.step_id}.json"
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        with open(blob_path, 'w') as f:
            json.dump({
                "messages": checkpoint.messages,
                "tool_calls": checkpoint.tool_calls,
                "model_config": checkpoint.model_config,
                "state": checkpoint.state
            }, f, indent=2)
    
    def load_checkpoint(self, run_id: str, step_id: str) -> Optional[Checkpoint]:
        """Load checkpoint from DB + blob store."""
        conn = sqlite3.connect(self.db_path)
        row = conn.execute("""
            SELECT step_number, timestamp, agent_version
            FROM checkpoints
            WHERE run_id = ? AND step_id = ?
        """, (run_id, step_id)).fetchone()
        conn.close()
        
        if not row:
            return None
        
        # Load payloads from blob store
        blob_path = self.blob_dir / run_id / f"{step_id}.json"
        if not blob_path.exists():
            return None
        
        with open(blob_path, 'r') as f:
            blob_data = json.load(f)
        
        return Checkpoint(
            run_id=run_id,
            step_id=step_id,
            step_number=row[0],
            timestamp=datetime.fromisoformat(row[1]),
            messages=blob_data["messages"],
            tool_calls=blob_data["tool_calls"],
            model_config=blob_data["model_config"],
            state=blob_data["state"],
            agent_version=row[2]
        )
    
    def save_event(self, event: StepEvent):
        """Save event to database."""
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
            INSERT OR REPLACE INTO events
            (run_id, step_id, step_number, tool_name, timestamp, duration_ms)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            event.run_id,
            event.step_id,
            event.step_number,
            event.tool_name,
            event.timestamp.isoformat(),
            event.duration_ms
        ))
        conn.commit()
        conn.close()
        
        # Save full event to blob
        blob_path = self.blob_dir / event.run_id / "events" / f"{event.step_id}.json"
        blob_path.parent.mkdir(parents=True, exist_ok=True)
        with open(blob_path, 'w') as f:
            json.dump(event.to_dict(), f, indent=2)
    
    def load_events(self, run_id: str) -> List[StepEvent]:
        """Load all events for a run."""
        events_dir = self.blob_dir / run_id / "events"
        if not events_dir.exists():
            return []
        
        events = []
        for event_file in sorted(events_dir.glob("*.json")):
            with open(event_file, 'r') as f:
                event_data = json.load(f)
                events.append(StepEvent.from_dict(event_data))
        
        return sorted(events, key=lambda e: e.step_number)
    
    def cleanup_old_checkpoints(self, retention_days: int = 30):
        """Delete checkpoints older than retention period."""
        cutoff = datetime.now() - timedelta(days=retention_days)
        conn = sqlite3.connect(self.db_path)
        
        # Get old run_ids
        rows = conn.execute("""
            SELECT DISTINCT run_id FROM checkpoints
            WHERE timestamp < ?
        """, (cutoff.isoformat(),)).fetchall()
        
        # Delete from DB
        conn.execute("""
            DELETE FROM checkpoints WHERE timestamp < ?
        """, (cutoff.isoformat(),))
        conn.execute("""
            DELETE FROM events WHERE timestamp < ?
        """, (cutoff.isoformat(),))
        conn.commit()
        conn.close()
        
        # Delete blob files
        for (run_id,) in rows:
            run_dir = self.blob_dir / run_id
            if run_dir.exists():
                import shutil
                shutil.rmtree(run_dir)
