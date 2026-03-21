"""Abstract base class for database execution.

Provides a unified interface for different database execution implementations.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Union


class DatabaseExecutor(ABC):
    """Abstract base class for database executors.

    All database execution implementations must inherit from this class
    and implement the execute method.
    """

    @abstractmethod
    def execute(self, action: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        """Execute a structured action against the database.

        Args:
            action: A structured action object or dict containing:
                - intent: CRUD operation (CREATE, READ, UPDATE, DELETE, SEARCH)
                - resource: Target resource type (e.g., "user", "order")
                - filters: WHERE conditions for filtering
                - data: Data for INSERT/UPDATE operations

        Returns:
            Dictionary with execution result containing:
            - status: "success" or "error"
            - message: Human-readable result message
            - data or id: Execution result (rows, IDs, etc.)

        Raises:
            Exception: If execution fails
        """
        pass
