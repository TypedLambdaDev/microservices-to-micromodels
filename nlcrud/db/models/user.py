"""User domain model for NLCRUD.

Represents a user entity in the database with validation.
"""
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


@dataclass
class User:
    """Domain model for User entity.

    Attributes:
        id: Unique identifier (None if not yet persisted)
        name: User's name
        email: User's email address
        age: User's age
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    name: str
    email: str
    age: int
    id: Optional[int] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    def validate(self) -> bool:
        """Validate user data.

        Returns:
            True if valid

        Raises:
            ValueError: If validation fails
        """
        if not self.name or not self.name.strip():
            raise ValueError("User name cannot be empty")

        if not self.email or "@" not in self.email:
            raise ValueError("Invalid email format")

        if not isinstance(self.age, int) or self.age < 0 or self.age > 150:
            raise ValueError("Age must be a number between 0 and 150")

        return True

    def to_dict(self) -> dict:
        """Convert user to dictionary.

        Returns:
            Dictionary representation of user
        """
        return {
            "id": self.id,
            "name": self.name,
            "email": self.email,
            "age": self.age,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "User":
        """Create User from dictionary.

        Args:
            data: Dictionary with user data

        Returns:
            User instance
        """
        return cls(
            id=data.get("id"),
            name=data.get("name", ""),
            email=data.get("email", ""),
            age=data.get("age", 0),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
        )
