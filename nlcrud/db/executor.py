"""Rule-based database executor.

Executes CRUD actions using predefined SQL generation rules.
All database operations are encapsulated in the RuleBasedExecutor class.
"""
import os
import sqlite3
from typing import Any, Dict, Union

from nlcrud.db.schema import SCHEMA
from nlcrud.db.interface import DatabaseExecutor


def initialize_database(db_path: str = "db/db.sqlite") -> None:
    """Initialize the database by creating tables based on the schema.

    Args:
        db_path: Path to SQLite database file
    """
    # Ensure the db directory exists
    db_dir = os.path.dirname(db_path) or "db"
    os.makedirs(db_dir, exist_ok=True)

    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

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
    conn.close()


class RuleBasedExecutor(DatabaseExecutor):
    """Rule-based database executor.

    Executes CRUD actions using predefined SQL generation rules.
    Each executor instance owns its own database connection.
    """

    def __init__(self, db_path: str = "db/db.sqlite") -> None:
        """Initialize executor with database path.

        Args:
            db_path: Path to SQLite database file
        """
        # Ensure the db directory exists
        db_dir = os.path.dirname(db_path) or "db"
        os.makedirs(db_dir, exist_ok=True)

        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.cursor = self.conn.cursor()

    @staticmethod
    def _get_action_attr(action: Union[Dict[str, Any], Any], attr: str) -> Any:
        """Get attribute from action (works with dict or Action object).

        Args:
            action: Action dict or Action object
            attr: Attribute name

        Returns:
            Attribute value
        """
        if isinstance(action, dict):
            return action[attr]
        return getattr(action, attr)

    def execute(self, action: Union[Dict[str, Any], Any]) -> Dict[str, Any]:
        """Execute a structured CRUD action against the database.

        Args:
            action: The structured action to execute (dict or Action object)

        Returns:
            Dictionary with the result of the execution
        """
        print("\n===== DATABASE EXECUTION LAYER =====")
        print(f"Executing action: {action}")

        resource = self._get_action_attr(action, "resource")
        if resource is None:
            print("ERROR: No resource specified in action")
            return {"error": "No resource specified"}

        table = SCHEMA[resource]["table"]
        print(f"Using table: {table}")

        intent = self._get_action_attr(action, "intent")
        filters = self._get_action_attr(action, "filters")
        data = self._get_action_attr(action, "data")

        # Dispatch to appropriate handler based on intent
        dispatch = {
            "READ": lambda: self._handle_read(table, filters),
            "CREATE": lambda: self._handle_create(table, data),
            "UPDATE": lambda: self._handle_update(table, filters, data),
            "DELETE": lambda: self._handle_delete(table, filters),
            "SEARCH": lambda: self._handle_search(table, data),
        }

        handler = dispatch.get(intent)
        if not handler:
            print(f"ERROR: Unknown intent: {intent}")
            return {"error": f"Unknown intent: {intent}"}

        return handler()

    def _handle_read(self, table: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle READ operations.

        Args:
            table: Table name to read from
            filters: WHERE conditions (dict of field:value pairs)

        Returns:
            Dictionary with status and results
        """
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

        self.cursor.execute(sql, params)
        columns = [description[0] for description in self.cursor.description]
        results = []

        for row in self.cursor.fetchall():
            results.append(dict(zip(columns, row)))

        print(f"Query returned {len(results)} results")
        print(f"Result data: {results}")

        return {"status": "success", "data": results}

    def _handle_create(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle CREATE operations.

        Args:
            table: Table name to insert into
            data: Data to insert (dict of field:value pairs)

        Returns:
            Dictionary with status, message, and inserted ID
        """
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

        self.cursor.execute(sql, values)
        self.conn.commit()

        new_id = self.cursor.lastrowid
        print(f"Created new record with ID: {new_id}")

        return {"status": "success", "message": f"Created in {table}", "id": new_id}

    def _handle_update(
        self, table: str, filters: Dict[str, Any], data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Handle UPDATE operations.

        Args:
            table: Table name to update
            filters: WHERE conditions (dict of field:value pairs)
            data: Data to update (dict of field:value pairs)

        Returns:
            Dictionary with status, message, and number of rows affected
        """
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

        self.cursor.execute(sql, params)
        self.conn.commit()

        rows_affected = self.cursor.rowcount
        print(f"Updated {rows_affected} rows")

        return {
            "status": "success",
            "message": f"Updated in {table}",
            "rows_affected": rows_affected,
        }

    def _handle_delete(self, table: str, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Handle DELETE operations.

        Args:
            table: Table name to delete from
            filters: WHERE conditions (dict of field:value pairs)

        Returns:
            Dictionary with status, message, and number of rows affected
        """
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

        self.cursor.execute(sql, params)
        self.conn.commit()

        rows_affected = self.cursor.rowcount
        print(f"Deleted {rows_affected} rows")

        return {
            "status": "success",
            "message": f"Deleted from {table}",
            "rows_affected": rows_affected,
        }

    def _handle_search(self, table: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SEARCH operations.

        Args:
            table: Table name to search
            data: Search criteria (dict of field:value pairs)
                  Numbers/floats use exact match (=)
                  Strings use pattern match (LIKE)

        Returns:
            Dictionary with status and search results
        """
        print("\n----- SEARCH Operation Details -----")

        sql = f"SELECT * FROM {table} WHERE "
        conditions = []
        params = []

        for key, value in data.items():
            if isinstance(value, (int, float)):
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

        self.cursor.execute(sql, params)
        columns = [description[0] for description in self.cursor.description]
        results = []

        for row in self.cursor.fetchall():
            results.append(dict(zip(columns, row)))

        print(f"Search returned {len(results)} results")
        print(f"Result data: {results}")

        return {"status": "success", "data": results}

