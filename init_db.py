import sqlite3
import os

# Ensure the db directory exists
os.makedirs("db", exist_ok=True)

# Connect to the SQLite database
conn = sqlite3.connect("db/db.sqlite")
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

# Insert sample users
sample_users = [
    ("John Doe", "john@example.com", 30),
    ("Jane Smith", "jane@example.com", 25),
    ("Bob Johnson", "bob@example.com", 40),
    ("Alice Brown", "alice@example.com", 35)
]

cursor.executemany(
    "INSERT INTO users (name, email, age) VALUES (?, ?, ?)",
    sample_users
)

# Insert sample orders
sample_orders = [
    (1, 100.50),
    (1, 200.75),
    (2, 50.25),
    (3, 300.00)
]

cursor.executemany(
    "INSERT INTO orders (user_id, amount) VALUES (?, ?)",
    sample_orders
)

# Commit changes and close connection
conn.commit()
conn.close()

print("Database initialized with sample data.")