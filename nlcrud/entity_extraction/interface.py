"""Abstract base class for entity extraction.

Provides a unified interface for different entity extraction implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class EntityExtractor(ABC):
    """Abstract base class for entity extractors.

    All entity extraction implementations must inherit from this class
    and implement the extract_entities method.
    """

    @abstractmethod
    def extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from the given text.

        Args:
            text: The input text to extract entities from

        Returns:
            Dictionary containing the extracted entities with keys:
            - resource: The target resource type (e.g., "user", "order")
            - filters: WHERE conditions for filtering
            - data: Data for INSERT/UPDATE operations

        Raises:
            Exception: If extraction fails
        """
        pass
