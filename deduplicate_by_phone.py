import sqlite3
import pandas as pd
import os
import re
import datetime

def deduplicate_by_phone(db_path='affiliates.db'):
    """Deduplicate records in the database by phone number, keeping the most recent record"""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # First, let's check how many records and unique phone numbers we have
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_records = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT raw_phone_number) FROM orders")
        unique_phones = cursor.fetchone()[0]
        
        print(f"Starting with {total_records} total records and {unique_phones} unique phone numbers")
        
        # Get the most recent record for each phone number
        cursor.execute("""
            CREATE TEMPORARY TABLE latest_records AS
            SELECT MAX(id) as latest_id
            FROM orders
            GROUP BY raw_phone_number
        """)
        
        # Count records to be deleted
        cursor.execute("""
            SELECT COUNT(*)
            FROM orders
            WHERE id NOT IN (SELECT latest_id FROM latest_records)
        """)
        to_delete = cursor.fetchone()[0]
        
        print(f"Will delete {to_delete} duplicate records, keeping {unique_phones} unique records")
        
        # Confirm with user
        confirmation = input("Proceed with deduplication? (y/n): ")
        if confirmation.lower() != 'y':
            print("Operation cancelled")
            return False
        
        # Delete duplicate records
        cursor.execute("""
            DELETE FROM orders
            WHERE id NOT IN (SELECT latest_id FROM latest_records)
        """)
        
        # Commit changes
        conn.commit()
        
        # Verify results
        cursor.execute("SELECT COUNT(*) FROM orders")
        new_total = cursor.fetchone()[0]
        
        print(f"Deduplication complete! Database now has {new_total} records")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error during deduplication: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    deduplicate_by_phone() 