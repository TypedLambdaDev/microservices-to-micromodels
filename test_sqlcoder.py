"""
Test script for SQLCoder-based database operations.
"""
import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set environment variables to use SQLCoder
os.environ["USE_SQLCODER"] = "true"

# Check if we're testing with a local LLM
llm_provider = os.environ.get("LLM_PROVIDER", "api")
print(f"Testing with LLM provider: {llm_provider}")

# Import after setting environment variables
from nlcrud.api.app import app
from fastapi.testclient import TestClient

# Create test client
client = TestClient(app)

def test_query_endpoint():
    """Test the query endpoint with SQLCoder enabled."""
    print("\n=== Testing query endpoint with SQLCoder ===")
    
    # Test a simple query
    response = client.post(
        "/query",
        json={"text": "show me all users"}
    )
    
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Action: {json.dumps(result['action'], indent=2)}")
        print(f"Result: {json.dumps(result['result'], indent=2)}")
        print(f"Latency: {result['latency_ms']} ms")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def test_generate_sql_endpoint():
    """Test the generate_sql endpoint."""
    print("\n=== Testing generate_sql endpoint ===")
    
    # Test SQL generation
    response = client.post(
        "/generate_sql",
        json={"text": "create a new user named John with email john@example.com and age 30"}
    )
    
    print(f"Response status code: {response.status_code}")
    if response.status_code == 200:
        result = response.json()
        print(f"Action: {json.dumps(result['action'], indent=2)}")
        print(f"Generated SQL: {result['sql']}")
    else:
        print(f"Error: {response.text}")
    
    return response.status_code == 200

def test_crud_operations():
    """Test CRUD operations with SQLCoder."""
    print("\n=== Testing CRUD operations with SQLCoder ===")
    
    # Test CREATE
    create_response = client.post(
        "/query",
        json={"text": "add a new user named Alice with email alice@example.com and age 25"}
    )
    
    if create_response.status_code == 200:
        print("CREATE operation successful")
        create_result = create_response.json()
        user_id = create_result["result"].get("id")
        print(f"Created user with ID: {user_id}")
        
        # Test READ
        read_response = client.post(
            "/query",
            json={"text": f"show me user with id {user_id}"}
        )
        
        if read_response.status_code == 200:
            print("READ operation successful")
            read_result = read_response.json()
            print(f"User data: {json.dumps(read_result['result'], indent=2)}")
            
            # Test UPDATE
            update_response = client.post(
                "/query",
                json={"text": f"update user with id {user_id} set age to 26"}
            )
            
            if update_response.status_code == 200:
                print("UPDATE operation successful")
                
                # Test DELETE
                delete_response = client.post(
                    "/query",
                    json={"text": f"delete user with id {user_id}"}
                )
                
                if delete_response.status_code == 200:
                    print("DELETE operation successful")
                    return True
    
    return False

if __name__ == "__main__":
    # Run tests
    query_test_passed = test_query_endpoint()
    sql_gen_test_passed = test_generate_sql_endpoint()
    crud_test_passed = test_crud_operations()
    
    # Print summary
    print("\n=== Test Summary ===")
    print(f"Query endpoint test: {'PASSED' if query_test_passed else 'FAILED'}")
    print(f"SQL generation test: {'PASSED' if sql_gen_test_passed else 'FAILED'}")
    print(f"CRUD operations test: {'PASSED' if crud_test_passed else 'FAILED'}")
    
    if query_test_passed and sql_gen_test_passed and crud_test_passed:
        print("\nAll tests PASSED!")
    else:
        print("\nSome tests FAILED!")