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
    print("\n===== DATABASE EXECUTION LAYER =====")
    print(f"Executing action: {action}")
    
    if action["resource"] is None:
        print("ERROR: No resource specified in action")
        return {"error": "No resource specified"}
    
    table = SCHEMA[action["resource"]]["table"]
    print(f"Using table: {table}")
    
    if action["intent"] == "READ":
        print(f"Handling READ operation with filters: {action['filters']}")
        return handle_read(table, action["filters"])
    
    elif action["intent"] == "CREATE":
        print(f"Handling CREATE operation with data: {action['data']}")
        return handle_create(table, action["data"])
    
    elif action["intent"] == "UPDATE":
        print(f"Handling UPDATE operation with filters: {action['filters']} and data: {action['data']}")
        return handle_update(table, action["filters"], action["data"])
    
    elif action["intent"] == "DELETE":
        print(f"Handling DELETE operation with filters: {action['filters']}")
        return handle_delete(table, action["filters"])
    
    elif action["intent"] == "SEARCH":
        print(f"Handling SEARCH operation with criteria: {action['data']}")
        return handle_search(table, action["data"])
    
    else:
        print(f"ERROR: Unknown intent: {action['intent']}")
        return {"error": f"Unknown intent: {action['intent']}"}

def handle_read(table, filters):
    """Handle READ operations"""
    print("\n----- READ Operation Details -----")
    sql = f"SELECT * FROM {table}"
    params = []
    
    if filters:
        where_clauses = []
        for key, value in filters.items():
            where_clauses.append(f"{key} = ?")
            params.append(value)
        
        sql += " WHERE " + " AND ".join(where_clauses)
    
    print(f"Generated SQL: {sql}")
    print(f"SQL parameters: {params}")
    
    cursor.execute(sql, params)
    columns = [description[0] for description in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    print(f"Query returned {len(results)} results")
    print(f"Result data: {results}")
    
    return {"status": "success", "data": results}

def handle_create(table, data):
    """Handle CREATE operations"""
    print("\n----- CREATE Operation Details -----")
    
    if not data:
        print("ERROR: No data provided for creation")
        return {"error": "No data provided for creation"}
    
    keys = list(data.keys())
    values = list(data.values())
    placeholders = ["?"] * len(keys)
    
    sql = f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({', '.join(placeholders)})"
    
    print(f"Generated SQL: {sql}")
    print(f"SQL parameters: {values}")
    
    cursor.execute(sql, values)
    conn.commit()
    
    new_id = cursor.lastrowid
    print(f"Created new record with ID: {new_id}")
    
    return {"status": "success", "message": f"Created in {table}", "id": new_id}

def handle_update(table, filters, data):
    """Handle UPDATE operations"""
    print("\n----- UPDATE Operation Details -----")
    
    if not filters:
        print("ERROR: No filters provided for update")
        return {"error": "No filters provided for update"}
    
    if not data:
        print("ERROR: No data provided for update")
        return {"error": "No data provided for update"}
    
    set_clause = ", ".join([f"{key} = ?" for key in data.keys()])
    where_clauses = []
    params = list(data.values())
    
    for key, value in filters.items():
        where_clauses.append(f"{key} = ?")
        params.append(value)
    
    sql = f"UPDATE {table} SET {set_clause} WHERE {' AND '.join(where_clauses)}"
    
    print(f"Generated SQL: {sql}")
    print(f"SQL parameters: {params}")
    print(f"  - SET parameters: {list(data.values())}")
    print(f"  - WHERE parameters: {[filters[key] for key in filters]}")
    
    cursor.execute(sql, params)
    conn.commit()
    
    rows_affected = cursor.rowcount
    print(f"Updated {rows_affected} rows")
    
    return {"status": "success", "message": f"Updated in {table}", "rows_affected": rows_affected}

def handle_delete(table, filters):
    """Handle DELETE operations"""
    print("\n----- DELETE Operation Details -----")
    
    if not filters:
        print("ERROR: No filters provided for deletion")
        return {"error": "No filters provided for deletion"}
    
    where_clauses = []
    params = []
    
    for key, value in filters.items():
        where_clauses.append(f"{key} = ?")
        params.append(value)
    
    sql = f"DELETE FROM {table} WHERE {' AND '.join(where_clauses)}"
    
    print(f"Generated SQL: {sql}")
    print(f"SQL parameters: {params}")
    
    cursor.execute(sql, params)
    conn.commit()
    
    rows_affected = cursor.rowcount
    print(f"Deleted {rows_affected} rows")
    
    return {"status": "success", "message": f"Deleted from {table}", "rows_affected": rows_affected}

def handle_search(table, data):
    """Handle SEARCH operations"""
    print("\n----- SEARCH Operation Details -----")
    
    sql = f"SELECT * FROM {table} WHERE "
    conditions = []
    params = []
    
    for key, value in data.items():
        if isinstance(value, int) or isinstance(value, float):
            conditions.append(f"{key} = ?")
            params.append(value)
            print(f"Adding exact match condition for {key} = {value}")
        elif isinstance(value, str):
            conditions.append(f"{key} LIKE ?")
            params.append(f"%{value}%")
            print(f"Adding LIKE condition for {key} LIKE '%{value}%'")
    
    if not conditions:
        print("ERROR: No search criteria provided")
        return {"error": "No search criteria provided"}
    
    sql += " AND ".join(conditions)
    
    print(f"Generated SQL: {sql}")
    print(f"SQL parameters: {params}")
    
    cursor.execute(sql, params)
    columns = [description[0] for description in cursor.description]
    results = []
    
    for row in cursor.fetchall():
        results.append(dict(zip(columns, row)))
    
    print(f"Search returned {len(results)} results")
    print(f"Result data: {results}")
    
    return {"status": "success", "data": results}

# Initialize the database when the module is imported
initialize_database()