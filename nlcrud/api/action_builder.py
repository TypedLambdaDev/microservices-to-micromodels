def build_action(intent, entities):
    """
    Build a structured action from the intent and entities.
    
    Args:
        intent (str): The detected intent (CREATE, READ, UPDATE, DELETE, SEARCH)
        entities (dict): The extracted entities
        
    Returns:
        dict: A structured action containing intent, resource, filters, and data
    """
    print("\n----- Action Builder Details -----")
    print(f"Building action with intent: {intent}")
    print(f"Entities received: {entities}")
    
    # Create the structured action
    action = {
        "intent": intent,
        "resource": entities["resource"],
        "filters": entities["filters"],
        "data": entities["data"]
    }
    
    print(f"Built action: {action}")
    
    # Validate the action
    if action["resource"] is None:
        print("WARNING: Action has no resource specified")
    
    if intent in ["UPDATE", "DELETE"] and not action["filters"]:
        print("WARNING: Update/Delete action has no filters specified")
    
    if intent == "CREATE" and not action["data"]:
        print("WARNING: Create action has no data specified")
    
    return action