"""
Database utility functions for CLI and web interface
"""
import sqlite3
import re
import datetime

def get_db_connection(db_path):
    """
    Create a connection to the SQLite database
    
    Args:
        db_path (str): Path to SQLite database file
        
    Returns:
        sqlite3.Connection: Database connection
    """
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

def clean_phone_number(phone_number):
    """
    Process a phone number:
    1. Check if it's obfuscated (contains *)
    2. Strip parentheses and + for sending
    3. Format for storage/sending
    
    Args:
        phone_number (str): Phone number to process
        
    Returns:
        tuple: (processed_number, raw_number, is_valid_for_whatsapp)
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

def get_recipients_from_db(db_path, filter_conditions=None, order_status=None, order_by=None, limit=None, force=False):
    """
    Get recipients from the database
    
    Args:
        db_path (str): Path to SQLite database file
        filter_conditions (str): Custom SQL WHERE clause
        order_status (str): Filter by order status (e.g., 'SHIPPED', 'DELIVERED')
        order_by (str): SQL ORDER BY clause
        limit (int): Maximum number of recipients to return
        force (bool): If True, include previously messaged recipients
    
    Returns:
        list: List of dicts with recipient information
    """
    recipients = []
    
    try:
        # Connect to database
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Build query
        query = """
            SELECT 
                o.id, o.order_id, o.phone_number, o.raw_phone_number, 
                o.order_status, o.recipient, o.product_name, o.last_messaged
            FROM 
                orders o
            WHERE 
                o.is_valid_for_whatsapp = 1
        """
        
        # Unless force flag is True, exclude recipients who have been messaged before
        if not force:
            query += " AND (o.last_messaged IS NULL OR o.last_messaged = '')"
        
        params = []
        
        # Add order status filter if provided
        if order_status:
            query += " AND o.order_status = ?"
            params.append(order_status)
        
        # Add custom filter conditions if provided
        if filter_conditions:
            query += f" AND {filter_conditions}"
        
        # Add ordering
        if order_by:
            query += f" ORDER BY {order_by}"
        else:
            query += " ORDER BY o.last_updated DESC"
        
        # Add limit
        if limit:
            query += " LIMIT ?"
            params.append(limit)
        
        # Execute query
        cursor.execute(query, params)
        
        # Get results
        unique_phone_numbers = set()  # Track unique phone numbers
        
        for row in cursor.fetchall():
            # Convert row to dict
            recipient = dict(row)
            
            # Skip this record if we've already seen this phone number
            if recipient['phone_number'] in unique_phone_numbers:
                continue
                
            # Add this phone number to our set of seen numbers
            unique_phone_numbers.add(recipient['phone_number'])
            
            # Format phone number for WhatsApp
            if recipient['phone_number'] and not recipient['phone_number'].startswith('whatsapp:'):
                recipient['formatted_number'] = f"whatsapp:{recipient['phone_number']}"
            else:
                recipient['formatted_number'] = recipient['phone_number']
                
            recipients.append(recipient)
        
        conn.close()
        return recipients
        
    except Exception as e:
        print(f"Error getting recipients from database: {e}")
        return []

def log_message_to_db(db_path, order_id, phone_number, template_id, message_sid, status, error_message=None):
    """
    Log message details to the database
    
    Args:
        db_path (str): Path to SQLite database file
        order_id (str): Order ID
        phone_number (str): Recipient's phone number
        template_id (str): Template ID used
        message_sid (str): Twilio message SID
        status (str): Message status
        error_message (str): Error message if any
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        sent_time = datetime.datetime.now().isoformat()
        
        cursor.execute('''
            INSERT INTO message_log 
            (order_id, phone_number, message_template_id, message_sid, status, sent_time, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (order_id, phone_number, template_id, message_sid, status, sent_time, error_message))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error logging message to database: {e}")

def update_last_messaged(db_path, phone_number):
    """
    Update the last_messaged timestamp for a phone number
    
    Args:
        db_path (str): Path to SQLite database file
        phone_number (str): Phone number to update
    """
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Extract just the phone number portion without 'whatsapp:' prefix
        cleaned_number = phone_number.replace("whatsapp:", "") if phone_number.startswith("whatsapp:") else phone_number
        
        # Update all records with this phone number
        cursor.execute("""
            UPDATE orders 
            SET last_messaged = ? 
            WHERE phone_number = ?
        """, (datetime.datetime.now().isoformat(), cleaned_number))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error updating last_messaged timestamp: {e}") 