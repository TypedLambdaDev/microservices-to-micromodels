#!/usr/bin/env python
"""
Test script to demonstrate data flow between layers in the NL CRUD system.
"""
from nlcrud.intent_classification.classifier import classifier
from nlcrud.entity_extraction.spacy_extractor import extract_entities
from nlcrud.api.action_builder import build_action
from nlcrud.db.executor import RuleBasedExecutor


# Initialize executor
executor = RuleBasedExecutor()


def test_data_flow(query):
    """
    Test the data flow between layers with a given query.

    Args:
        query (str): The natural language query to process
    """
    print("\n" + "="*50)
    print(f"Processing query: '{query}'")
    print("="*50)

    # Step 1: Intent Classification
    intent, confidence = classifier.predict(query)

    # Step 2: Entity Extraction
    entities = extract_entities(query)

    # Step 3: Action Building
    action = build_action(intent, entities)

    # Step 4: Database Execution
    result = executor.execute(action)
    
    # Final Result
    print("\n" + "="*50)
    print("FINAL RESULT:")
    print(f"Query: '{query}'")
    print(f"Intent: {intent} (confidence: {confidence:.4f})")
    print(f"Entities: {entities}")
    print(f"Action: {action}")
    print(f"Result: {result}")
    print("="*50)
    
    return result

if __name__ == "__main__":
    # Test with different types of queries
    test_data_flow("show all users")
    test_data_flow("find users with age 30")
    test_data_flow("create user with name John and email john@example.com and age 30")
    test_data_flow("update user with id 1 set email to updated@example.com")
    test_data_flow("delete user with id 30")