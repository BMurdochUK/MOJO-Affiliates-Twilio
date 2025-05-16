import sqlite3
import pandas as pd
import os
import re
import sys
import datetime

def clean_phone_number(phone_number):
    """
    Process a phone number:
    1. Check if it's obfuscated (contains *)
    2. Strip parentheses and + for sending
    3. Format for storage/sending
    
    Returns a tuple of (processed_number, raw_number, is_valid_for_whatsapp)
    """
    if not isinstance(phone_number, str):
        return None, str(phone_number) if phone_number else None, False
        
    # Store the original format
    raw_number = phone_number.strip()
    
    # Check if number is obfuscated (contains asterisks)
    is_obfuscated = '*' in raw_number
    
    # Strip parentheses, plus signs, and spaces for processing
    clean_number = re.sub(r'[\(\)\+\s]', '', raw_number)
    
    # A valid number should not be obfuscated and should contain only digits
    is_valid = not is_obfuscated and bool(re.match(r'^\d+$', clean_number))
    
    return clean_number if is_valid else None, raw_number, is_valid

def debug_csv_import(csv_path, delimiter=','):
    """Debug the CSV import process without modifying the database"""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return False
    
    try:
        # Read CSV file using pandas - handle various CSV formats
        try:
            df = pd.read_csv(csv_path, delimiter=delimiter)
            print(f"Successfully read CSV with delimiter '{delimiter}'")
        except Exception as e:
            print(f"Error reading CSV with delimiter '{delimiter}': {e}")
            print("Trying to auto-detect delimiter...")
            with open(csv_path, 'r', encoding='utf-8') as f:
                first_line = f.readline()
                potential_delimiters = [',', ';', '\t', '|']
                max_count = 0
                best_delimiter = delimiter
                
                for d in potential_delimiters:
                    count = first_line.count(d)
                    if count > max_count:
                        max_count = count
                        best_delimiter = d
                
            print(f"Using delimiter: '{best_delimiter}'")
            df = pd.read_csv(csv_path, delimiter=best_delimiter)
        
        # Print DataFrame information
        print(f"\nCSV file info:")
        print(f"Total rows: {len(df)}")
        print(f"Columns: {list(df.columns)}")
        
        # Check for key columns
        important_columns = ['Order ID', 'Buyer Username', 'Phone #']
        for col in important_columns:
            if col in df.columns:
                print(f"✅ Column found: '{col}'")
                # Check for null values
                null_count = df[col].isnull().sum()
                print(f"   - Null values: {null_count}")
                # Check for empty strings
                if df[col].dtype == 'object':
                    empty_count = (df[col] == '').sum()
                    print(f"   - Empty strings: {empty_count}")
            else:
                print(f"❌ Column NOT found: '{col}'")
                # Look for similar columns
                similar_cols = [c for c in df.columns if col.lower() in c.lower()]
                if similar_cols:
                    print(f"   - Similar columns: {similar_cols}")
        
        # Show first 5 rows as a sample
        print("\nSample data (first 5 rows):")
        print(df.head().to_string())
        
        # Test phone number cleaning on a sample
        if 'Phone #' in df.columns:
            print("\nPhone number processing test (5 samples):")
            sample_phones = df['Phone #'].dropna().head(5)
            for phone in sample_phones:
                clean, raw, valid = clean_phone_number(phone)
                print(f"Original: '{phone}' → Clean: '{clean}', Raw: '{raw}', Valid: {valid}")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_import.py <csv_file> [delimiter]")
        sys.exit(1)
        
    csv_file = sys.argv[1]
    delimiter = sys.argv[2] if len(sys.argv) > 2 else ','
    
    debug_csv_import(csv_file, delimiter) 