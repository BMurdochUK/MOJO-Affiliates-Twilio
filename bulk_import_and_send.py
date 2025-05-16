#!/usr/bin/env python3
import sqlite3
import datetime
import re
import os
import sys
import argparse
from send_message import send_bulk_messages, ensure_testing_db_exists

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

def import_numbers_to_db(phone_numbers_file, db_path='affiliates.db'):
    """Import phone numbers from a file into the SQLite database"""
    if not os.path.exists(phone_numbers_file):
        print(f"Error: Phone numbers file not found at {phone_numbers_file}")
        return False
    
    # Connect to the database
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Read the phone numbers file
    with open(phone_numbers_file, 'r') as f:
        numbers = f.readlines()
    
    # Process and deduplicate numbers
    unique_numbers = set()
    unique_valid_numbers = 0
    invalid_numbers = 0
    
    for number in numbers:
        number = number.strip()
        if not number:
            continue
        
        # Process the number
        clean_number, raw_number, is_valid = clean_phone_number(number)
        
        # Skip if we've already seen this number
        if raw_number in unique_numbers:
            continue
        
        unique_numbers.add(raw_number)
        
        if is_valid:
            # Insert the record with a unique order_id based on the cleaned number
            order_id = f"UK{clean_number[-8:]}"
            
            try:
                cursor.execute("""
                    INSERT INTO orders 
                    (order_id, order_status, recipient, product_name, raw_phone_number, phone_number, is_valid_for_whatsapp, last_updated)
                    VALUES (?, 'ACTIVE', 'UK Customer', 'MOJO Import', ?, ?, ?, ?)
                """, (order_id, raw_number, clean_number, is_valid, datetime.datetime.now().isoformat()))
                unique_valid_numbers += 1
            except sqlite3.IntegrityError:
                # If the order_id already exists, use a timestamped version
                order_id = f"UK{clean_number[-8:]}{int(datetime.datetime.now().timestamp())}"
                cursor.execute("""
                    INSERT INTO orders 
                    (order_id, order_status, recipient, product_name, raw_phone_number, phone_number, is_valid_for_whatsapp, last_updated)
                    VALUES (?, 'ACTIVE', 'UK Customer', 'MOJO Import', ?, ?, ?, ?)
                """, (order_id, raw_number, clean_number, is_valid, datetime.datetime.now().isoformat()))
                unique_valid_numbers += 1
        else:
            invalid_numbers += 1
    
    # Commit changes
    conn.commit()
    conn.close()
    
    print(f"Import summary:")
    print(f"  - Total unique numbers processed: {len(unique_numbers)}")
    print(f"  - Valid numbers imported: {unique_valid_numbers}")
    print(f"  - Invalid numbers (obfuscated): {invalid_numbers}")
    
    return True

def parse_arguments():
    parser = argparse.ArgumentParser(description="Import phone numbers and send WhatsApp messages")
    
    parser.add_argument("--phone-file", type=str, default="temp/phone_numbers.txt",
                        help="File containing phone numbers (one per line)")
    
    parser.add_argument("--db", type=str, default="affiliates.db",
                        help="Database file path")
    
    parser.add_argument("--live", action="store_true",
                        help="Send actual messages (without this flag, dry-run is the default)")
    
    parser.add_argument("--delay", type=float, default=1.0,
                        help="Delay between messages in seconds")
    
    parser.add_argument("--status", type=str, default="ACTIVE",
                        help="Filter by order status")
    
    parser.add_argument("--force", action="store_true",
                        help="Force sending to all recipients, including those previously messaged")
    
    parser.add_argument("--import-only", action="store_true",
                        help="Only import numbers, don't send messages")
    
    parser.add_argument("--testing-mode", action="store_true",
                        help="Use testing database with only the test phone number")
    
    return parser.parse_args()

def main():
    # Parse command line arguments
    args = parse_arguments()
    
    # Determine database path
    db_path = args.db
    if args.testing_mode:
        db_path = "testing.db"
        ensure_testing_db_exists(db_path)
        print("\n⚠️  TESTING MODE ENABLED - Using test database with single test number ⚠️\n")
    
    # Determine if we're in dry run mode (default) or live mode
    dry_run = not args.live
    if dry_run:
        print("DRY RUN MODE: No actual messages will be sent (use --live to send real messages)")
    else:
        print("\n⚠️  LIVE MODE ENABLED - ACTUAL MESSAGES WILL BE SENT ⚠️\n")
        input("Press ENTER to continue or CTRL+C to cancel...")
    
    # Import numbers to database (unless in testing mode)
    if not args.testing_mode:
        if not import_numbers_to_db(args.phone_file, db_path):
            print("Failed to import numbers. Exiting.")
            sys.exit(1)
    else:
        print("Skipping import in testing mode - using predefined test number")
    
    # Exit if import-only mode
    if args.import_only:
        print("\nImport-only mode selected. Exiting without sending messages.")
        return
    
    # Send messages to all valid recipients
    print("\nSending messages to all valid recipients...")
    
    # Display warning if force flag is set
    if args.force and not dry_run:
        print("\n⚠️  WARNING: FORCE FLAG ENABLED - Will send to ALL recipients including previously messaged ones ⚠️\n")
        input("Press ENTER to continue or CTRL+C to cancel...")
    
    # Use the send_message functionality with explicit DB path
    send_bulk_messages(
        filter_conditions=None,  # Send to all valid numbers
        order_status=args.status,   # Only send to ACTIVE status
        dry_run=dry_run,
        delay=args.delay,               # 1 second delay between messages
        content_variables={"senderName": "MOJO Health Supplements"},
        db_path=db_path,          # Pass the database path explicitly
        force=args.force          # Pass the force flag
    )

if __name__ == "__main__":
    main() 