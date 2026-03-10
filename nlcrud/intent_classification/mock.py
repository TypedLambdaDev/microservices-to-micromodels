"""
A simple mock intent classifier for testing purposes.
This avoids the issues with fasttext and numpy.
"""

def detect_intent(text):
    """
    Detect the intent of the given text using simple keyword matching.
    
    Args:
        text (str): The input text to classify
        
    Returns:
        tuple: (intent, confidence)
    """
    text_lower = text.lower()
    
    # Simple keyword-based classification
    if any(word in text_lower for word in ["create", "add", "register", "new"]):
        return "CREATE", 0.95
    
    elif any(word in text_lower for word in ["show", "list", "get", "display"]):
        return "READ", 0.95
    
    elif any(word in text_lower for word in ["update", "change", "modify", "set"]):
        return "UPDATE", 0.95
    
    elif any(word in text_lower for word in ["delete", "remove", "drop"]):
        return "DELETE", 0.95
    
    elif any(word in text_lower for word in ["find", "search", "query", "where"]):
        return "SEARCH", 0.95
    
    # Default fallback
    return "READ", 0.6