"""Streamlit dashboard for LLM observability"""

import streamlit as st
import sqlite3
import pandas as pd
from datetime import datetime, timedelta

st.set_page_config(page_title="LLM Observability Dashboard", layout="wide")

db_path = "observability.db"


@st.cache_data(ttl=60)
def get_metrics():
    """Fetch metrics from database"""
    conn = sqlite3.connect(db_path)
    
    # Cost metrics
    try:
        cost_df = pd.read_sql_query("""
            SELECT 
                DATE(timestamp) as date,
                SUM(cost_usd) as total_cost,
                prompt_version
            FROM llm_calls
            WHERE timestamp > datetime('now', '-7 days')
            GROUP BY DATE(timestamp), prompt_version
            ORDER BY date
        """, conn)
    except:
        cost_df = pd.DataFrame()
    
    # Token metrics
    try:
        token_df = pd.read_sql_query("""
            SELECT 
                prompt_version,
                AVG(total_tokens) as avg_tokens,
                SUM(total_tokens) as total_tokens
            FROM llm_calls
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY prompt_version
        """, conn)
    except:
        token_df = pd.DataFrame()
    
    # Latency metrics
    try:
        latency_df = pd.read_sql_query("""
            SELECT 
                prompt_version,
                AVG(latency_ms) as avg_latency,
                MIN(latency_ms) as min_latency,
                MAX(latency_ms) as max_latency
            FROM llm_calls
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY prompt_version
        """, conn)
    except:
        latency_df = pd.DataFrame()
    
    # Branch metrics
    try:
        branch_df = pd.read_sql_query("""
            SELECT 
                to_node,
                COUNT(*) as count,
                SUM(CASE WHEN condition_result = 1 THEN 1 ELSE 0 END) * 1.0 / COUNT(*) as rate
            FROM branch_decisions
            WHERE timestamp > datetime('now', '-24 hours')
            GROUP BY to_node
        """, conn)
    except:
        branch_df = pd.DataFrame()
    
    conn.close()
    
    return cost_df, token_df, latency_df, branch_df


st.title("LLM Observability Dashboard")

try:
    cost_df, token_df, latency_df, branch_df = get_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_cost = cost_df['total_cost'].sum() if not cost_df.empty else 0
        st.metric("Total Cost (7d)", f"${total_cost:.2f}")
    
    with col2:
        total_tokens = token_df['total_tokens'].sum() if not token_df.empty else 0
        st.metric("Total Tokens (24h)", f"{total_tokens:,}")
    
    with col3:
        avg_latency = latency_df['avg_latency'].mean() if not latency_df.empty else 0
        st.metric("Avg Latency (24h)", f"{avg_latency:.0f}ms")
    
    with col4:
        total_requests = len(cost_df) if not cost_df.empty else 0
        st.metric("Total Requests", f"{total_requests:,}")
    
    st.subheader("Cost Trends")
    if not cost_df.empty:
        st.line_chart(cost_df.set_index('date')['total_cost'])
    else:
        st.info("No cost data available. Run some workflows first.")
    
    st.subheader("Token Usage by Prompt Version")
    if not token_df.empty:
        st.bar_chart(token_df.set_index('prompt_version')['avg_tokens'])
    else:
        st.info("No token data available.")
    
    st.subheader("Latency by Prompt Version")
    if not latency_df.empty:
        st.bar_chart(latency_df.set_index('prompt_version')['avg_latency'])
    else:
        st.info("No latency data available.")
    
    st.subheader("Branch Distribution")
    if not branch_df.empty:
        st.bar_chart(branch_df.set_index('to_node')['count'])
    else:
        st.info("No branch data available.")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
    st.info("Make sure you've run some workflows to generate data.")

