"""
Database interface module.
Provides a unified API for database operations.
"""
from .executor import execute
from .schema import SCHEMA

def execute_action(action):
    """
    Execute a structured action against the database.
    
    Args:
        action (dict): A structured action containing intent, resource, filters, and data
        
    Returns:
        dict: The result of the execution
    """
    return execute(action)

def get_schema():
    """
    Get the available schema information.
    
    Returns:
        dict: The schema information
    """
    return SCHEMA