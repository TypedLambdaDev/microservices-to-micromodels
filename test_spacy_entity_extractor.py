import unittest
from spacy_entity_extractor import extract_entities

class TestSpacyEntityExtractor(unittest.TestCase):
    """Test cases for the spaCy-based entity extractor."""
    
    def test_extract_resource(self):
        """Test extracting resource types."""
        # Test singular form
        result = extract_entities("show me user with id 1")
        self.assertEqual(result["resource"], "user")
        
        # Test plural form
        result = extract_entities("find all users")
        self.assertEqual(result["resource"], "user")
        
        # Test with orders
        result = extract_entities("show all orders")
        self.assertEqual(result["resource"], "order")
    
    def test_extract_id(self):
        """Test extracting ID filters."""
        result = extract_entities("get user with id 42")
        self.assertEqual(result["filters"]["id"], 42)
        
        result = extract_entities("show order id 123")
        self.assertEqual(result["filters"]["id"], 123)
    
    def test_extract_name(self):
        """Test extracting name entities."""
        result = extract_entities("create user with name John")
        self.assertEqual(result["data"]["name"], "John")
        
        # Test with full name (should recognize as PERSON entity)
        result = extract_entities("add a new user named John Smith")
        self.assertEqual(result["data"]["name"], "John Smith")
    
    def test_extract_age(self):
        """Test extracting age entities."""
        result = extract_entities("create user with age 30")
        self.assertEqual(result["data"]["age"], 30)
        
        result = extract_entities("change age of user with id 1 to 35")
        self.assertEqual(result["data"]["age"], 35)
    
    def test_extract_email(self):
        """Test extracting email entities."""
        result = extract_entities("create user with email john@example.com")
        self.assertEqual(result["data"]["email"], "john@example.com")
    
    def test_extract_amount(self):
        """Test extracting amount entities for orders."""
        result = extract_entities("create order with amount 99.99")
        self.assertEqual(result["data"]["amount"], 99.99)
    
    def test_extract_user_id(self):
        """Test extracting user_id for orders."""
        result = extract_entities("create order with user_id 5")
        self.assertEqual(result["data"]["user_id"], 5)
        
        result = extract_entities("add order for user id 10")
        self.assertEqual(result["data"]["user_id"], 10)
    
    def test_search_queries(self):
        """Test handling of search queries."""
        result = extract_entities("find users with age 25")
        self.assertEqual(result["resource"], "user")
        self.assertEqual(result["filters"]["age"], 25)
        
        result = extract_entities("search for orders with amount 50")
        self.assertEqual(result["resource"], "order")
        self.assertEqual(result["filters"]["amount"], 50.0)
    
    def test_complex_queries(self):
        """Test more complex natural language queries."""
        result = extract_entities("find all users who are 30 years old with email john@example.com")
        self.assertEqual(result["resource"], "user")
        # Age could be in either data or filters depending on implementation
        age_value = result["filters"].get("age", result["data"].get("age"))
        self.assertEqual(age_value, 30)
        # Email could be in either data or filters depending on implementation
        email_value = result["filters"].get("email", result["data"].get("email"))
        self.assertEqual(email_value, "john@example.com")
        
        result = extract_entities("update the user with id 5 and change their name to Alice")
        self.assertEqual(result["resource"], "user")
        self.assertEqual(result["filters"]["id"], 5)
        self.assertEqual(result["data"]["name"], "Alice")

if __name__ == "__main__":
    unittest.main()