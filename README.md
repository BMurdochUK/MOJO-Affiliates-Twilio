# MOJO Twilio WhatsApp Bulk Messaging System

A robust system for sending Twilio Content Template messages to multiple WhatsApp recipients using a SQLite database.

## Features

- Import order data from CSV files into a SQLite database
- Automatically handle obfuscated phone numbers
- Send WhatsApp messages to customers with valid phone numbers
- Filter recipients by order status (e.g., only send to SHIPPED orders)
- Log all message sending attempts for tracking and analysis
- Dry run mode to test without sending actual messages
- Deduplication to ensure only one message per unique phone number
- Detailed reporting with timestamped log files
- Bulk import of phone numbers from text files
- Safety feature to prevent accidental re-messaging of contacts

## Setup

1. Make sure you have Python 3.6+ installed
2. Create a virtual environment: `python3 -m venv venv`
3. Activate the virtual environment:
   - On macOS/Linux: `source venv/bin/activate`
   - On Windows: `venv\Scripts\activate`
4. Install dependencies: `pip install twilio python-dotenv pandas`
5. Create a `.env` file with your Twilio credentials:
```
TWILIO_ACCOUNT_SID=your_account_sid
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_WHATSAPP_NUMBER=whatsapp:+your_whatsapp_number
# Optional: TWILIO_MESSAGING_SERVICE_SID=your_messaging_service_sid
# Optional: DB_PATH=path/to/your/database.db
```

## Database Setup

Initialize the database:

```bash
python create_database.py
```

This creates a SQLite database with the order schema and message logging table.

You can specify a custom database name:

```bash
python create_database.py --db affiliates.db
```

## Importing Data

### From CSV Files

Import order data from a CSV file:

```bash
python import_csv.py path/to/your/orders.csv
```

Options:
- `--db path/to/your/database.db`: Specify a custom database path
- `--delimiter ","`: Specify a custom CSV delimiter

### From Text File (Bulk Import)

Import phone numbers directly from a text file (one number per line) and send messages:

```bash
python bulk_import_and_send.py
```

This script will:
1. Read phone numbers from `temp/phone_numbers.txt`
2. Deduplicate and validate the numbers
3. Import them into the affiliates.db database
4. Send messages to all valid numbers that haven't been messaged before
5. Generate a detailed report

Options:
```bash
# Specify a custom phone numbers file
python bulk_import_and_send.py --phone-file numbers.txt

# Use a custom database
python bulk_import_and_send.py --db customers.db

# Only import numbers without sending messages
python bulk_import_and_send.py --import-only

# Perform a dry run without sending messages
python bulk_import_and_send.py --dry-run

# Override safety feature to message all contacts including previously messaged ones
python bulk_import_and_send.py --force
```

## Sending Messages

Basic usage:
```bash
python send_message.py
```

Filter options:
```bash
# Only send to orders with a specific status
python send_message.py --status SHIPPED

# Send to a specific order ID
python send_message.py --order-id ORDER123456

# Limit to 10 messages
python send_message.py --limit 10

# Perform a dry run (no messages sent)
python send_message.py --dry-run

# Specify a custom delay between messages (in seconds)
python send_message.py --delay 2.5

# Use a different database
python send_message.py --db affiliates.db

# Use a different template
python send_message.py --template HXXXXXXXXXXXXXXXX

# Override safety feature to message all contacts including previously messaged ones
python send_message.py --force
```

## Phone Number Handling

The system automatically processes phone numbers:

1. Obfuscated numbers (containing * characters) are flagged as invalid for WhatsApp
2. Phone numbers are cleaned by removing parentheses and + for WhatsApp compatibility
3. WhatsApp prefix is added to valid numbers

## Deduplication

The system ensures that only one message is sent per unique phone number, even if:
- The same number appears in multiple orders
- The same number is imported multiple times
- Different formatting is used for the same number

This prevents sending duplicate messages to customers.

## Safety Features

### Anti-Messaging Protection

To prevent accidental repeat messaging to contacts:

