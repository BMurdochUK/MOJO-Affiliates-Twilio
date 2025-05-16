import sqlite3
import pandas as pd
import os
import re

def clean_phone_number(phone_number):
    """
    Process a phone number to standardize its format for matching
    """
    if not isinstance(phone_number, str):
        return str(phone_number) if phone_number else None
        
    # Strip parentheses, plus signs, and spaces for processing
    clean_number = re.sub(r'[\(\)\+\s\*]', '', phone_number.strip())
    
    return clean_number

def update_buyer_usernames(csv_path, db_path='affiliates.db', delimiter=','):
    """Update buyer usernames in database based on phone numbers from CSV"""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return False
    
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at {db_path}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Read CSV file using pandas
        df = pd.read_csv(csv_path, delimiter=delimiter)
        
        # Exact column names from the CSV file
        phone_col = 'Phone #'
        buyer_col = 'Buyer Username'
        
        if phone_col not in df.columns or buyer_col not in df.columns:
            print(f"Error: Columns '{phone_col}' or '{buyer_col}' not found in CSV")
            print(f"Available columns: {df.columns.tolist()}")
            return False
            
        print(f"Using columns: Phone: '{phone_col}', Buyer Username: '{buyer_col}'")
        
        # Create a mapping of clean phone numbers to buyer usernames
        phone_to_username = {}
        for _, row in df.iterrows():
            phone = row[phone_col]
            username = row[buyer_col]
            
            if pd.isna(phone) or pd.isna(username) or not username:
                continue
                
            clean_phone = clean_phone_number(phone)
            if clean_phone:
                phone_to_username[clean_phone] = username
        
        print(f"Found {len(phone_to_username)} phone number to username mappings in CSV")
        
        # Update database records
        records_updated = 0
        records_skipped = 0
        
        # Get all records from database
        cursor.execute("SELECT id, raw_phone_number, buyer_username FROM orders")
        db_records = cursor.fetchall()
        
        for record_id, phone, current_username in db_records:
            if not phone:
                continue
                
            clean_phone = clean_phone_number(phone)
            if clean_phone in phone_to_username:
                new_username = phone_to_username[clean_phone]
                
                # Skip if username is already set correctly
                if current_username == new_username:
                    records_skipped += 1
                    continue
                    
                # Update the record
                cursor.execute(
                    "UPDATE orders SET buyer_username = ? WHERE id = ?",
                    (new_username, record_id)
                )
                records_updated += 1
                
                # Print progress
                if records_updated % 10 == 0:
                    print(f"Updated {records_updated} records...", end='\r')
        
        # Commit changes
        conn.commit()
        
        print(f"\nUpdate complete!")
        print(f"  - {records_updated} records updated with buyer usernames")
        print(f"  - {records_skipped} records already had correct usernames")
        print(f"  - {len(db_records) - records_updated - records_skipped} records had no matching phone in CSV")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error updating data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

if __name__ == "__main__":
    update_buyer_usernames('to-import.csv') 