"""Abstract base class for intent classification.

Provides a unified interface for different intent classification implementations.
"""
from abc import ABC, abstractmethod
from typing import Tuple


class IntentClassifier(ABC):
    """Abstract base class for intent classifiers.

    All intent classification implementations must inherit from this class
    and implement the predict method.
    """

    @abstractmethod
    def predict(self, text: str) -> Tuple[str, float]:
        """Predict the intent of the given text.

        Args:
            text: The input text to classify

        Returns:
            Tuple of (intent, confidence) where intent is one of
            CREATE, READ, UPDATE, DELETE, SEARCH and confidence is 0.0-1.0

        Raises:
            Exception: If prediction fails
        """
        pass