1. The system tracks when each contact was last messaged in the database
2. By default, contacts who have been messaged before will be excluded from future messaging operations
3. When no contacts are found to message, the system will indicate that previously messaged contacts exist
4. To explicitly override this protection, you must use the `--force` flag
5. When using `--force`, the system will display a warning and require confirmation before proceeding

This helps prevent accidental messaging during development and testing while still allowing deliberate re-messaging when needed.

## Reporting

Detailed reports are automatically generated after each messaging operation in the `reports/` directory. Reports include:

- Timestamp and run mode (dry run or live)
- Filters applied to select recipients
- Detailed message log for each recipient
- Message status and Twilio SID
- Summary statistics

Example report filename: `message_report_status_SHIPPED_16-05-25_18-12-13.txt`

## Database Schema

The system uses two tables:

### Orders Table
Stores all order information including:
- Order details (ID, status, products, etc.)
- Customer information (name, phone, address)
- Phone number processing results (clean number, valid flag)
- Last messaged timestamp (to prevent accidental re-messaging)

### Message Log Table
Records all message sending attempts:
- Order ID
- Phone number
- Template used
- Message SID
- Status
- Timestamp
- Error message (if any)

## Workflow

1. Import order data daily from CSV exports
2. The system updates existing orders and adds new ones
3. Obfuscated phone numbers are automatically marked as invalid
4. When an order's phone number becomes unobfuscated, it's updated and marked as valid
5. Send messages to orders with valid phone numbers filtered by criteria
6. Only contacts that haven't been messaged before will receive messages (unless `--force` is used)

## Command Line Options

| Option | Description |
| ------ | ----------- |
| `--dry-run` | Perform a dry run without sending actual messages |
| `--delay SECONDS` | Set the delay between messages (default: 1 second) |
| `--status STATUS` | Filter recipients by order status (e.g., SHIPPED, DELIVERED) |
| `--order-id ID` | Send to a specific order ID |
| `--limit NUMBER` | Maximum number of messages to send |
| `--template SID` | Use a different Twilio Content Template |
| `--db PATH` | Use an alternative database file |
| `--force` | Override safety protection and message all contacts including previously messaged ones |

## Notes

- WhatsApp messages sent with Twilio are subject to rate limits and messaging policies
- Add appropriate delay between messages to avoid rate limiting
- Recipients must have opted in to receive WhatsApp messages from your Twilio number
- Always test with a small group before sending to a large list
- Automatic deduplication prevents sending duplicate messages to the same number
- All message activity is logged in the database and in text reports
- Safety feature prevents accidental re-messaging of contacts during development

## Web Interface

MOJO WhatsApp Manager now includes a web interface for easier management of templates, campaigns, and reporting.

### Web Features

- **Template Management**: Create and manage WhatsApp message templates
- **Campaign Scheduling**: Schedule one-time or recurring message campaigns
- **Advanced Reporting**: View detailed message statistics and campaign results
- **Contact Management**: Import, search, and filter recipients
- **Visualization**: Get graphical insights into your messaging performance
- **User-Friendly Interface**: Modern UI with MOJO branding
- **Secure Authentication**: Password-protected access with account lockout protection

### Running the Web Interface

1. Make sure you've installed all dependencies: `pip install -r requirements.txt`
2. Start the web server: `python web.py`
3. Before first use, create an admin user: `flask create-admin --username mojo-admin --password Letmein99#123`
4. Open your browser and visit `http://localhost:5000`
5. Log in with the default credentials:
   - Username: `mojo-admin`
   - Password: `Letmein99#123`

### Security Features

- Password-protected authentication for all pages
- Account lockout for 120 seconds after 5 failed login attempts
- Secure password hashing

The web interface uses the same database and functionality as the CLI tools, so you can use both interchangeably.

### Web Interface Screenshots

- Dashboard: Shows key statistics and recent activities
- Templates: Manage WhatsApp message templates
- Campaigns: Schedule and track messaging campaigns
- Contacts: Import and manage recipient data
- Reports: View detailed performance metrics

Note: The command-line tools continue to function exactly as before. 