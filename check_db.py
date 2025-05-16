import sqlite3
import os

# Check if the database exists
if not os.path.exists('affiliates.db'):
    print("Database file doesn't exist!")
    exit(1)

# Connect to database
conn = sqlite3.connect('affiliates.db')
cursor = conn.cursor()

# Get list of tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
tables = cursor.fetchall()
print("Tables in database:", [table[0] for table in tables])

# If there are tables, get schema for each
for table in tables:
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    print(f"\nColumns in {table[0]}:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")

conn.close()