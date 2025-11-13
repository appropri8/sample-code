"""A/B testing utilities"""

import hashlib
import random
import json
from datetime import datetime
from typing import Dict, Optional
import psycopg2
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


def hash_user_id(user_id: str) -> str:
    """Hash user ID for privacy."""
    return hashlib.sha256(user_id.encode()).hexdigest()[:16]


def route_to_variant(user_id: str, variants: Dict[str, float]) -> str:
    """
    Route user to A/B test variant based on consistent hashing.
    
    Args:
        user_id: User identifier
        variants: Dictionary mapping variant names to weights (0.0-1.0)
    
    Returns:
        Variant name
    """
    # Use consistent hashing so same user always gets same variant
    hash_value = int(hashlib.md5(user_id.encode()).hexdigest(), 16)
    total_weight = sum(variants.values())
    
    if total_weight == 0:
        return list(variants.keys())[0] if variants else "default"
    
    random.seed(hash_value)
    rand = random.random() * total_weight
    
    cumulative = 0
    for variant, weight in variants.items():
        cumulative += weight
        if rand <= cumulative:
            return variant
    
    # Fallback to first variant
    return list(variants.keys())[0]


def get_or_assign_variant(
    test_name: str,
    user_id: str,
    variants: Dict[str, float]
) -> str:
    """
    Get existing variant assignment or assign new one.
    Ensures same user always gets same variant.
    """
    user_id_hash = hash_user_id(user_id)
    
    # Check if user already has assignment
    conn = get_db_connection()
    cur = conn.cursor(cursor_factory=RealDictCursor)
    
    try:
        cur.execute("""
            SELECT variant FROM ab_test_assignments
            WHERE test_name = %s AND user_id_hash = %s
        """, (test_name, user_id_hash))
        
        result = cur.fetchone()
        if result:
            return result["variant"]
        
        # Assign new variant
        variant = route_to_variant(user_id, variants)
        
        # Store assignment
        cur.execute("""
            INSERT INTO ab_test_assignments (test_name, user_id_hash, variant, timestamp)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (test_name, user_id_hash) DO NOTHING
        """, (test_name, user_id_hash, variant, datetime.utcnow()))
        
        conn.commit()
        return variant
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        cur.close()
        conn.close()


def log_ab_test(
    request_id: str,
    user_id: str,
    test_name: str,
    variant: str,
    result: Dict
):
    """Log A/B test assignment and result."""
    from src.feedback import insert_feedback
    
    user_id_hash = hash_user_id(user_id)
    
    # Store in feedback table with metadata
    insert_feedback(
        conversation_id=f"ab_test_{test_name}",
        turn_id=1,
        request_id=request_id,
        input_text=result.get("input", ""),
        output_text=result.get("output", ""),
        prompt_version=variant,
        model=result.get("model", "gpt-4"),
        user_id_hash=user_id_hash,
        metadata={
            "ab_test": test_name,
            "variant": variant,
            "latency_ms": result.get("latency_ms", 0),
            "cost_estimate": result.get("cost_estimate", 0)
        }
    )


def get_ab_test_results(
    test_name: str,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None
) -> Dict[str, Dict]:
    """Get A/B test results grouped by variant."""
    from src.feedback import get_feedback_data
    from src.metrics import compare_prompt_versions
    
    # Get feedback data for this test
    feedback_data = get_feedback_data(start_date=start_date, end_date=end_date)
    
    # Filter by test name
    test_data = [
        f for f in feedback_data
        if f.get("metadata", {}).get("ab_test") == test_name
    ]
    
    # Group by variant and calculate metrics
    return compare_prompt_versions(test_data)

