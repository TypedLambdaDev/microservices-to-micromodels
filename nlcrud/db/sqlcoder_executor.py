"""
SQLCoder-based database executor for Natural Language CRUD operations.
This module replaces the standard executor with one that uses a language model
to generate SQL queries directly from natural language.
"""
import sqlite3
import os
import requests
import json
from dotenv import load_dotenv
from nlcrud.db.schema import SCHEMA

# Load environment variables
load_dotenv()

# LLM Provider types
LLM_PROVIDER_API = "api"
LLM_PROVIDER_OLLAMA = "ollama"
LLM_PROVIDER_LMSTUDIO = "lmstudio"

# Ensure the db directory exists
os.makedirs("db", exist_ok=True)

# Connect to the SQLite database
conn = sqlite3.connect("db/db.sqlite", check_same_thread=False)
cursor = conn.cursor()

# SQLCoder configuration from environment variables
LLM_PROVIDER = os.environ.get("LLM_PROVIDER", LLM_PROVIDER_API).lower()
SQLCODER_API_URL = os.environ.get("SQLCODER_API_URL", "https://api.example.com/sqlcoder")
SQLCODER_API_KEY = os.environ.get("SQLCODER_API_KEY", "")

# Ollama configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "sqlcoder")

# LM Studio configuration
LMSTUDIO_URL = os.environ.get("LMSTUDIO_URL", "http://localhost:1234/v1/completions")
LMSTUDIO_MODEL = os.environ.get("LMSTUDIO_MODEL", "sqlcoder")

print(f"Using LLM provider: {LLM_PROVIDER}")

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

def generate_sql_from_nl(intent, resource, filters, data):
    """
    Generate SQL from natural language using SQLCoder.
    
    Args:
        intent (str): The intent (CREATE, READ, UPDATE, DELETE, SEARCH)
        resource (str): The resource type (user, order)
        filters (dict): Filters to apply
        data (dict): Data for creation or updates
        
    Returns:
        str: The generated SQL query
    """
    # Get table name from resource
    table = SCHEMA[resource]["table"] if resource in SCHEMA else None
    if not table:
        return None
    
    # Create a schema description for SQLCoder
    schema_description = "Database schema:\n"
    for res, details in SCHEMA.items():
        schema_description += f"Table: {details['table']}\n"
        schema_description += f"Fields: {', '.join(details['fields'])}\n\n"
    
    # Create a natural language description of the operation
    nl_description = f"{intent} operation on {table}"
    
    if filters:
        filter_desc = ", ".join([f"{k}={v}" for k, v in filters.items()])
        nl_description += f" with filters: {filter_desc}"
    
    if data:
        data_desc = ", ".join([f"{k}={v}" for k, v in data.items()])
        nl_description += f" with data: {data_desc}"
    
    # Prepare the prompt for SQLCoder
    prompt = f"""
    {schema_description}
    
    Task: Generate a SQL query for the following operation:
    {nl_description}
    
    The query should be compatible with SQLite.
    """
    
    try:
        print(f"Sending prompt to LLM ({LLM_PROVIDER}):\n{prompt}")
        
        if LLM_PROVIDER == LLM_PROVIDER_API:
            # Call SQLCoder API
            sql_query = call_sqlcoder_api(prompt)
        elif LLM_PROVIDER == LLM_PROVIDER_OLLAMA:
            # Call Ollama
            sql_query = call_ollama(prompt)
        elif LLM_PROVIDER == LLM_PROVIDER_LMSTUDIO:
            # Call LM Studio
            sql_query = call_lmstudio(prompt)
        else:
            # Fallback to simulation
            print(f"Unknown LLM provider: {LLM_PROVIDER}, using simulation")
            sql_query = simulate_sqlcoder_response(intent, table, filters, data)
        
        # If we couldn't extract a valid SQL query, try our fallback generator
        if not sql_query:
            print("Failed to extract valid SQL from LLM response. Using fallback SQL generator.")
            sql_query = generate_fallback_sql(intent, resource, filters, data)
            
            # If that also fails, fall back to simulation
            if not sql_query:
                print("Fallback SQL generator failed. Using simulation fallback.")
                sql_query = simulate_sqlcoder_response(intent, table, filters, data)
        
        print(f"Generated SQL query: {sql_query}")
        return sql_query
        
    except Exception as e:
        print(f"Error generating SQL with SQLCoder: {str(e)}")
        return None

def call_sqlcoder_api(prompt):
    """
    Call the SQLCoder API to generate SQL from natural language.
    
    Args:
        prompt (str): The prompt to send to the API
        
    Returns:
        str: The generated SQL query
    """
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {SQLCODER_API_KEY}"
    }
    
    payload = {
        "prompt": prompt,
        "max_tokens": 200
    }
    
    try:
        response = requests.post(SQLCODER_API_URL, headers=headers, json=payload)
        response.raise_for_status()
        sql_query = response.json().get("sql", "")
        return sql_query
    except Exception as e:
        print(f"Error calling SQLCoder API: {str(e)}")
        return None

