"""
Action builder for converting intent and entities into Action objects.

This module is responsible for taking the output of intent classification
and entity extraction, and building a structured Action that can be executed
against the database.
"""
from typing import Dict, Any, Optional

from nlcrud.logger import get_logger
from nlcrud.exceptions import ActionBuildError
from nlcrud.action.action import Action

logger = get_logger("action.builder")


class ActionBuilder:
    """Builds Action objects from intent and entities.

    This class converts the results of NLP processing (intent classification
    and entity extraction) into structured Action objects that represent
    CRUD operations.
    """

    def __init__(self, schema: Dict[str, Any]) -> None:
        """Initialize the ActionBuilder.

        Args:
            schema: Database schema defining available resources
        """
        self.schema = schema
        logger.debug(f"ActionBuilder initialized with schema for: {list(schema.keys())}")

    def build(
        self, intent: str, entities: Dict[str, Any]
    ) -> Action:
        """Build an Action from intent and extracted entities.

        Args:
            intent: The detected intent (CREATE, READ, UPDATE, DELETE, SEARCH)
            entities: Dictionary with resource, filters, and data keys

        Returns:
            Action object representing the CRUD operation

        Raises:
            ActionBuildError: If action cannot be built from intent and entities
        """
        logger.debug(f"Building action with intent: {intent}")
        logger.debug(f"Entities: {entities}")

        try:
            # Create the action
            action = Action(
                intent=intent,
                resource=entities.get("resource"),
                filters=entities.get("filters", {}),
                data=entities.get("data", {})
            )

            # Validate the action
            action.is_valid()

            logger.info(f"Built valid action: {action}")
            return action

        except ValueError as e:
            logger.error(f"Action validation failed: {e}")
            raise ActionBuildError(f"Invalid action: {e}") from e
        except KeyError as e:
            logger.error(f"Missing required field: {e}")
            raise ActionBuildError(f"Missing required field: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error building action: {e}")
            raise ActionBuildError(f"Failed to build action: {e}") from e

    def build_from_dict(self, data: Dict[str, Any]) -> Action:
        """Build an Action from a dictionary.

        Args:
            data: Dictionary with intent, resource, filters, data

        Returns:
            Action object

        Raises:
            ActionBuildError: If action cannot be built
        """
        try:
            return Action.from_dict(data)
        except (KeyError, ValueError) as e:
            logger.error(f"Failed to build action from dict: {e}")
            raise ActionBuildError(f"Invalid action data: {e}") from e


# Global builder instance (lazy-initialized)
_builder: Optional[ActionBuilder] = None


def get_builder(schema: Optional[Dict[str, Any]] = None) -> ActionBuilder:
    """Get the global ActionBuilder instance.

    Args:
        schema: Database schema (required on first call)

    Returns:
        ActionBuilder instance

    Raises:
        ActionBuildError: If schema not provided on first call
    """
    global _builder

    if _builder is None:
        if schema is None:
            raise ActionBuildError("Schema required to initialize ActionBuilder")
        _builder = ActionBuilder(schema)
        logger.debug("Initialized global ActionBuilder")

    return _builder


def set_builder(builder: ActionBuilder) -> None:
    """Set the global ActionBuilder instance.

    Useful for testing with different schemas.

    Args:
        builder: ActionBuilder instance to use globally
    """
    global _builder
    _builder = builder
    logger.debug("Set global ActionBuilder")


def build_action(intent: str, entities: Dict[str, Any]) -> Action:
    """Convenience function to build an action using global builder.

    Args:
        intent: The detected intent
        entities: Dictionary with extracted entities

    Returns:
        Action object

    Raises:
        ActionBuildError: If action cannot be built
    """
    builder = get_builder()
    return builder.build(intent, entities)
