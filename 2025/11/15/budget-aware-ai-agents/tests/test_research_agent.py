"""Tests for research agent."""

import pytest
from src.budgets import RunBudget
from src.research_agent import ResearchAgent


class TestResearchAgent:
    """Tests for ResearchAgent."""
    
    def test_create_agent(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        agent = ResearchAgent(budget)
        
        assert agent.budget == budget
    
    def test_search_documents(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        agent = ResearchAgent(budget)
        
        results = agent.search_documents("test query", max_results=3)
        
        assert len(results) == 3
        assert all("test query" in doc for doc in results)
    
    def test_answer_within_budget(self):
        budget = RunBudget(max_steps=10, max_tokens=5000, max_seconds=30)
        agent = ResearchAgent(budget)
        
        result = agent.answer("What is Python?")
        
        assert "answer" in result
        assert "documents_found" in result
        assert "budget_used" in result
        assert "budget_remaining" in result
        assert result["documents_found"] > 0
    
    def test_answer_budget_exhausted(self):
        # Very small budget to trigger exhaustion
        budget = RunBudget(max_steps=1, max_tokens=50, max_seconds=5)
        agent = ResearchAgent(budget)
        
        result = agent.answer("What is machine learning?")
        
        assert "answer" in result
        assert result["budget_exhausted"] is True
    
    def test_graceful_exit(self):
        budget = RunBudget(max_steps=1, max_tokens=50, max_seconds=5)
        agent = ResearchAgent(budget)
        
        result = agent.answer("Complex question that needs many tokens")
        
        # Should still return an answer (even if brief)
        assert "answer" in result
        assert len(result["answer"]) > 0

