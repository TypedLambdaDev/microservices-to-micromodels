"""
Action domain object for NLCRUD.

Represents a structured CRUD operation that has been built from
natural language intent and extracted entities.
"""
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, Literal

from nlcrud.logger import get_logger

logger = get_logger("action")


@dataclass
class Action:
    """Represents a structured CRUD operation.

    This is the core domain object that bridges the gap between
    natural language understanding and database execution.

    Attributes:
        intent: The CRUD operation type (CREATE, READ, UPDATE, DELETE, SEARCH)
        resource: The target resource type (e.g., "user", "order")
        filters: WHERE conditions for filtering (id, name, email, etc.)
        data: Data for INSERT/UPDATE operations
    """

    intent: Literal["CREATE", "READ", "UPDATE", "DELETE", "SEARCH"]
    resource: Optional[str] = None
    filters: Dict[str, Any] = field(default_factory=dict)
    data: Dict[str, Any] = field(default_factory=dict)

    def is_valid(self) -> bool:
        """Check if action is structurally valid.

        Returns:
            True if action is valid

        Raises:
            ValueError: If action is invalid
        """
        # Resource is always required
        if not self.resource:
            raise ValueError("Action must have a resource specified")

        # UPDATE and DELETE require filters
        if self.intent in ("UPDATE", "DELETE"):
            if not self.filters:
                raise ValueError(f"{self.intent} action must have filters")

        # CREATE requires data
        if self.intent == "CREATE":
            if not self.data:
                raise ValueError("CREATE action must have data specified")

        return True

    def __repr__(self) -> str:
        """String representation of action."""
        return (
            f"Action(intent={self.intent}, resource={self.resource}, "
            f"filters={self.filters}, data={self.data})"
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert action to dictionary (for API responses).

        Returns:
            Dictionary representation of action
        """
        return {
            "intent": self.intent,
            "resource": self.resource,
            "filters": self.filters,
            "data": self.data
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Action":
        """Create Action from dictionary.

        Args:
            data: Dictionary with intent, resource, filters, data

        Returns:
            Action instance

        Raises:
            KeyError: If required fields are missing
            ValueError: If values are invalid
        """
        return cls(
            intent=data["intent"],
            resource=data.get("resource"),
            filters=data.get("filters", {}),
            data=data.get("data", {})
        )
