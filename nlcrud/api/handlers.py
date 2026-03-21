"""Request handlers for API endpoints.

Contains business logic for processing queries and generating SQL.
"""
import time
from typing import Tuple, Dict, Any

from nlcrud.logger import get_logger
from nlcrud.exceptions import NLCRUDError
from nlcrud.intent_classification.classifier import classifier
from nlcrud.entity_extraction.regex_extractor import extract_entities as regex_extract
from nlcrud.entity_extraction.spacy_extractor import extract_entities as spacy_extract
from nlcrud.action import build_action, Action
from nlcrud.config import get_config

logger = get_logger("api.handlers")


class QueryHandler:
    """Handler for natural language query processing.

    Processes queries through the full NLP pipeline:
    Intent → Entities → Action → Execution
    """

    def __init__(self):
        """Initialize handler with config and executors."""
        self.config = get_config()

        # Initialize executors
        from nlcrud.db.executor import RuleBasedExecutor
        from nlcrud.db.sqlcoder_executor import SQLCoderExecutor

        self.rule_based_executor = RuleBasedExecutor()
        self.sqlcoder_executor = SQLCoderExecutor()

        logger.debug("QueryHandler initialized")

    def handle(self, text: str, should_execute: bool = True) -> Tuple[Action, Dict[str, Any], float]:
        """Process a natural language query.

        Args:
            text: Natural language query text
            execute: Whether to execute the action

        Returns:
            Tuple of (action, result, latency_ms)

        Raises:
            NLCRUDError: If processing fails
        """
        start_time = time.time()
        logger.info(f"Processing query: {text[:50]}...")

        try:
            # Step 1: Intent classification
            logger.debug("Step 1: Intent classification")
            intent, confidence = classifier.predict(text)
            logger.info(f"Detected intent: {intent} (confidence: {confidence:.4f})")

            # Step 2: Entity extraction
            logger.debug("Step 2: Entity extraction")
            entities = self._extract_entities(text)
            logger.info(f"Extracted entities: {entities}")

            # Step 3: Action building
            logger.debug("Step 3: Action building")
            action = build_action(intent, entities)
            logger.info(f"Built action: {action}")

            # Step 4: Execution (optional)
            result = {}
            if should_execute:
                logger.debug("Step 4: Database execution")

                if self.config.use_sqlcoder:
                    result = self.sqlcoder_executor.execute(action)
                else:
                    result = self.rule_based_executor.execute(action)

                logger.info(f"Execution result: {result}")

            latency_ms = (time.time() - start_time) * 1000
            logger.info(f"Query processed in {latency_ms:.2f}ms")

            return action, result, latency_ms

        except NLCRUDError as e:
            logger.error(f"NLCRUD error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise NLCRUDError(f"Failed to process query: {e}") from e

    def _extract_entities(self, text: str) -> Dict[str, Any]:
        """Extract entities from text using configured extractor.

        Args:
            text: Text to extract entities from

        Returns:
            Dictionary with extracted entities

        Raises:
            Exception: If extraction fails
        """
        if self.config.use_regex_extractor:
            logger.debug("Using regex extractor")
            return regex_extract(text)

        # Try spaCy first, fall back to regex
        try:
            logger.debug("Using spaCy extractor")
            return spacy_extract(text)
        except Exception as e:
            logger.warning(f"spaCy extraction failed: {e}. Falling back to regex.")
            return regex_extract(text)


class SQLGenerationHandler:
    """Handler for SQL generation without execution.

    Processes queries up to SQL generation, useful for debugging.
    """

    def __init__(self):
        """Initialize handler with config."""
        self.config = get_config()
        self.query_handler = QueryHandler()
        logger.debug("SQLGenerationHandler initialized")

    def generate_sql(self, text: str) -> Tuple[Action, str]:
        """Generate SQL for a query without executing it.

        Args:
            text: Natural language query text

        Returns:
            Tuple of (action, sql_query)

        Raises:
            NLCRUDError: If SQL generation fails
        """
        logger.info(f"Generating SQL for: {text[:50]}...")

        if not self.config.use_sqlcoder:
            raise NLCRUDError(
                "SQL generation is only available when SQLCoder is enabled. "
                "Set USE_SQLCODER=1"
            )

        try:
            # Build action without execution
            action, _, _ = self.query_handler.handle(text, should_execute=False)

            # Generate SQL
            from nlcrud.db.sqlcoder_executor import generate_sql_from_nl

            sql = generate_sql_from_nl(
                action.intent,
                action.resource,
                action.filters,
                action.data
            )

            logger.info(f"Generated SQL: {sql}")
            return action, sql

        except NLCRUDError as e:
            logger.error(f"NLCRUD error: {e}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            raise NLCRUDError(f"Failed to generate SQL: {e}") from e
