"""Tool interfaces and implementations."""

from abc import ABC, abstractmethod
from typing import List, Dict, Any
import os
import requests


class DatabaseTool(ABC):
    """Abstract interface for database search tool."""
    
    @abstractmethod
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the database."""
        pass


class RealDatabaseTool(DatabaseTool):
    """Real database tool implementation."""
    
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
        # In real implementation, would connect to database
        self._connected = True
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search the database (real implementation)."""
        # In real implementation, would query actual database
        # This is a placeholder
        return [
            {"id": 1, "email": "user1@example.com", "name": "User One"},
            {"id": 2, "email": "user2@example.com", "name": "User Two"}
        ][:limit]


class MockDatabaseTool(DatabaseTool):
    """Mock database tool for testing."""
    
    def __init__(self):
        self.data = [
            {"id": 1, "email": "user1@example.com", "name": "User One"},
            {"id": 2, "email": "user2@example.com", "name": "User Two"},
            {"id": 3, "email": "admin@example.com", "name": "Admin User"},
        ]
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """Search mock database."""
        # Simple mock search
        results = []
        query_lower = query.lower()
        for record in self.data:
            if query_lower in str(record).lower():
                results.append(record)
        return results[:limit]


class EmailTool(ABC):
    """Abstract interface for email service."""
    
    @abstractmethod
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send an email."""
        pass


class RealEmailTool(EmailTool):
    """Real email tool implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.emailservice.com"
    
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email via real API."""
        response = requests.post(
            f"{self.base_url}/send",
            json={"to": to, "subject": subject, "body": body},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()


class MockEmailTool(EmailTool):
    """Mock email tool for testing."""
    
    def __init__(self):
        self.sent_emails = []
    
    def send_email(self, to: str, subject: str, body: str) -> Dict[str, Any]:
        """Send email (mock - just stores it)."""
        email = {
            "to": to,
            "subject": subject,
            "body": body,
            "message_id": f"mock_{len(self.sent_emails)}"
        }
        self.sent_emails.append(email)
        return {"status": "sent", "message_id": email["message_id"]}


class SearchTool(ABC):
    """Abstract interface for search tool."""
    
    @abstractmethod
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search for content."""
        pass


class RealSearchTool(SearchTool):
    """Real search tool implementation."""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search via real API."""
        response = requests.get(
            "https://api.example.com/search",
            params={"q": query},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json().get("results", [])


class MockSearchTool(SearchTool):
    """Mock search tool for testing."""
    
    def search(self, query: str) -> List[Dict[str, Any]]:
        """Search (mock - returns fake data)."""
        return [
            {"id": 1, "title": "Result 1", "url": "https://example.com/1"},
            {"id": 2, "title": "Result 2", "url": "https://example.com/2"}
        ]


def create_tools(use_mocks: bool = False) -> Dict[str, Any]:
    """
    Create tools (real or mock) based on environment.
    
    Args:
        use_mocks: If True, use mock implementations
    
    Returns:
        Dictionary of tool instances
    """
    if use_mocks or os.getenv("USE_MOCKS") == "true":
        return {
            "database": MockDatabaseTool(),
            "email": MockEmailTool(),
            "search": MockSearchTool()
        }
    else:
        return {
            "database": RealDatabaseTool(os.getenv("DB_CONNECTION_STRING", "")),
            "email": RealEmailTool(os.getenv("EMAIL_API_KEY", "")),
            "search": RealSearchTool(os.getenv("SEARCH_API_KEY", ""))
        }
