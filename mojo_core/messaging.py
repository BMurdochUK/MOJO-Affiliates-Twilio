"""
Core messaging functionality shared between CLI and web interface
"""
import os
import time
import datetime
import pathlib
from mojo_core.twilio_client import twilio_client
from mojo_core.db_utils import (
    get_recipients_from_db,
    log_message_to_db,
    update_last_messaged
)

def send_message(db_path, to, content_sid, content_variables=None, order_id=None, log_to_db=True):
    """
    Send a WhatsApp message and log it to the database
    
    Args:
        db_path (str): Path to SQLite database file
        to (str): Recipient's WhatsApp number
        content_sid (str): Content template SID
        content_variables (dict): Variables for the template
        order_id (str): Order ID for tracking
        log_to_db (bool): Whether to log the message to the database
    
    Returns:
        dict: Message result with status and details
    """
    if content_variables is None:
        content_variables = {"senderName": "MOJO Health Supplements"}
        
    try:
        # Send message via Twilio
        message = twilio_client.send_whatsapp_message(
            to=to,
            content_sid=content_sid,
            content_variables=content_variables,
            order_id=order_id
        )
        
        # Log to database if requested
        if log_to_db and order_id:
            log_message_to_db(
                db_path=db_path,
                order_id=order_id,
                phone_number=to,
                template_id=content_sid,
                message_sid=message.sid,
                status=message.status
            )
            
            # Update last_messaged timestamp
            update_last_messaged(db_path, to)
        
        return {
            "success": True,
            "sid": message.sid,
            "status": message.status,
            "to": to,
            "order_id": order_id
        }
    
    except Exception as e:
        # Log error to database if requested
        if log_to_db and order_id:
            log_message_to_db(
                db_path=db_path,
                order_id=order_id,
                phone_number=to,
                template_id=content_sid,
                message_sid=None,
                status="error",
                error_message=str(e)
            )
        
        return {
            "success": False,
            "error": str(e),
            "to": to,
            "order_id": order_id
        }

def send_bulk_messages(db_path, content_sid, content_variables=None, recipients=None, 
                      filter_conditions=None, order_status=None, limit=None, 
                      dry_run=False, delay=1.0, force=False):
    """
    Send WhatsApp messages to multiple recipients
    
    Args:
        db_path (str): Path to SQLite database file
        content_sid (str): Content template SID
        content_variables (dict): Variables for the template
        recipients (list): List of recipient dictionaries (optional)
        filter_conditions (str): Custom SQL WHERE clause
        order_status (str): Filter by order status (e.g., 'SHIPPED', 'DELIVERED')
        limit (int): Maximum number of messages to send
        dry_run (bool): If True, don't actually send messages
        delay (float): Delay between messages in seconds
        force (bool): If True, include previously messaged recipients
    
    Returns:
        dict: Results summary with message logs
    """
    if content_variables is None:
        content_variables = {"senderName": "MOJO Health Supplements"}
    
    if recipients is None:
        # Get recipients from database
        recipients = get_recipients_from_db(
            db_path=db_path,
            filter_conditions=filter_conditions,
            order_status=order_status,
            limit=limit,
            force=force
        )
    
    if not recipients:
        return {
            "success": False,
            "error": "No recipients found",
            "total": 0,
            "successful": 0,
            "failed": 0,
            "logs": []
        }
    
    successful = 0
    failed = 0
    
    start_time = time.time()
    
    # Track processed phone numbers to avoid duplicates
    processed_numbers = set()
    
    # Store message logs
    message_logs = []
    
    for i, recipient in enumerate(recipients):
        # Skip if we've already processed this phone number
        if recipient['formatted_number'] in processed_numbers:
            continue
            
        # Add to processed set
        processed_numbers.add(recipient['formatted_number'])
        
        # Create log entry
        log_entry = {
            'order_id': recipient['order_id'],
            'recipient': recipient.get('recipient', 'Unknown'),
            'phone_number': recipient['formatted_number'],
            'timestamp': datetime.datetime.now().isoformat()
        }
        
        if dry_run:
            log_entry['status'] = 'dry-run'
            log_entry['message_sid'] = None
            successful += 1
        else:
            # Send the message
            result = send_message(
                db_path=db_path,
                to=recipient['formatted_number'],
                content_sid=content_sid,
                content_variables=content_variables,
                order_id=recipient['order_id']
            )
            
            log_entry['status'] = result.get('status', 'failed')
            log_entry['message_sid'] = result.get('sid')
            
            if result['success']:
                successful += 1
            else:
                failed += 1
                log_entry['error'] = result.get('error')
        
        # Add to logs
        message_logs.append(log_entry)
        
        # Add delay between messages to avoid rate limits
        if i < len(recipients) - 1 and not dry_run:
            time.sleep(delay)
    
    elapsed_time = time.time() - start_time
    
    # Generate a detailed report file
    if message_logs:
        report_path = generate_report(
            message_logs=message_logs,
            summary={
                'total': len(processed_numbers),
                'successful': successful,
                'failed': failed,
                'elapsed_time': elapsed_time,
                'dry_run': dry_run,
                'order_status': order_status,
                'force': force
            }
        )
    else:
        report_path = None
    
    return {
        "success": True,
        "total": len(processed_numbers),
        "successful": successful,
        "failed": failed,
        "elapsed_time": elapsed_time,
        "report_path": report_path,
        "logs": message_logs
    }

def generate_report(message_logs, summary):
    """
    Generate a detailed report of the messaging session
    
    Args:
        message_logs (list): List of message log entries
        summary (dict): Dictionary with summary information
        
    Returns:
        str: Path to the generated report file
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
        if summary.get('order_status'):
            f.write("MESSAGE SENT TO:\n")
            if summary.get('order_status'):
                f.write(f"  Orders with status: {summary['order_status']}\n")
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
            if log.get('message_sid'):
                f.write(f"  Message SID: {log['message_sid']}\n")
            if log.get('error'):
                f.write(f"  Error: {log['error']}\n")
            f.write(f"  Timestamp: {log['timestamp']}\n")
            f.write('-'*80 + '\n')
        
        # Write summary
        f.write("\nSUMMARY:\n")
        f.write(f"Total unique recipients: {summary['total']}\n")
        f.write(f"Successful: {summary['successful']}\n")
        f.write(f"Failed: {summary['failed']}\n")
        f.write(f"Time elapsed: {summary['elapsed_time']:.2f} seconds\n")
    
    return str(report_path) 