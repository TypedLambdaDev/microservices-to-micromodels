"""SQLCoder-based database executor for Natural Language CRUD operations.

This module uses Ollama to generate SQL queries from natural language.
"""
import sqlite3
import os
from typing import Any, Dict, Union

import requests
from dotenv import load_dotenv

from nlcrud.db.schema import SCHEMA
from nlcrud.db.interface import DatabaseExecutor

# Load environment variables
load_dotenv()

# Ensure the db directory exists
os.makedirs("db", exist_ok=True)

# Connect to the SQLite database
conn = sqlite3.connect("db/db.sqlite", check_same_thread=False)
cursor = conn.cursor()

# Ollama configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "sqlcoder")

print(f"Using Ollama LLM provider at {OLLAMA_URL} with model {OLLAMA_MODEL}")


def generate_sql_from_nl(intent, resource, filters, data):
    """
    Generate SQL from natural language using Ollama.

    Args:
        intent (str): The intent (CREATE, READ, UPDATE, DELETE, SEARCH)/
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

    # Create a schema description for Ollama
    schema_description = "Database schema:\n"
    for _, details in SCHEMA.items():
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

    # Prepare the prompt for Ollama
    prompt = f"""
{schema_description}

Task: Generate a SQL query for the following operation:
{nl_description}

The query should be compatible with SQLite.
Respond with only the SQL query, no explanations.
"""

    try:
        print(f"Sending prompt to Ollama:\n{prompt}")

        # Call Ollama
        sql_query = call_ollama(prompt)

        # If we couldn't extract a valid SQL query, try our fallback generator
        if not sql_query:
            print("Failed to extract valid SQL from Ollama response. Using fallback SQL generator.")
            sql_query = generate_fallback_sql(intent, resource, filters, data)

        print(f"Generated SQL query: {sql_query}")
        return sql_query

    except Exception as e:
        print(f"Error generating SQL with Ollama: {str(e)}")
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

def extract_sql_from_text(text):
    """
    Extract SQL query from generated Ollama response.

    Args:
        text (str): The generated text from Ollama
        
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


class SQLCoderExecutor(DatabaseExecutor):
    """LLM-based database executor using SQLCoder and Ollama.

    Generates SQL queries from natural language using Ollama's SQLCoder model.
    Falls back to rule-based SQL generation if LLM fails.
    """

    def __init__(self, ollama_url: str = None, ollama_model: str = None) -> None:
        """Initialize SQLCoder executor.

        Args:
            ollama_url: Ollama API endpoint URL
            ollama_model: Ollama model name
        """
        self.ollama_url = ollama_url or os.environ.get(
            "OLLAMA_URL", "http://localhost:11434/api/generate"
        )
        self.ollama_model = ollama_model or os.environ.get("OLLAMA_MODEL", "sqlcoder")
        self.conn = conn
        self.cursor = cursor

    def execute(self, action: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        """Execute action using LLM-based SQL generation.

        Args:
            action: The structured action to execute (dict or Action object)

        Returns:
            Dictionary with execution result
        """
        print("\n===== SQLCODER DATABASE EXECUTION LAYER =====")
        print(f"Executing action: {action}")

        # Handle both dict and Action object
        resource = action["resource"] if isinstance(action, dict) else action.resource
        if resource is None:
            print("ERROR: No resource specified in action")
            return {"error": "No resource specified"}

        # Get fields from action (handle both dict and object)
        intent = action["intent"] if isinstance(action, dict) else action.intent
        filters = action["filters"] if isinstance(action, dict) else action.filters
        data = action["data"] if isinstance(action, dict) else action.data

        # Generate SQL from natural language using SQLCoder
        sql = generate_sql_from_nl(intent, resource, filters, data)

        if not sql:
            print("ERROR: Failed to generate SQL query")
            return {"error": "Failed to generate SQL query"}

        print(f"Generated SQL: {sql}")

        try:
            cursor.execute(sql)
            conn.commit()

            # Determine response based on SQL type
            sql_upper = sql.strip().upper()
            if sql_upper.startswith("SELECT"):
                columns = [description[0] for description in cursor.description]
                results = [dict(zip(columns, row)) for row in cursor.fetchall()]
                print(f"Query returned {len(results)} results")
                return {"status": "success", "data": results}
            else:
                rows_affected = cursor.rowcount
                print(f"Query affected {rows_affected} rows")
                return {
                    "status": "success",
                    "message": f"Executed in {resource}",
                    "rows_affected": rows_affected,
                }
        except Exception as e:
            print(f"ERROR executing SQL: {e}")
            return {"error": str(e)}


# Create a singleton executor instance
_executor = SQLCoderExecutor()


def execute(action: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
    """Execute action using LLM-based SQL generation.

    Delegates to the SQLCoderExecutor instance.

    Args:
        action: The structured action to execute (dict or Action object)

    Returns:
        Dictionary with execution result
    """
    return _executor.execute(action)