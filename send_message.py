import os
import json
import time
import argparse
import datetime
import sqlite3
import pathlib
from twilio.rest import Client
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

# Configuration
CONFIG = {
    "templateId": "HXf8a6226ae9bc9dcd6bb8e9ee0120d5f5",
    "whatsappNumber": os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+15551234567"),
    "messagingServiceSid": os.environ.get("TWILIO_MESSAGING_SERVICE_SID"),
    "dbPath": os.environ.get("DB_PATH", "affiliates.db"),
    "delayBetweenMessages": 1  # seconds to wait between sends to avoid rate limits
}

# Initialize Twilio Client
account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
auth_token = os.environ.get("TWILIO_AUTH_TOKEN")

if not account_sid or not auth_token:
    print("Error: TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment variables or .env file.", flush=True)
    exit(1)

client = Client(account_sid, auth_token)

def send_message(options=None):
    if options is None:
        options = {}

    content_sid = options.get("content_sid", CONFIG["templateId"])
    content_variables = options.get("content_variables", {})
    from_ = options.get("from_", CONFIG["whatsappNumber"])
    to = options.get("to")
    messaging_service_sid = options.get("messaging_service_sid", CONFIG["messagingServiceSid"])
    order_id = options.get("order_id")

    if not to:
        print("Error: 'to' number is required.", flush=True)
        return None

    message_params = {
        "content_sid": content_sid,
        "content_variables": json.dumps(content_variables),
        "to": to
    }

    if messaging_service_sid:
        message_params["messaging_service_sid"] = messaging_service_sid
        if "from_" in options:
             message_params["from_"] = from_
    else:
        message_params["from_"] = from_

    try:
        message = client.messages.create(**message_params)
        print(f"Message sent successfully to {to}:", flush=True)
        print(f"  SID: {message.sid}", flush=True)
        print(f"  Status: {message.status}", flush=True)
        
        # Log message in database if order_id is provided
        if order_id and options.get("log_message", True):
            log_message_to_db(order_id, to, content_sid, message.sid, message.status)
            
            # Update last_messaged timestamp in orders table
            try:
                conn = sqlite3.connect(CONFIG["dbPath"])
                cursor = conn.cursor()
                
                # Extract just the phone number portion without 'whatsapp:' prefix
                cleaned_number = to.replace("whatsapp:", "") if to.startswith("whatsapp:") else to
                
                # Update all records with this phone number
                cursor.execute("""
                    UPDATE orders 
                    SET last_messaged = ? 
                    WHERE phone_number = ?
                """, (datetime.datetime.now().isoformat(), cleaned_number))
                
                conn.commit()
                conn.close()
            except Exception as e:
                print(f"Error updating last_messaged timestamp: {e}", flush=True)
            
        return message
    except Exception as e:
        print(f"Error sending message to {to}: {e}", flush=True)
        
        # Log error in database if order_id is provided
        if order_id and options.get("log_message", True):
            log_message_to_db(order_id, to, content_sid, None, "error", str(e))
            
        return None

def log_message_to_db(order_id, phone_number, template_id, message_sid, status, error_message=None):
    """Log message details to the database"""
    try:
        conn = sqlite3.connect(CONFIG["dbPath"])
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
        print(f"Error logging message to database: {e}", flush=True)

def get_recipients_from_db(filter_conditions=None, order_status=None, order_by=None, limit=None, force=False):
    """
    Get recipients from the database
    
    Args:
        filter_conditions: Custom SQL WHERE clause
        order_status: Filter by order status (e.g., 'SHIPPED', 'DELIVERED')
        order_by: SQL ORDER BY clause
        limit: Maximum number of recipients to return
        force: If True, include previously messaged recipients
    
    Returns:
        List of dicts with recipient information
    """
    recipients = []
    
    try:
        # Connect to database
        conn = sqlite3.connect(CONFIG["dbPath"])
        conn.row_factory = sqlite3.Row  # Return rows as dictionaries
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
        print(f"Loaded {len(recipients)} unique recipients from database", flush=True)
        return recipients
        
    except Exception as e:
        print(f"Error getting recipients from database: {e}", flush=True)
        return []

