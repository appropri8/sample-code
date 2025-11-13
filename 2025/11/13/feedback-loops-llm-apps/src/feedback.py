"""Feedback collection and storage"""

import json
import psycopg2
from datetime import datetime
from typing import Dict, Any, Optional
from psycopg2.extras import RealDictCursor


def get_db_connection():
    """Get database connection."""
    import os
    from dotenv import load_dotenv
    load_dotenv()
    
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        database=os.getenv("DB_NAME", "feedback_loops"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "")
    )


def insert_feedback(
    conversation_id: str,
    turn_id: int,
    request_id: str,
    input_text: str,
    output_text: str,
    prompt_version: str,
    model: str,
    feedback_type: Optional[str] = None,
    feedback_value: Optional[Dict[str, Any]] = None,
    user_id_hash: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Insert feedback into database."""
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            INSERT INTO feedback (
                conversation_id, turn_id, request_id,
                input, output, prompt_version, model,
                feedback_type, feedback_value, timestamp,
                user_id_hash, metadata
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            conversation_id, turn_id, request_id,
            input_text, output_text, prompt_version, model,
            feedback_type,
            json.dumps(feedback_value) if feedback_value else None,
            datetime.utcnow(),
            user_id_hash,
            json.dumps(metadata) if metadata else None
        ))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def collect_explicit_feedback(
    request_id: str,
    rating: Optional[int] = None,
    comment: Optional[str] = None,
    thumbs_up: Optional[bool] = None
):
    """Collect explicit feedback from users."""
    feedback_value = {}
    
    if rating is not None:
        feedback_value["rating"] = rating
    if comment:
        feedback_value["comment"] = comment
    if thumbs_up is not None:
        feedback_value["thumbs_up"] = thumbs_up
    
    # Get existing feedback record
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("SELECT * FROM feedback WHERE request_id = %s", (request_id,))
        existing = cur.fetchone()
        
        if existing:
            # Update existing record
            cur.execute("""
                UPDATE feedback
                SET feedback_type = 'explicit',
                    feedback_value = %s
                WHERE request_id = %s
            """, (json.dumps(feedback_value), request_id))
        else:
            # Create new record (minimal data)
            cur.execute("""
                INSERT INTO feedback (
                    conversation_id, turn_id, request_id,
                    input, output, prompt_version, model,
                    feedback_type, feedback_value, timestamp
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                f"conv_{request_id}", 1, request_id,
                "", "", "unknown", "unknown",
                "explicit", json.dumps(feedback_value), datetime.utcnow()
            ))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def collect_implicit_feedback(
    request_id: str,
    edit_ratio: Optional[float] = None,
    time_to_completion: Optional[float] = None,
    abandoned: Optional[bool] = None
):
    """Collect implicit feedback from user actions."""
    feedback_value = {}
    
    if edit_ratio is not None:
        feedback_value["edit_ratio"] = edit_ratio
    if time_to_completion is not None:
        feedback_value["time_to_completion"] = time_to_completion
    if abandoned is not None:
        feedback_value["abandoned"] = abandoned
    
    # Update existing record
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE feedback
            SET feedback_type = 'implicit',
                feedback_value = COALESCE(feedback_value, '{}'::jsonb) || %s::jsonb
            WHERE request_id = %s
        """, (json.dumps(feedback_value), request_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def collect_outcome_feedback(
    request_id: str,
    task_succeeded: Optional[bool] = None,
    needed_human_help: Optional[bool] = None,
    safety_filter_level: Optional[str] = None
):
    """Collect outcome-based feedback."""
    feedback_value = {}
    
    if task_succeeded is not None:
        feedback_value["task_succeeded"] = task_succeeded
    if needed_human_help is not None:
        feedback_value["needed_human_help"] = needed_human_help
    if safety_filter_level:
        feedback_value["safety_filter_level"] = safety_filter_level
    
    # Update existing record
    conn = get_db_connection()
    cur = conn.cursor()
    
    try:
        cur.execute("""
            UPDATE feedback
            SET feedback_type = 'outcome',
                feedback_value = COALESCE(feedback_value, '{}'::jsonb) || %s::jsonb
            WHERE request_id = %s
        """, (json.dumps(feedback_value), request_id))
        
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def get_feedback_data(
    prompt_version: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> list:
    """Get feedback data from database."""
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        query = "SELECT * FROM feedback WHERE 1=1"
        params = []
        
        if prompt_version:
            query += " AND prompt_version = %s"
            params.append(prompt_version)
        
        if start_date:
            query += " AND timestamp >= %s"
            params.append(start_date)
        
        if end_date:
            query += " AND timestamp <= %s"
            params.append(end_date)
        
        query += " ORDER BY timestamp DESC"
        
        cur.execute(query, params)
        results = cur.fetchall()
        
        # Convert to list of dicts
        return [dict(row) for row in results]
    finally:
        cur.close()
        conn.close()

