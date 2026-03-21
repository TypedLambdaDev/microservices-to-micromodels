"""Database initialization script.

Initializes the database schema and populates with sample data.
"""
import sqlite3
import os

from nlcrud.db.executor import initialize_database
from nlcrud.logger import get_logger

logger = get_logger("db.init")


def seed_sample_data(db_path: str = "db/db.sqlite") -> None:
    """Insert sample data into the database.

    Args:
        db_path: Path to SQLite database
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Insert sample users
    sample_users = [
        ("John Doe", "john@example.com", 30),
        ("Jane Smith", "jane@example.com", 25),
        ("Bob Johnson", "bob@example.com", 40),
        ("Alice Brown", "alice@example.com", 35),
    ]

    cursor.executemany(
        "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
        sample_users,
    )

    # Insert sample orders
    sample_orders = [
        (1, 100.50),
        (1, 200.75),
        (2, 50.25),
        (3, 300.00),
    ]

    cursor.executemany(
        "INSERT INTO orders (user_id, amount) VALUES (?, ?)",
        sample_orders,
    )

    conn.commit()
    conn.close()


def init_db(db_path: str = "db/db.sqlite", seed: bool = True) -> None:
    """Initialize database with schema and optional sample data.

    Args:
        db_path: Path to SQLite database
        seed: If True, populate with sample data
    """
    # Ensure the db directory exists
    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    # Create tables
    initialize_database()

    # Optionally insert sample data
    if seed:
        seed_sample_data(db_path)


if __name__ == "__main__":
    init_db()
    logger.info("Database initialized with sample data.")