def send_bulk_messages(content_variables=None, recipients=None, filter_conditions=None, 
                      order_status=None, limit=None, dry_run=False, delay=None, order_id=None, db_path=None, force=False):
    """Send messages to multiple recipients from the database"""
    if content_variables is None:
        content_variables = {"senderName": "MOJO Health Supplements"}
    
    # Update database path if provided
    if db_path:
        original_db_path = CONFIG["dbPath"]
        CONFIG["dbPath"] = db_path
    
    if recipients is None:
        # Get recipients from database
        recipients = get_recipients_from_db(
            filter_conditions=filter_conditions,
            order_status=order_status,
            limit=limit,
            force=force  # Pass the force flag to include previously messaged recipients if True
        )
    
    # Restore original database path if it was changed
    if db_path:
        CONFIG["dbPath"] = original_db_path
    
    if not recipients:
        print("No recipients found. Please check your database and filter conditions.", flush=True)
        if not force:
            print("Note: By default, recipients who have been messaged before are excluded.", flush=True)
            print("To include previously messaged recipients, use the --force flag.", flush=True)
        return
    
    successful = 0
    failed = 0
    
    # Use provided delay or default from CONFIG
    delay_seconds = delay if delay is not None else CONFIG["delayBetweenMessages"]
    
    print(f"\n{'='*50}", flush=True)
    if dry_run:
        print(f"DRY RUN: Would send to {len(recipients)} unique recipients", flush=True)
    else:
        print(f"Starting bulk message sending to {len(recipients)} unique recipients", flush=True)
        print(f"Delay between messages: {delay_seconds} seconds", flush=True)
        if force:
            print("WARNING: Force mode enabled - sending to ALL contacts including previously messaged ones", flush=True)
    print(f"{'='*50}\n", flush=True)
    
    start_time = time.time()
    
    # Track processed phone numbers to avoid duplicates
    processed_numbers = set()
    
    # Create a list to store message results for logging
    message_logs = []
    
    for i, recipient in enumerate(recipients):
        # Skip if we've already processed this phone number
        if recipient['formatted_number'] in processed_numbers:
            print(f"[{i+1}/{len(recipients)}] Skipping duplicate number {recipient['formatted_number']} (Order ID: {recipient['order_id']})", flush=True)
            continue
            
        # Add to processed set
        processed_numbers.add(recipient['formatted_number'])
        
        # Display last messaged info if available
        last_messaged_info = ""
        if recipient.get('last_messaged'):
            last_messaged_info = f" [Last messaged: {recipient['last_messaged']}]"
        
        # Print progress
        print(f"[{i+1}/{len(recipients)}] ", end="", flush=True)
        
        if dry_run:
            print(f"Would send to {recipient['formatted_number']} (Order ID: {recipient['order_id']}){last_messaged_info}", flush=True)
            successful += 1
            # Log the dry run result
            message_logs.append({
                'order_id': recipient['order_id'],
                'recipient': recipient.get('recipient', 'Unknown'),
                'phone_number': recipient['formatted_number'],
                'status': 'dry-run',
                'message_sid': None,
                'timestamp': datetime.datetime.now().isoformat()
            })
            continue
        
        result = send_message({
            "content_variables": content_variables,
            "to": recipient['formatted_number'],
            "order_id": recipient['order_id']
        })
        
        # Log the result
        log_entry = {
            'order_id': recipient['order_id'],
            'recipient': recipient.get('recipient', 'Unknown'),
            'phone_number': recipient['formatted_number'],
            'status': result.status if result else 'failed',
            'message_sid': result.sid if result else None,
            'timestamp': datetime.datetime.now().isoformat()
        }
        message_logs.append(log_entry)
        
        if result:
            successful += 1
        else:
            failed += 1
        
        # Add delay between messages to avoid rate limits
        if i < len(recipients) - 1:  # No need to sleep after the last message
            time.sleep(delay_seconds)
    
    elapsed_time = time.time() - start_time
    
    print(f"\n{'='*50}", flush=True)
    if dry_run:
        print("Dry run complete", flush=True)
    else:
        print("Bulk messaging complete", flush=True)
    print(f"Total: {len(processed_numbers)}, Successful: {successful}, Failed: {failed}", flush=True)
    print(f"Time elapsed: {elapsed_time:.2f} seconds", flush=True)
    print(f"{'='*50}\n", flush=True)
    
    # Generate a detailed report file
    if message_logs:
        report_path = generate_report(message_logs, {
            'total': len(processed_numbers),
            'successful': successful,
            'failed': failed,
            'elapsed_time': elapsed_time,
            'dry_run': dry_run,
            'order_status': order_status,
            'order_id': order_id,
            'force': force
        })
        print(f"Report saved to: {report_path}", flush=True)
    
    return {
        "total": len(processed_numbers),
        "successful": successful,
        "failed": failed,
        "elapsed_time": elapsed_time
    }

