import re
from nlcrud.db.schema import SCHEMA

def extract_entities(text: str):
    """
    Extract entities from the given text based on the schema.
    
    Args:
        text (str): The input text to extract entities from
        
    Returns:
        dict: A dictionary containing the extracted resource, filters, and data
    """
    entities = {
        "resource": None,
        "filters": {},
        "data": {}
    }
    
    # Convert text to lowercase for case-insensitive matching
    text_lower = text.lower()
    words = text_lower.split()
    
    # Extract resource type (user, order, etc.)
    for resource in SCHEMA:
        if resource in words:
            entities["resource"] = resource
            break
    
    # If we're showing "all users" or similar, set the resource
    if "users" in words and entities["resource"] is None:
        entities["resource"] = "user"
    
    if "orders" in words and entities["resource"] is None:
        entities["resource"] = "order"
    
    # Extract ID filter
    id_match = re.search(r"id\s*(\d+)", text_lower)
    if id_match:
        entities["filters"]["id"] = int(id_match.group(1))
    
    # Extract name
    name_match = re.search(r"name\s+([a-zA-Z]+)", text_lower)
    if name_match:
        entities["data"]["name"] = name_match.group(1)
    
    # Extract age
    age_match = re.search(r"age\s*(\d+)", text_lower)
    if age_match:
        entities["data"]["age"] = int(age_match.group(1))
    
    # Alternative age pattern: "change age of user with id X to Y"
    alt_age_match = re.search(r"change\s+age\s+.*\s+to\s+(\d+)", text_lower)
    if alt_age_match and "age" not in entities["data"]:
        entities["data"]["age"] = int(alt_age_match.group(1))
    
    # Extract email
    email_match = re.search(r"[\w\.-]+@[\w\.-]+", text)
    if email_match:
        entities["data"]["email"] = email_match.group(0)
    
    # Extract amount (for orders)
    amount_match = re.search(r"amount\s*(\d+(?:\.\d+)?)", text_lower)
    if amount_match:
        entities["data"]["amount"] = float(amount_match.group(1))
    
    # Extract user_id (for orders)
    user_id_match = re.search(r"user[_\s]*id\s*(\d+)", text_lower)
    if user_id_match:
        entities["data"]["user_id"] = int(user_id_match.group(1))
    
    # For search queries, move data to filters if appropriate
    if "find" in words or "search" in words:
        if entities["resource"] is None:
            # Try to infer resource from context
            if "user" in words or "users" in words:
                entities["resource"] = "user"
            elif "order" in words or "orders" in words:
                entities["resource"] = "order"
        
        # Move data to filters for search
        for key, value in list(entities["data"].items()):
            if key not in entities["filters"]:
                entities["filters"][key] = value
    
    return entities