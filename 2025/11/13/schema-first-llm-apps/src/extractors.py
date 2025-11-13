"""Extractor patterns for schema-first LLM apps."""

from typing import Type, TypeVar
from pydantic import BaseModel
from .llm_client import LLMClient
from .schemas import EntityExtraction, StructuredSummary, ExtractionResult

T = TypeVar('T', bound=BaseModel)


class Extractor:
    """Base class for extractors."""
    
    def __init__(self, llm_client: LLMClient):
        """Initialize extractor with LLM client."""
        self.llm_client = llm_client
    
    def extract(self, text: str, schema_class: Type[T]) -> T:
        """Extract structured data from unstructured text.
        
        Args:
            text: Unstructured input text
            schema_class: Pydantic model class to extract into
            
        Returns:
            Validated instance of schema_class
        """
        prompt = f"Extract structured information from the following text:\n\n{text}"
        return self.llm_client.call_with_schema(prompt, schema_class)


class EntityExtractor(Extractor):
    """Extract entities, dates, and decisions from text."""
    
    def extract_entities(self, text: str) -> EntityExtraction:
        """Extract entities from text."""
        return self.extract(text, EntityExtraction)


class Summarizer(Extractor):
    """Generate structured summaries."""
    
    def summarize(self, text: str) -> StructuredSummary:
        """Generate structured summary of text."""
        prompt = (
            f"Summarize the following text. Return valid JSON matching the schema.\n\n{text}"
        )
        return self.llm_client.call_with_schema(
            prompt,
            StructuredSummary,
            system_prompt="You are a helpful assistant that creates structured summaries."
        )


class ContactExtractor(Extractor):
    """Extract contact information from text."""
    
    def extract_contact(self, text: str) -> ExtractionResult:
        """Extract name and email from text."""
        prompt = (
            f"Extract name and email from the following text. "
            f"If not found, set to null.\n\n{text}"
        )
        return self.llm_client.call_with_schema(
            prompt,
            ExtractionResult,
            system_prompt="Extract contact information. Return null for missing fields."
        )

