"""Order domain model for NLCRUD.

Represents an order entity in the database with validation.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class Order:
    """Domain model for Order entity.

    Attributes:
        id: Unique identifier (None if not yet persisted)
        user_id: Reference to User
        amount: Order amount
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    user_id: int
    amount: float
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self) -> bool:
        """Validate order data.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if not isinstance(self.user_id, int) or self.user_id <= 0:
            raise ValueError("User ID must be a positive integer")

        if not isinstance(self.amount, (int, float)) or self.amount < 0:
            raise ValueError("Amount must be a non-negative number")

        return True

    def to_dict(self) -> dict:
        """Convert order to dictionary.

        Returns:
            Dictionary representation of order
        """
        return {
            "id": self.id,
            "user_id": self.user_id,
            "amount": self.amount,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Order":
        """Create Order from dictionary.

        Args:
            data: Dictionary with order data

        Returns:
            Order instance
        """
        return cls(
            id=data.get("id"),
            user_id=data.get("user_id", 0),
            amount=data.get("amount", 0.0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
