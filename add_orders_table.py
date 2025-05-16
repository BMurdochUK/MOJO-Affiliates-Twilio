import sqlite3
import os

# Connect to the existing database
conn = sqlite3.connect('affiliates.db')
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
    raw_phone_number TEXT,
    is_valid_for_whatsapp BOOLEAN,
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
    last_messaged TEXT,
    last_updated TEXT
)
''')

# Create message_log table which is also needed
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

conn.commit()
conn.close()
print("Added orders and message_log tables to the database") 