def call_ollama(prompt):
    """
    Call Ollama to generate SQL from natural language.
    
    Args:
        prompt (str): The prompt to send to Ollama
        
    Returns:
        str: The generated SQL query
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False
    }
    
    try:
        response = requests.post(OLLAMA_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # Extract SQL from the response
        response_json = response.json()
        generated_text = response_json.get("response", "")
        
        # Extract SQL query from the generated text
        # Typically, the SQL will be in a code block or after certain markers
        sql_query = extract_sql_from_text(generated_text)
        
        return sql_query
    except Exception as e:
        print(f"Error calling Ollama: {str(e)}")
        return None

def call_lmstudio(prompt):
    """
    Call LM Studio to generate SQL from natural language.
    
    Args:
        prompt (str): The prompt to send to LM Studio
        
    Returns:
        str: The generated SQL query
    """
    headers = {
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": LMSTUDIO_MODEL,
        "prompt": prompt,
        "max_tokens": 500,
        "temperature": 0.1,
        "stop": ["```", ";"]
    }
    
    try:
        response = requests.post(LMSTUDIO_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # Extract SQL from the response
        response_json = response.json()
        generated_text = response_json.get("choices", [{}])[0].get("text", "")
        
        # Extract SQL query from the generated text
        sql_query = extract_sql_from_text(generated_text)
        
        return sql_query
    except Exception as e:
        print(f"Error calling LM Studio: {str(e)}")
        return None

def extract_sql_from_text(text):
    """
    Extract SQL query from generated text.
    
    Args:
        text (str): The generated text from the LLM
        
    Returns:
        str: The extracted SQL query
    """
    import re
    
    # Clean up the text
    text = text.strip()
    
    # Look for SQL between code blocks
    sql_match = re.search(r"```(?:sql)?\s*(.*?)\s*```", text, re.DOTALL)
    if sql_match:
        return sql_match.group(1).strip()
    
    # Look for SQL after "SQL:" or similar markers
    sql_marker_match = re.search(r"(?:SQL|Query):\s*(.*?)(?:\n\n|$)", text, re.DOTALL)
    if sql_marker_match:
        return sql_marker_match.group(1).strip()
    
    # Look for SQL statements with semicolons
    semicolon_match = re.search(r"([^;]*?;)", text)
    if semicolon_match:
        sql = semicolon_match.group(1).strip()
        # Check if it looks like SQL
        if re.search(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b", sql, re.IGNORECASE):
            return sql.rstrip(";")
    
    # Look for SQL in quotes
    quotes_match = re.search(r'["\'](SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)[^"\']*["\']', text, re.IGNORECASE)
    if quotes_match:
        sql = quotes_match.group(0).strip('\'"')
        return sql
    
    # If no specific markers, try to find anything that looks like SQL
    sql_keywords = [
        "SELECT", "INSERT", "UPDATE", "DELETE",
        "CREATE", "DROP", "ALTER", "FROM", "WHERE"
    ]
    
    # Try to find a SQL statement
    for keyword in sql_keywords:
        pattern = r"(?i)\b" + keyword + r"\b.*?(?:;|$)"
        sql_match = re.search(pattern, text, re.DOTALL)
        if sql_match:
            sql = sql_match.group(0).strip()
            # Clean up the SQL
            sql = re.sub(r"[\r\n]+", " ", sql)  # Replace newlines with spaces
            sql = re.sub(r"\s+", " ", sql)      # Normalize whitespace
            sql = re.sub(r";.*$", "", sql)      # Remove anything after semicolon
            sql = re.sub(r"```.*$", "", sql)    # Remove code block markers
            sql = re.sub(r"\+.*$", "", sql)     # Remove + comments
            sql = re.sub(r"/\*.*?\*/", "", sql, flags=re.DOTALL)  # Remove /* */ comments
            sql = re.sub(r"NOTE:.*$", "", sql, flags=re.IGNORECASE)  # Remove NOTE: comments
            sql = sql.strip()
            
            # If SQL still contains non-SQL text, try to clean it further
            if not re.match(r"^(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b", sql, re.IGNORECASE):
                continue
                
            return sql
    
    # If we couldn't find a valid SQL statement, try a more aggressive approach
    # Just extract the first line that looks like SQL
    lines = text.split('\n')
    for line in lines:
        line = line.strip()
        if any(keyword in line.upper() for keyword in sql_keywords):
            # Clean up the line
            line = re.sub(r"\+.*$", "", line)  # Remove + comments
            line = re.sub(r"/\*.*?\*/", "", line)  # Remove /* */ comments
            line = line.strip()
            if line:
                return line
    
    # If all else fails, return a default query based on the intent and table
    print("WARNING: Could not extract valid SQL from LLM response. Using fallback.")
    return None

def generate_fallback_sql(intent, resource, filters, data):
    """
    Generate a simple SQL query based on the intent, resource, filters, and data.
    
    Args:
        intent (str): The intent (CREATE, READ, UPDATE, DELETE, SEARCH)
        resource (str): The resource type (user, order)
        filters (dict): Filters to apply
        data (dict): Data for creation or updates
        
    Returns:
        str: A simple SQL query
    """
    table = SCHEMA[resource]["table"] if resource in SCHEMA else None
    if not table:
        return None
    
    if intent == "READ":
        if filters:
            where_clauses = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in filters.items()]
            return f"SELECT * FROM {table} WHERE {' AND '.join(where_clauses)}"
        else:
            return f"SELECT * FROM {table}"
    
    elif intent == "CREATE":
        if not data:
            return None
        keys = list(data.keys())
        values = [f"'{v}'" if isinstance(v, str) else str(v) for v in data.values()]
        return f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({', '.join(values)})"
    
    elif intent == "UPDATE":
        if not filters or not data:
            return None
        set_clauses = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in data.items()]
        where_clauses = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in filters.items()]
        return f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
    
    elif intent == "DELETE":
        if not filters:
            return None
        where_clauses = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in filters.items()]
        return f"DELETE FROM {table} WHERE {' AND '.join(where_clauses)}"
    
    elif intent == "SEARCH":
        conditions = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                conditions.append(f"{key} = {value}")
            elif isinstance(value, str):
                conditions.append(f"{key} LIKE '%{value}%'")
        
        if not conditions:
            return None
        
        return f"SELECT * FROM {table} WHERE {' AND '.join(conditions)}"
    
    return None

def simulate_sqlcoder_response(intent, table, filters, data):
    """
    Simulate SQLCoder response for development purposes.
    In a production environment, this would be replaced with actual API calls.
    
    Args:
        intent (str): The intent (CREATE, READ, UPDATE, DELETE, SEARCH)
        table (str): The table name
        filters (dict): Filters to apply
        data (dict): Data for creation or updates
        
    Returns:
        str: The simulated SQL query
    """
    if intent == "READ":
        sql = f"SELECT * FROM {table}"
        if filters:
            where_clauses = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in filters.items()]
            sql += " WHERE " + " AND ".join(where_clauses)
        return sql
    
    elif intent == "CREATE":
        if not data:
            return None
        keys = list(data.keys())
        values = [f"'{v}'" if isinstance(v, str) else str(v) for v in data.values()]
        return f"INSERT INTO {table} ({', '.join(keys)}) VALUES ({', '.join(values)})"
    
    elif intent == "UPDATE":
        if not filters or not data:
            return None
        set_clauses = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in data.items()]
        where_clauses = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in filters.items()]
        return f"UPDATE {table} SET {', '.join(set_clauses)} WHERE {' AND '.join(where_clauses)}"
    
    elif intent == "DELETE":
        if not filters:
            return None
        where_clauses = [f"{k} = '{v}'" if isinstance(v, str) else f"{k} = {v}" for k, v in filters.items()]
        return f"DELETE FROM {table} WHERE {' AND '.join(where_clauses)}"
    
    elif intent == "SEARCH":
        sql = f"SELECT * FROM {table} WHERE "
        conditions = []
        for key, value in data.items():
            if isinstance(value, (int, float)):
                conditions.append(f"{key} = {value}")
            elif isinstance(value, str):
                conditions.append(f"{key} LIKE '%{value}%'")
        
        if not conditions:
            return None
        
        return sql + " AND ".join(conditions)
    
    return None

def execute(action):
    """
    Execute a structured CRUD action against the database using SQLCoder.
    
    Args:
        action (dict): The structured action to execute
        
    Returns:
        dict: The result of the execution
    """
    print("\n===== SQLCODER DATABASE EXECUTION LAYER =====")
    print(f"Executing action: {action}")
    
    if action["resource"] is None:
        print("ERROR: No resource specified in action")
        return {"error": "No resource specified"}
    
    # Generate SQL from natural language using SQLCoder
    sql = generate_sql_from_nl(
        action["intent"], 
        action["resource"], 
        action["filters"], 
        action["data"]
    )
    
    if not sql:
        print("ERROR: Failed to generate SQL query")
        return {"error": "Failed to generate SQL query"}
    
    print(f"Executing SQL: {sql}")
    
    try:
        # Execute the SQL query
        cursor.execute(sql)
        
        # Handle different types of operations
        if action["intent"] == "READ" or action["intent"] == "SEARCH":
            columns = [description[0] for description in cursor.description]
            results = []
            
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))
            
            print(f"Query returned {len(results)} results")
            return {"status": "success", "data": results}
        
        elif action["intent"] == "CREATE":
            conn.commit()
            new_id = cursor.lastrowid
            print(f"Created new record with ID: {new_id}")
            return {"status": "success", "message": f"Created in {action['resource']}", "id": new_id}
        
        elif action["intent"] == "UPDATE" or action["intent"] == "DELETE":
            conn.commit()
            rows_affected = cursor.rowcount
            print(f"Affected {rows_affected} rows")
            return {
                "status": "success", 
                "message": f"{action['intent']} operation on {action['resource']}", 
                "rows_affected": rows_affected
            }
        
        else:
            print(f"ERROR: Unknown intent: {action['intent']}")
            return {"error": f"Unknown intent: {action['intent']}"}
            
    except Exception as e:
        print(f"Error executing SQL: {str(e)}")
        return {"error": f"SQL execution error: {str(e)}"}

# Initialize the database when the module is imported
initialize_database()