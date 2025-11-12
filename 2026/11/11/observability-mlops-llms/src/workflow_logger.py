"""Workflow and branch decision logging"""

import json
import sqlite3
from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class BranchDecisionLog:
    timestamp: str
    request_id: str
    from_node: str
    to_node: str
    condition: str
    condition_result: bool
    context: Dict[str, Any]


@dataclass
class ToolCallLog:
    timestamp: str
    request_id: str
    tool_name: str
    inputs: Dict[str, Any]
    output: Any
    latency_ms: float
    status: str
    error: Optional[str] = None


class WorkflowLogger:
    """Logger for workflow branches and tool calls"""
    
    def __init__(self, db_path: str = "observability.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database for workflow logging"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS branch_decisions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                request_id TEXT,
                from_node TEXT,
                to_node TEXT,
                condition TEXT,
                condition_result INTEGER,
                context TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tool_calls (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT,
                request_id TEXT,
                tool_name TEXT,
                inputs TEXT,
                output TEXT,
                latency_ms REAL,
                status TEXT,
                error TEXT
            )
        """)
        
        conn.commit()
        conn.close()
    
    def log_branch_decision(
        self,
        request_id: str,
        from_node: str,
        to_node: str,
        condition: str,
        condition_result: bool,
        context: Dict[str, Any]
    ):
        """Log a branching decision"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO branch_decisions (
                timestamp, request_id, from_node, to_node,
                condition, condition_result, context
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            request_id,
            from_node,
            to_node,
            condition,
            1 if condition_result else 0,
            json.dumps(context)
        ))
        conn.commit()
        conn.close()
    
    def log_tool_call(
        self,
        request_id: str,
        tool_name: str,
        inputs: Dict[str, Any],
        output: Any,
        latency_ms: float,
        status: str = "success",
        error: Optional[str] = None
    ):
        """Log a tool call"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tool_calls (
                timestamp, request_id, tool_name, inputs, output,
                latency_ms, status, error
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            datetime.utcnow().isoformat(),
            request_id,
            tool_name,
            json.dumps(inputs),
            json.dumps(output) if output else None,
            latency_ms,
            status,
            error
        ))
        conn.commit()
        conn.close()

