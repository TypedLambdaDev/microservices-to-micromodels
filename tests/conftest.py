"""
Pytest configuration and shared fixtures for NLCRUD tests.
"""
import pytest
import sys
import os
from pathlib import Path

# Add src directory to path for imports
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Suppress warnings during tests
import warnings
warnings.filterwarnings("ignore")


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "age": 30
    }


@pytest.fixture
def sample_order_data():
    """Sample order data for testing."""
    return {
        "user_id": 1,
        "amount": 99.99
    }


@pytest.fixture
def sample_intent_texts():
    """Sample texts for intent classification testing."""
    return {
        "CREATE": [
            "create user with name John and email john@example.com and age 30",
            "add new user named Alice with email alice@example.com and age 25"
        ],
        "READ": [
            "show all users",
            "get user with id 1",
            "display user with email john@example.com"
        ],
        "UPDATE": [
            "update user with id 1 set email to newemail@example.com",
            "change user 5 age to 40"
        ],
        "DELETE": [
            "delete user with id 3",
            "remove user named John"
        ],
        "SEARCH": [
            "find users older than 30",
            "search users with email john@example.com"
        ]
    }


@pytest.fixture
def intent_classifier():
    """Fixture for intent classifier."""
    from nlcrud.intent_classification.classifier import classifier
    return classifier


@pytest.fixture
def regex_extractor():
    """Fixture for regex entity extractor."""
    from nlcrud.entity_extraction.regex_extractor import extract_entities
    return extract_entities


@pytest.fixture
def spacy_extractor():
    """Fixture for spaCy entity extractor."""
    from nlcrud.entity_extraction.spacy_extractor import extract_entities
    return extract_entities


@pytest.fixture
def action_builder():
    """Fixture for action builder."""
    from nlcrud.api.action_builder import build_action
    return build_action


@pytest.fixture
def schema():
    """Fixture for database schema."""
    from nlcrud.db.schema import SCHEMA
    return SCHEMA
