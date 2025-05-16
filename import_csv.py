import sqlite3
import pandas as pd
import os
import re
import sys
import datetime
import argparse
from create_database import create_database

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

def import_csv_to_db(csv_path, db_path='affiliates.db', delimiter=','):
    """Import data from CSV into SQLite database"""
    if not os.path.exists(csv_path):
        print(f"Error: CSV file not found at {csv_path}")
        return False
    
    # Ensure database exists
    if not os.path.exists(db_path):
        create_database(db_path)
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # Read CSV file using pandas - handle various CSV formats
        try:
            df = pd.read_csv(csv_path, delimiter=delimiter)
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
        
        # Normalize column names (lowercase, replace spaces with underscores)
        df.columns = [col.lower().replace(' ', '_').replace('#', 'number').replace('/', '_') for col in df.columns]
        
        # Map CSV columns to database columns - adjust as needed based on actual CSV columns
        # This mapping assumes CSV headers match the schema closely
        column_mapping = {
            'order_id': 'order_id',
            'order_status': 'order_status',
            'order_substatus': 'order_substatus',
            'cancelation_return_type': 'cancellation_return_type',
            'normal_or_pre-order': 'normal_or_preorder',
            'sku_id': 'sku_id',
            'seller_sku': 'seller_sku',
            'product_name': 'product_name',
            'variation': 'variation',
            'quantity': 'quantity',
            'sku_quantity_of_return': 'sku_quantity_return',
            'sku_unit_original_price': 'sku_unit_original_price',
            'sku_subtotal_before_discount': 'sku_subtotal_before_discount',
            'sku_platform_discount': 'sku_platform_discount',
            'sku_seller_discount': 'sku_seller_discount',
            'sku_subtotal_after_discount': 'sku_subtotal_after_discount',
            'shipping_fee_after_discount': 'shipping_fee_after_discount',
            'original_shipping_fee': 'original_shipping_fee',
            'shipping_fee_seller_discount': 'shipping_fee_seller_discount',
            'shipping_fee_platform_discount': 'shipping_fee_platform_discount',
            'taxes': 'taxes',
            'order_amount': 'order_amount',
            'order_refund_amount': 'order_refund_amount',
            'created_time': 'created_time',
            'paid_time': 'paid_time',
            'rth_time': 'rth_time',
            'shipped_time': 'shipped_time',
            'delivered_time': 'delivered_time',
            'cancelled_time': 'cancelled_time',
            'cancel_by': 'cancel_by',
            'cancel_reason': 'cancel_reason',
            'fulfillment_type': 'fulfillment_type',
            'warehouse_name': 'warehouse_name',
            'tracking_id': 'tracking_id',
            'delivery_option': 'delivery_option',
            'shipping_provider_name': 'shipping_provider_name',
            'buyer_message': 'buyer_message',
            'buyer_username': 'buyer_username',
            'recipient': 'recipient',
            'phone_number': 'raw_phone_number',  # Will use raw value first, then process
            'zipcode': 'zipcode',
            'state': 'state',
            'country': 'country',
            'county': 'county',
            'districts': 'districts',
            'street_name': 'street_name',
            'house_name_or_number': 'house_number',
            'delivery_instruction': 'delivery_instruction',
            'payment_method': 'payment_method',
            'weight(kg)': 'weight',
            'product_category': 'product_category',
            'package_id': 'package_id',
            'seller_note': 'seller_note',
            'shipping_information': 'shipping_information',
            'checked_status': 'checked_status',
            'checked_marked_by': 'checked_marked_by'
        }
        
        # Handle missing columns in the CSV
        columns_to_use = {}
        for csv_col, db_col in column_mapping.items():
            if csv_col in df.columns:
                columns_to_use[csv_col] = db_col
        
        # Create a timestamp for the update
        current_time = datetime.datetime.now().isoformat()
        
        # Process each row in the dataframe
        records_processed = 0
        records_updated = 0
        records_inserted = 0
        
        for _, row in df.iterrows():
            # Build data dictionary
            data = {}
            for csv_col, db_col in columns_to_use.items():
                data[db_col] = row[csv_col]
            
            # Add last_updated timestamp
            data['last_updated'] = current_time
            
            # Process phone number
            if 'raw_phone_number' in data:
                phone_number, raw_number, is_valid = clean_phone_number(data['raw_phone_number'])
                data['phone_number'] = phone_number
                data['raw_phone_number'] = raw_number
                data['is_valid_for_whatsapp'] = is_valid
            
            # Check if record exists (by order_id and sku_id)
            cursor.execute(
                "SELECT id FROM orders WHERE order_id = ? AND sku_id = ?",
                (data.get('order_id'), data.get('sku_id'))
            )
            existing_record = cursor.fetchone()
            
            if existing_record:
                # Update existing record
                update_fields = [f"{k} = ?" for k in data.keys()]
                update_values = list(data.values())
                update_sql = f"UPDATE orders SET {', '.join(update_fields)} WHERE order_id = ? AND sku_id = ?"
                cursor.execute(update_sql, update_values + [data.get('order_id'), data.get('sku_id')])
                records_updated += 1
            else:
                # Insert new record
                placeholders = ", ".join(["?"] * len(data))
                insert_sql = f"INSERT INTO orders ({', '.join(data.keys())}) VALUES ({placeholders})"
                cursor.execute(insert_sql, list(data.values()))
                records_inserted += 1
                
            records_processed += 1
            
            # Commit every 100 records to avoid large transactions
            if records_processed % 100 == 0:
                conn.commit()
                print(f"Processed {records_processed} records...", end='\r')
        
        # Final commit
        conn.commit()
        
        print(f"\nImport complete: {records_processed} records processed")
        print(f"  - {records_inserted} new records inserted")
        print(f"  - {records_updated} existing records updated")
        
        return True
        
    except Exception as e:
        conn.rollback()
        print(f"Error importing data: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        conn.close()

def parse_arguments():
    parser = argparse.ArgumentParser(description='Import CSV data into SQLite database')
    parser.add_argument('csv_file', help='Path to the CSV file to import')
    parser.add_argument('--db', default='affiliates.db', help='Path to the SQLite database (default: affiliates.db)')
    parser.add_argument('--delimiter', default=',', help='CSV delimiter (default: ,)')
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_arguments()
    import_csv_to_db(args.csv_file, args.db, args.delimiter) 