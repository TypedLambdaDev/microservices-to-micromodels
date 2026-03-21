import time
from nlcrud.intent_classification.classifier import classifier
from nlcrud.entity_extraction.regex_extractor import extract_entities
from nlcrud.api.action_builder import build_action
from nlcrud.db.executor import execute

def process_query(text):
    """
    Process a natural language query and execute the corresponding CRUD operation.
    
    Args:
        text (str): The natural language query
        
    Returns:
        dict: The result of the query execution
    """
    start_time = time.time()
    
    # Detect intent
    intent, confidence = classifier.predict(text)
    print(f"Intent: {intent} (confidence: {confidence:.4f})")
    
    # Extract entities
    entities = extract_entities(text)
    print(f"Entities: {entities}")
    
    # Build action
    action = build_action(intent, entities)
    print(f"Action: {action}")
    
    # Execute action
    result = execute(action)
    print(f"Result: {result}")
    
    # Calculate latency
    latency_ms = (time.time() - start_time) * 1000
    print(f"Latency: {latency_ms:.2f} ms")
    
    return {
        "action": action,
        "result": result,
        "latency_ms": latency_ms
    }

def run_tests():
    """Run a series of test queries"""
    test_queries = [
        # CREATE tests
        "create user with name John and email john@example.com and age 30",
        "add new user with name Alice and email alice@example.com and age 25",
        
        # READ tests
        "show all users",
        "get user with id 1",
        
        # UPDATE tests
        "update user with id 1 set email to updated@example.com",
        "change age of user with id 2 to 35",
        
        # DELETE tests
        "delete user with id 3",
        
        # SEARCH tests
        "find users with age 30",
        "search for users with email alice@example.com"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n{'='*50}")
        print(f"Test {i+1}: {query}")
        print(f"{'='*50}")
        
        try:
            process_query(query)
        except Exception as e:
            print(f"Error: {str(e)}")
        
        print()

if __name__ == "__main__":
    run_tests()