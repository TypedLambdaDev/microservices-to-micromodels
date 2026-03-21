"""
Simple script to test Ollama directly without going through the API.
"""
import os
import requests
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Ollama configuration
OLLAMA_URL = os.environ.get("OLLAMA_URL", "http://localhost:11434/api/generate")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "sqlcoder")

def call_ollama(prompt):
    """
    Call Ollama to generate SQL from natural language.
    
    Args:
        prompt (str): The prompt to send to Ollama
        
    Returns:
        str: The generated text
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
        print(f"Calling Ollama with model: {OLLAMA_MODEL}")
        response = requests.post(OLLAMA_URL, headers=headers, json=payload)
        response.raise_for_status()
        
        # Extract response
        response_json = response.json()
        generated_text = response_json.get("response", "")
        
        return generated_text
    except Exception as e:
        print(f"Error calling Ollama: {str(e)}")
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
            sql = sql.strip()
            
            # If SQL still contains non-SQL text, try to clean it further
            if not re.match(r"^(?:SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER)\b", sql, re.IGNORECASE):
                continue
                
            return sql
    
    # Generate SQL based on the natural language query
    print("WARNING: Could not extract valid SQL from LLM response.")
    return None

def generate_fallback_sql(query):
    """
    Generate a simple SQL query based on the natural language query.
    
    Args:
        query (str): The natural language query
        
    Returns:
        str: A simple SQL query
    """
    import re
    query_lower = query.lower()
    
    if "show" in query_lower or "find" in query_lower or "get" in query_lower:
        if "user" in query_lower:
            if "older than" in query_lower or "age" in query_lower:
                age_match = re.search(r"(\d+)", query_lower)
                age = age_match.group(1) if age_match else "30"
                return f"SELECT * FROM users WHERE age > {age}"
            else:
                return "SELECT * FROM users"
        elif "order" in query_lower:
            return "SELECT * FROM orders"
    elif "create" in query_lower or "add" in query_lower or "new" in query_lower:
        if "user" in query_lower:
            name_match = re.search(r"named\s+(\w+)", query_lower)
            name = name_match.group(1) if name_match else "John"
            
            email_match = re.search(r"email\s+(\S+@\S+)", query_lower)
            email = email_match.group(1) if email_match else "john@example.com"
            
            age_match = re.search(r"age\s+(\d+)", query_lower)
            age = age_match.group(1) if age_match else "25"
            
            return f"INSERT INTO users (name, email, age) VALUES ('{name}', '{email}', {age})"
    elif "update" in query_lower:
        if "user" in query_lower:
            id_match = re.search(r"id\s+(\d+)", query_lower)
            id = id_match.group(1) if id_match else "1"
            
            age_match = re.search(r"age\s+(\d+)", query_lower)
            age = age_match.group(1) if age_match else "35"
            
            return f"UPDATE users SET age = {age} WHERE id = {id}"
    elif "delete" in query_lower:
        if "user" in query_lower:
            id_match = re.search(r"id\s+(\d+)", query_lower)
            id = id_match.group(1) if id_match else "1"
            
            return f"DELETE FROM users WHERE id = {id}"
    
    return None

def main():
    # Database schema description
    schema_description = """
    Database schema:
    Table: users
    Fields: id, name, email, age

    Table: orders
    Fields: id, user_id, amount
    """
    
    # Test queries
    test_queries = [
        "Show me all users",
        "Find users who are older than 30",
        "Create a new user named John with email john@example.com and age 25",
        "Update user with id 1 to have age 35",
        "Delete user with id 2"
    ]
    
    for query in test_queries:
        print("\n" + "="*50)
        print(f"Natural language query: {query}")
        
        # Create prompt
        prompt = f"""
        {schema_description}
        
        Task: Generate a SQL query for the following operation:
        {query}
        
        The query should be compatible with SQLite.
        """
        
        # Call Ollama
        generated_text = call_ollama(prompt)
        
        if generated_text:
            print("\nGenerated text:")
            print("-"*50)
            print(generated_text)
            print("-"*50)
            
            # Extract SQL
            sql_query = extract_sql_from_text(generated_text)
            
            # If extraction failed, use fallback
            if not sql_query:
                print("\nUsing fallback SQL generation")
                sql_query = generate_fallback_sql(query)
            
            print("\nFinal SQL query:")
            print("-"*50)
            print(sql_query)
            print("-"*50)
        else:
            print("Failed to generate text from Ollama")

if __name__ == "__main__":
    main()