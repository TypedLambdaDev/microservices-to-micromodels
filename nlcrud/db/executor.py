import sqlite3
import os
from nlcrud.db.schema import SCHEMA

# Ensure the db directory exists
os.makedirs("db", exist_ok=True)

# Connect to the SQLite database
conn = sqlite3.connect("db/db.sqlite", check_same_thread=False)
cursor = conn.cursor()

def initialize_database():
    """
    Initialize the database by creating tables based on the schema.
    """
    # Create users table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        age INTEGER
    )
    ''')
    
    # Create orders table
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        amount REAL,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )
    ''')
    
    conn.commit()

def execute(action):
    """
    Execute a structured CRUD action against the database.
    
    Args:
        action (dict): The structured action to execute
        
    Returns:
        dict: The result of the execution
    """
    if action["resource"] is None:
        return {"error": "No resource specified"}
    
    table = SCHEMA[action["resource"]]["table"]
    
    if action["intent"] == "READ":
        return handle_read(table, action["filters"])
    
    elif action["intent"] == "CREATE":
        return handle_create(table, action["data"])
    
    elif action["intent"] == "UPDATE":
        return handle_update(table, action["filters"], action["data"])
    
    elif action["intent"] == "DELETE":
        return handle_delete(table, action["filters"])
    
    elif action["intent"] == "SEARCH":
        return handle_search(table, action["data"])
    
    else:
        return {"error": f"Unknown intent: {action['intent']}"}

def handle_read(table, filters):
    """Handle READ operations"""
    sql = f"SELECT * FROM {table}"
    params = []
    
    if filters:
        where_clauses = []
        for key, value in filters.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        sql += " WHERE " + " AND ".join(where_clauses)
    
    cursor.execute(sql, params)
    columns = [description[0] for description in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    return {"status": "success", "data": results}

def handle_create(table, data):
    """Handle CREATE operations"""
    if not data:
        return {"error": "No data provided for creation"}
    
    keys = list(data.keys())
    values = list(data.values())
    placeholders = ["?"] * len(keys)
    
    sql = f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({', '.join(placeholders)})"
    
    cursor.execute(sql, values)
    conn.commit()
    
    return {"status": "success", "message": f"Created in {table}", "id": cursor.lastrowid}

def handle_update(table, filters, data):
    """Handle UPDATE operations"""
    if not filters:
        return {"error": "No filters provided for update"}
    
    if not data:
        return {"error": "No data provided for update"}
    
    set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
    where_clauses = []
    params = list(data.values())
    
    for key, value in filters.items():
        where_clauses.append(f"{key} = ?")
        params.append(value)
    
    sql = f"UPDATE {table} SET {set_clause} WHERE {' AND '.join(where_clauses)}"
    
    cursor.execute(sql, params)
    conn.commit()
    
    return {"status": "success", "message": f"Updated in {table}", "rows_affected": cursor.rowcount}

def handle_delete(table, filters):
    """Handle DELETE operations"""
    if not filters:
        return {"error": "No filters provided for deletion"}
    
    where_clauses = []
    params = []
    
    for key, value in filters.items():
        where_clauses.append(f"{key} = ?")
        params.append(value)
    
    sql = f"DELETE FROM {table} WHERE {' AND '.join(where_clauses)}"
    
    cursor.execute(sql, params)
    conn.commit()
    
    return {"status": "success", "message": f"Deleted from {table}", "rows_affected": cursor.rowcount}

def handle_search(table, data):
    """Handle SEARCH operations"""
    sql = f"SELECT * FROM {table} WHERE "
    conditions = []
    params = []
    
    for key, value in data.items():
        if isinstance(value, int) or isinstance(value, float):
            conditions.append(f"{key} = ?")
            params.append(value)
        elif isinstance(value, str):
            conditions.append(f"{key} LIKE ?")
            params.append(f"%{value}%")
    
    if not conditions:
        return {"error": "No search criteria provided"}
    
    sql += " AND ".join(conditions)
    
    cursor.execute(sql, params)
    columns = [description[0] for description in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    return {"status": "success", "data": results}

# Initialize the database when the module is imported
initialize_database()