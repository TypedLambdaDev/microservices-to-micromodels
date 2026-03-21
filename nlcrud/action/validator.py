"""Action validation logic for NLCRUD.

Provides validation rules and checks for Action objects.
"""
from typing import Dict, Any, List

from nlcrud.logger import get_logger
from nlcrud.exceptions import ValidationError
from nlcrud.action.action import Action

logger = get_logger("action.validator")


class ActionValidator:
    """Validates Action objects against schema and business rules."""

    def __init__(self, schema: Dict[str, Any]) -> None:
        """Initialize validator with database schema.

        Args:
            schema: Database schema defining resources and fields
        """
        self.schema = schema
        logger.debug(f"ActionValidator initialized with resources: {list(schema.keys())}")

    def validate(self, action: Action) -> bool:
        """Validate an action against all rules.

        Args:
            action: Action to validate

        Returns:
            True if action passes all validation

        Raises:
            ValidationError: If action fails any validation rule
        """
        logger.debug(f"Validating action: {action}")

        # Check structural validity
        self._validate_structure(action)

        # Check against schema
        self._validate_against_schema(action)

        # Check business rules
        self._validate_business_rules(action)

        logger.info(f"Action validation passed: {action}")
        return True

    def _validate_structure(self, action: Action) -> None:
        """Validate action structure.

        Args:
            action: Action to validate

        Raises:
            ValidationError: If structure is invalid
        """
        if not action.intent:
            raise ValidationError("Action must have intent")

        valid_intents = ("CREATE", "READ", "UPDATE", "DELETE", "SEARCH")
        if action.intent not in valid_intents:
            raise ValidationError(f"Invalid intent: {action.intent}")

    def _validate_against_schema(self, action: Action) -> None:
        """Validate action against database schema.

        Args:
            action: Action to validate

        Raises:
            ValidationError: If action violates schema
        """
        if not action.resource:
            raise ValidationError("Action must have a resource")

        if action.resource not in self.schema:
            raise ValidationError(f"Unknown resource: {action.resource}")

        resource_schema = self.schema[action.resource]
        allowed_fields = set(resource_schema.get("fields", []))

        # Validate filter fields exist in schema
        for field_name in action.filters.keys():
            if field_name not in allowed_fields:
                logger.warning(f"Filter field not in schema: {field_name}")

        # Validate data fields exist in schema
        for field_name in action.data.keys():
            if field_name not in allowed_fields:
                logger.warning(f"Data field not in schema: {field_name}")

    def _validate_business_rules(self, action: Action) -> None:
        """Validate business rules for action.

        Args:
            action: Action to validate

        Raises:
            ValidationError: If business rule is violated
        """
        # UPDATE and DELETE must have filters
        if action.intent in ("UPDATE", "DELETE"):
            if not action.filters:
                raise ValidationError(
                    f"{action.intent} operation requires filters"
                )

        # CREATE must have data
        if action.intent == "CREATE":
            if not action.data:
                raise ValidationError("CREATE operation requires data")

        # READ and SEARCH can work without filters, but that's a warning
        if action.intent in ("READ", "SEARCH") and not action.filters:
            logger.warning(f"{action.intent} has no filters (will return all records)")

    def get_validation_errors(self, action: Action) -> List[str]:
        """Get all validation errors for an action without raising.

        Args:
            action: Action to validate

        Returns:
            List of validation error messages (empty if valid)
        """
        errors: List[str] = []

        try:
            self._validate_structure(action)
        except ValidationError as e:
            errors.append(str(e))

        try:
            self._validate_against_schema(action)
        except ValidationError as e:
            errors.append(str(e))

        try:
            self._validate_business_rules(action)
        except ValidationError as e:
            errors.append(str(e))

        return errors
