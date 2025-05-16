import sqlite3
import os

def create_database(db_path='affiliates.db'):
    """Create a SQLite database with the specified schema"""
    # Check if database already exists
    db_exists = os.path.exists(db_path)
    
    # Connect to database (creates it if it doesn't exist)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Create orders table if it doesn't exist
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        order_id TEXT,
        order_status TEXT,
        order_substatus TEXT,
        cancellation_return_type TEXT,
        normal_or_preorder TEXT,
        sku_id TEXT,
        seller_sku TEXT,
        product_name TEXT,
        variation TEXT,
        quantity INTEGER,
        sku_quantity_return INTEGER,
        sku_unit_original_price REAL,
        sku_subtotal_before_discount REAL,
        sku_platform_discount REAL,
        sku_seller_discount REAL,
        sku_subtotal_after_discount REAL,
        shipping_fee_after_discount REAL,
        original_shipping_fee REAL,
        shipping_fee_seller_discount REAL,
        shipping_fee_platform_discount REAL,
        taxes REAL,
        order_amount REAL,
        order_refund_amount REAL,
        created_time TEXT,
        paid_time TEXT,
        rth_time TEXT,
        shipped_time TEXT,
        delivered_time TEXT,
        cancelled_time TEXT,
        cancel_by TEXT,
        cancel_reason TEXT,
        fulfillment_type TEXT,
        warehouse_name TEXT,
        tracking_id TEXT,
        delivery_option TEXT,
        shipping_provider_name TEXT,
        buyer_message TEXT,
        buyer_username TEXT,
        recipient TEXT,
        phone_number TEXT,
        raw_phone_number TEXT, -- Stores the original phone number format
        is_valid_for_whatsapp BOOLEAN, -- Flag indicating if the number is valid for WhatsApp
        zipcode TEXT,
        state TEXT,
        country TEXT,
        county TEXT,
        districts TEXT,
        street_name TEXT,
        house_number TEXT,
        delivery_instruction TEXT,
        payment_method TEXT,
        weight REAL,
        product_category TEXT,
        package_id TEXT,
        seller_note TEXT,
        shipping_information TEXT,
        checked_status TEXT,
        checked_marked_by TEXT,
        last_messaged TEXT, -- Timestamp when a message was last sent to this number
        last_updated TEXT,
        UNIQUE(order_id, sku_id)
    )
    ''')
    
    # Create WhatsApp message log table
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
    
    # Commit changes and close connection
    conn.commit()
    conn.close()
    
    print(f"{'Created' if not db_exists else 'Verified'} database at {db_path}")
    return db_path

if __name__ == "__main__":
    create_database() 