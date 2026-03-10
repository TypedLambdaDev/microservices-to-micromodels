def build_action(intent, entities):
    """
    Build a structured action from the intent and entities.
    
    Args:
        intent (str): The detected intent (CREATE, READ, UPDATE, DELETE, SEARCH)
        entities (dict): The extracted entities
        
    Returns:
        dict: A structured action containing intent, resource, filters, and data
    """
    return {
        "intent": intent,
        "resource": entities["resource"],
        "filters": entities["filters"],
        "data": entities["data"]
    }