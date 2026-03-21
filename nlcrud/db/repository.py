"""Abstract repository pattern for database operations.

Provides a consistent interface for CRUD operations on domain entities.
"""
from abc import ABC, abstractmethod
from typing import List, Optional, TypeVar, Generic

from nlcrud.logger import get_logger

logger = get_logger("repository")

# Generic type for domain entities
T = TypeVar("T")


class Repository(ABC, Generic[T]):
    """Abstract base class for repository pattern.

    Provides consistent interface for CRUD operations on entities.
    Subclasses implement this for specific entity types (User, Order, etc).
    """

    @abstractmethod
    def create(self, entity: T) -> T:
        """Create a new entity.

        Args:
            entity: Entity to create

        Returns:
            Created entity with ID assigned

        Raises:
            ValueError: If entity is invalid
        """
        pass

    @abstractmethod
    def read(self, entity_id: int) -> Optional[T]:
        """Read an entity by ID.

        Args:
            entity_id: ID of entity to retrieve

        Returns:
            Entity if found, None otherwise
        """
        pass

    @abstractmethod
    def read_all(self) -> List[T]:
        """Read all entities.

        Returns:
            List of all entities
        """
        pass

    @abstractmethod
    def update(self, entity_id: int, entity: T) -> T:
        """Update an existing entity.

        Args:
            entity_id: ID of entity to update
            entity: Updated entity data

        Returns:
            Updated entity

        Raises:
            ValueError: If entity not found or invalid
        """
        pass

    @abstractmethod
    def delete(self, entity_id: int) -> bool:
        """Delete an entity by ID.

        Args:
            entity_id: ID of entity to delete

        Returns:
            True if entity was deleted, False if not found
        """
        pass

    @abstractmethod
    def find(self, **criteria) -> List[T]:
        """Find entities matching criteria.

        Args:
            **criteria: Field names and values to match

        Returns:
            List of matching entities
        """
        pass


class RepositoryError(Exception):
    """Base exception for repository operations."""

    pass


class EntityNotFoundError(RepositoryError):
    """Raised when entity is not found."""

    pass


class InvalidEntityError(RepositoryError):
    """Raised when entity is invalid."""

    pass