def generate_report(message_logs, summary):
    """
    Generate a detailed report of the messaging session
    
    Args:
        message_logs: List of message log entries
        summary: Dictionary with summary information
        
    Returns:
        Path to the generated report file
    """
    # Create reports directory if it doesn't exist
    reports_dir = pathlib.Path('reports')
    reports_dir.mkdir(exist_ok=True)
    
    # Generate timestamp for filename with the format dd-mm-yy_hh-mm-ss
    timestamp = datetime.datetime.now().strftime('%d-%m-%y_%H-%M-%S')
    
    # Create filename based on parameters and timestamp
    filename_parts = ['message_report']
    if summary.get('dry_run'):
        filename_parts.append('dry_run')
    if summary.get('force'):
        filename_parts.append('force')
    if summary.get('order_status'):
        filename_parts.append(f"status_{summary['order_status']}")
    filename_parts.append(timestamp)
    
    filename = '_'.join(filename_parts) + '.txt'
    report_path = reports_dir / filename
    
    # Write the report
    with open(report_path, 'w') as f:
        # Write header
        f.write('='*80 + '\n')
        f.write(f"MOJO WHATSAPP MESSAGE REPORT\n")
        f.write(f"Generated: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        if summary.get('dry_run'):
            f.write("Mode: DRY RUN (no messages actually sent)\n")
        else:
            f.write("Mode: LIVE RUN\n")
        if summary.get('force'):
            f.write("WARNING: FORCE MODE ENABLED - Including previously messaged recipients\n")
        f.write('='*80 + '\n\n')
        
        # Only include filters section if there are actual filters to display
        if summary.get('order_status') or summary.get('order_id'):
            f.write("MESSAGE SENT TO:\n")
            if summary.get('order_status'):
                f.write(f"  Orders with status: {summary['order_status']}\n")
            if summary.get('order_id'):
                f.write(f"  Specific order ID: {summary['order_id']}\n")
            f.write("\n")
        
        # Write detailed message logs
        f.write("DETAILED MESSAGE LOG:\n")
        f.write('-'*80 + '\n')
        for i, log in enumerate(message_logs, 1):
            f.write(f"Message {i}:\n")
            f.write(f"  Order ID: {log['order_id']}\n")
            f.write(f"  Recipient: {log['recipient']}\n")
            f.write(f"  Phone Number: {log['phone_number']}\n")
            f.write(f"  Status: {log['status']}\n")
            if log['message_sid']:
                f.write(f"  Message SID: {log['message_sid']}\n")
            f.write(f"  Timestamp: {log['timestamp']}\n")
            f.write('-'*80 + '\n')
        
        # Write summary
        f.write("\nSUMMARY:\n")
        f.write(f"Total unique recipients: {summary['total']}\n")
        f.write(f"Successful: {summary['successful']}\n")
        f.write(f"Failed: {summary['failed']}\n")
        f.write(f"Time elapsed: {summary['elapsed_time']:.2f} seconds\n")
        
    return report_path

def parse_arguments():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(description="Send WhatsApp messages using Twilio")
    
    parser.add_argument("--dry-run", action="store_true", 
                        help="Perform a dry run without actually sending messages (default mode)")
    
    parser.add_argument("--live", action="store_true",
                        help="Send actual messages (without this flag, dry-run is the default)")
    
    parser.add_argument("--delay", type=float, 
                        help=f"Delay between messages in seconds (default: {CONFIG['delayBetweenMessages']})")
    
    parser.add_argument("--status", type=str, 
                        help="Filter recipients by order status (e.g., SHIPPED, DELIVERED)")
    
    parser.add_argument("--order-id", type=str,
                        help="Filter by specific order ID")
    
    parser.add_argument("--limit", type=int, 
                        help="Maximum number of messages to send")
    
    parser.add_argument("--template", type=str, 
                        help=f"Twilio Content Template SID (default: {CONFIG['templateId']})")
    
    parser.add_argument("--db", type=str, 
                        help=f"Database path (default: {CONFIG['dbPath']})")
    
    parser.add_argument("--force", action="store_true",
                        help="Force sending to all recipients, including those previously messaged")
    
    parser.add_argument("--testing-mode", action="store_true",
                        help="Use testing database with only the test phone number")
    
    return parser.parse_args()

def main():
    args = parse_arguments()
    
    print("--- Running send_message.py main() function ---", flush=True)
    print(f"Using Account SID: {account_sid[:5]}...", flush=True)
    print(f"Using WhatsApp Number: {CONFIG['whatsappNumber']}", flush=True)
    
    if CONFIG['messagingServiceSid']:
        print(f"Using Messaging Service SID: {CONFIG['messagingServiceSid']}", flush=True)
    else:
        print("Messaging Service SID not configured (optional).", flush=True)
    
    # Override template ID if provided
    if args.template:
        CONFIG["templateId"] = args.template
    
    print(f"Using Template ID: {CONFIG['templateId']}", flush=True)
    
    # Override database path if testing mode is enabled
    db_path = CONFIG["dbPath"]
    if args.testing_mode:
        # Create or use a testing database with only the test number
        db_path = "testing.db"
        ensure_testing_db_exists(db_path)
        print("\n⚠️  TESTING MODE ENABLED - Using test database with single test number ⚠️\n", flush=True)
    elif args.db:
        db_path = args.db
    
    print(f"Using database: {db_path}", flush=True)
    
    # Determine if we're in dry run mode (default) or live mode
    dry_run = not args.live
    if dry_run:
        print("DRY RUN MODE: No actual messages will be sent (use --live to send real messages)", flush=True)
    else:
        print("\n⚠️  LIVE MODE ENABLED - ACTUAL MESSAGES WILL BE SENT ⚠️\n", flush=True)
        input("Press ENTER to continue or CTRL+C to cancel...")
    
    # Set filter condition for specific order ID
    filter_conditions = None
    if args.order_id:
        filter_conditions = f"o.order_id = '{args.order_id}'"
    
    # Display warning if force flag is set
    if args.force and not dry_run:
        print("\n⚠️  WARNING: FORCE FLAG ENABLED - Will send to ALL recipients including previously messaged ones ⚠️\n", flush=True)
        input("Press ENTER to continue or CTRL+C to cancel...")
    
    # Send to all recipients matching criteria from database
    send_bulk_messages(
        filter_conditions=filter_conditions,
        order_status=args.status,
        limit=args.limit,
        dry_run=dry_run,
        delay=args.delay,
        order_id=args.order_id,
        db_path=db_path,
        force=args.force
    )

def ensure_testing_db_exists(db_path):
    """
    Create or verify a testing database with only the test number
    """
    test_phone = "+61417890602"
    
    # Create database if it doesn't exist
    if not os.path.exists(db_path):
        # Connect to the database
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Create orders table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS orders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            order_status TEXT,
            recipient TEXT,
            product_name TEXT,
            phone_number TEXT,
            raw_phone_number TEXT,
            is_valid_for_whatsapp BOOLEAN,
            last_messaged TEXT,
            last_updated TEXT
        )
        ''')
        
        # Create message log table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS message_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            order_id TEXT,
            phone_number TEXT,
            message_template_id TEXT,
            message_sid TEXT,
            status TEXT,
            sent_time TEXT,
            error_message TEXT
        )
        ''')
        
        # Add test phone number
        cursor.execute('''
        INSERT INTO orders (
            order_id, order_status, recipient, product_name, 
            phone_number, raw_phone_number, is_valid_for_whatsapp, last_updated
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            "TEST12345", "TEST", "Test Recipient", "Test Product", 
            test_phone.replace("+", ""), test_phone, 1, datetime.datetime.now().isoformat()
        ))
        
        conn.commit()
        conn.close()
        print(f"Created testing database at {db_path} with test number {test_phone}")
    
    return db_path

if __name__ == "__main__":
    main() 