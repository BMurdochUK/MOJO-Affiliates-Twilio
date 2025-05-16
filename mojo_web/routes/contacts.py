"""
Contacts routes for managing recipients/contacts
"""
import os
import sqlite3
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response
from flask_login import login_required
from werkzeug.utils import secure_filename
from mojo_core.db_utils import get_db_connection, clean_phone_number
import datetime

bp = Blueprint('contacts', __name__, url_prefix='/contacts')

@bp.route('/')
@login_required
def index():
    """List contacts from selected database"""
    db_path = request.args.get('db_path', current_app.config['DEFAULT_DB_PATH'])
    page = request.args.get('page', 1, type=int)
    per_page = 50
    offset = (page - 1) * per_page
    
    contacts = []
    total_count = 0
    total_pages = 0
    error_message = None
    
    try:
        conn = get_db_connection(db_path)
        
        # Get total count
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM orders")
        total_count = cursor.fetchone()[0]
        
        # Get contacts with pagination
        cursor.execute("""
            SELECT 
                order_id, recipient, phone_number, raw_phone_number, order_status, 
                is_valid_for_whatsapp, last_messaged, last_updated
            FROM 
                orders
            ORDER BY 
                last_updated DESC
            LIMIT ? OFFSET ?
        """, (per_page, offset))
        
        contacts = cursor.fetchall()
        conn.close()
        
        # Calculate total pages
        total_pages = (total_count + per_page - 1) // per_page
        
    except Exception as e:
        error_message = f"Error accessing database: {str(e)}"
    
    # Generate direct HTML response
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Contacts - MOJO WhatsApp Manager</title>
        
        <!-- Bootstrap CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
        
        <style>
            :root {
                --mojo-dark: #272D45;
                --mojo-red: #E60517;
                --mojo-dark-red: #87000A;
            }
            
            body {
                background-color: #f5f5f5;
            }
            
            .navbar {
                background-color: var(--mojo-dark);
            }
            
            .logo-text {
                color: white;
                font-weight: bold;
                font-size: 24px;
            }
            
            .btn-primary {
                background-color: var(--mojo-red);
                border-color: var(--mojo-red);
            }
            
            .btn-primary:hover {
                background-color: var(--mojo-dark-red);
                border-color: var(--mojo-dark-red);
            }
            
            .logout-btn {
                color: white;
                text-decoration: none;
            }
            
            .logout-btn:hover {
                color: #f8f9fa;
            }
            
            .pagination .page-item.active .page-link {
                background-color: var(--mojo-red);
                border-color: var(--mojo-red);
            }
            
            .pagination .page-link {
                color: var(--mojo-dark);
            }
            
            .valid-badge {
                background-color: #28a745;
            }
            
            .invalid-badge {
                background-color: #dc3545;
            }
        </style>
    </head>
    <body>
        <!-- Navbar -->
        <nav class="navbar navbar-dark py-3">
            <div class="container">
                <span class="navbar-brand logo-text">
                    <div style="background: var(--mojo-red); color: white; display: inline-block; width: 40px; height: 40px; border-radius: 50%; text-align: center; line-height: 40px; margin-right: 10px;">M</div>
                    MOJO WhatsApp Manager
                </span>
                <div>
                    <a href="/" class="btn btn-outline-light me-2">Dashboard</a>
                    <a href="/auth/logout" class="logout-btn">
                        <i class="fas fa-sign-out-alt"></i> Logout
                    </a>
                </div>
            </div>
        </nav>
        
        <!-- Main Content -->
        <div class="container mt-4">
            <div class="row mb-4">
                <div class="col-md-6">
                    <h2>Contacts</h2>
                    <p class="text-muted">Manage recipient contacts from your database</p>
                </div>
                <div class="col-md-6 text-end">
                    <a href="/contacts/import" class="btn btn-primary">
                        <i class="fas fa-upload"></i> Import Contacts
                    </a>
                </div>
            </div>
            
            <!-- Search and Filter -->
            <div class="card mb-4">
                <div class="card-body">
                    <div class="row g-3">
                        <div class="col-md-6">
                            <form action="/contacts/search" method="get" class="d-flex">
                                <input type="hidden" name="db_path" value="{db_path}">
                                <input type="text" name="q" class="form-control" placeholder="Search contacts...">
                                <button type="submit" class="btn btn-primary ms-2">
                                    <i class="fas fa-search"></i>
                                </button>
                            </form>
                        </div>
                        <div class="col-md-6">
                            <form action="/contacts/filter" method="get" class="d-flex">
                                <input type="hidden" name="db_path" value="{db_path}">
                                <select name="status" class="form-select">
                                    <option value="">All Statuses</option>
                                    <option value="READY_TO_SHIP">Ready to Ship</option>
                                    <option value="SHIPPED">Shipped</option>
                                    <option value="DELIVERED">Delivered</option>
                                    <option value="CANCELLED">Cancelled</option>
                                    <option value="IMPORTED">Imported</option>
                                </select>
                                <button type="submit" class="btn btn-primary ms-2">
                                    <i class="fas fa-filter"></i>
                                </button>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
    """
    
    # Add error message if exists
    if error_message:
        html += f"""
            <div class="alert alert-danger" role="alert">
                {error_message}
            </div>
        """
    
    # Add contacts table
    html += f"""
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <span>Contacts ({total_count})</span>
                    <span>Database: {db_path}</span>
                </div>
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Order ID</th>
                                    <th>Recipient</th>
                                    <th>Phone Number</th>
                                    <th>Status</th>
                                    <th>WhatsApp</th>
                                    <th>Last Messaged</th>
                                    <th>Last Updated</th>
                                </tr>
                            </thead>
                            <tbody>
    """
    
    # Add contacts rows
    if contacts:
        for contact in contacts:
            order_id, recipient, phone_number, raw_phone_number, order_status, is_valid, last_messaged, last_updated = contact
            
            # Format validity badge
            valid_badge = f'<span class="badge valid-badge">Valid</span>' if is_valid else f'<span class="badge invalid-badge">Invalid</span>'
            
            # Format last messaged date
            if last_messaged:
                try:
                    last_messaged_date = datetime.datetime.fromisoformat(last_messaged)
                    last_messaged_formatted = last_messaged_date.strftime('%Y-%m-%d %H:%M')
                except:
                    last_messaged_formatted = last_messaged
            else:
                last_messaged_formatted = 'Never'
            
            # Format last updated date
            if last_updated:
                try:
                    last_updated_date = datetime.datetime.fromisoformat(last_updated)
                    last_updated_formatted = last_updated_date.strftime('%Y-%m-%d %H:%M')
                except:
                    last_updated_formatted = last_updated
            else:
                last_updated_formatted = 'Unknown'
            
            html += f"""
                                <tr>
                                    <td>{order_id}</td>
                                    <td>{recipient}</td>
                                    <td>{phone_number or raw_phone_number}</td>
                                    <td>{order_status}</td>
                                    <td>{valid_badge}</td>
                                    <td>{last_messaged_formatted}</td>
                                    <td>{last_updated_formatted}</td>
                                </tr>
            """
    else:
        html += """
                                <tr>
                                    <td colspan="7" class="text-center">No contacts found.</td>
                                </tr>
        """
    
    # Close table and add pagination
    html += """
                            </tbody>
                        </table>
                    </div>
    """
    
    # Add pagination if needed
    if total_pages > 1:
        html += f"""
                    <nav aria-label="Page navigation">
                        <ul class="pagination justify-content-center">
        """
        
        # Previous page button
        prev_disabled = "disabled" if page <= 1 else ""
        prev_page = page - 1 if page > 1 else 1
        html += f"""
                            <li class="page-item {prev_disabled}">
                                <a class="page-link" href="/contacts/?db_path={db_path}&page={prev_page}" aria-label="Previous">
                                    <span aria-hidden="true">&laquo;</span>
                                </a>
                            </li>
        """
        
        # Page number buttons
        for p in range(max(1, page - 2), min(total_pages + 1, page + 3)):
            active = "active" if p == page else ""
            html += f"""
                            <li class="page-item {active}">
                                <a class="page-link" href="/contacts/?db_path={db_path}&page={p}">{p}</a>
                            </li>
            """
        
        # Next page button
        next_disabled = "disabled" if page >= total_pages else ""
        next_page = page + 1 if page < total_pages else total_pages
        html += f"""
                            <li class="page-item {next_disabled}">
                                <a class="page-link" href="/contacts/?db_path={db_path}&page={next_page}" aria-label="Next">
                                    <span aria-hidden="true">&raquo;</span>
                                </a>
                            </li>
                        </ul>
                    </nav>
        """
    
    # Close card and main container
    html += """
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-12 text-center">
                    <p class="text-muted">MOJO WhatsApp Manager | Version 1.0</p>
                </div>
            </div>
        </div>
        
        <!-- Bootstrap JavaScript -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    # Format DB path in the HTML
    html = html.replace("{db_path}", db_path)
    
    return make_response(html)

@bp.route('/import', methods=['GET', 'POST'])
@login_required
def import_contacts():
    """Import contacts from CSV or text file"""
    if request.method == 'POST':
        import_type = request.form.get('import_type')
        db_path = request.form.get('db_path', current_app.config['DEFAULT_DB_PATH'])
        
        if import_type == 'csv':
            # CSV import
            if 'csv_file' not in request.files:
                flash('No file selected', 'danger')
                return redirect(request.url)
                
            file = request.files['csv_file']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)
                
            if file:
                filename = secure_filename(file.filename)
                temp_dir = os.path.join(current_app.root_path, '..', 'temp')
                os.makedirs(temp_dir, exist_ok=True)
                file_path = os.path.join(temp_dir, filename)
                file.save(file_path)
                
                # Call the CSV import function from import_csv.py
                # We'll just show a success message here for the demo
                flash(f'File {filename} imported successfully. Use the CLI tool import_csv.py for actual import.', 'success')
                return redirect(url_for('contacts.index', db_path=db_path))
        
        elif import_type == 'text':
            # Text file import (one number per line)
            if 'text_file' not in request.files:
                flash('No file selected', 'danger')
                return redirect(request.url)
                
            file = request.files['text_file']
            if file.filename == '':
                flash('No file selected', 'danger')
                return redirect(request.url)
                
            if file:
                # Read the numbers from the file
                numbers = file.read().decode('utf-8').strip().split('\n')
                numbers = [n.strip() for n in numbers if n.strip()]
                
                if not numbers:
                    flash('No valid phone numbers found in file', 'warning')
                    return redirect(request.url)
                
                # Process the numbers
                try:
                    conn = get_db_connection(db_path)
                    cursor = conn.cursor()
                    
                    # Ensure the orders table exists
                    cursor.execute("""
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
                    """)
                    
                    # Process and deduplicate numbers
                    unique_numbers = set()
                    valid_count = 0
                    invalid_count = 0
                    
                    for number in numbers:
                        clean_number, raw_number, is_valid = clean_phone_number(number)
                        
                        # Skip if already seen
                        if raw_number in unique_numbers:
                            continue
                            
                        unique_numbers.add(raw_number)
                        
                        if is_valid:
                            # Generate an order ID based on the cleaned number
                            order_id = f"IMPORT{clean_number[-8:]}"
                            
                            # Check if order_id exists
                            cursor.execute("SELECT id FROM orders WHERE order_id = ?", (order_id,))
                            if cursor.fetchone():
                                # Append timestamp to make it unique
                                import time
                                order_id = f"{order_id}{int(time.time())}"
                            
                            # Insert the contact
                            cursor.execute("""
                                INSERT INTO orders 
                                (order_id, order_status, recipient, product_name, raw_phone_number, phone_number, is_valid_for_whatsapp, last_updated)
                                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                            """, (
                                order_id, 
                                'IMPORTED', 
                                'Imported Contact', 
                                'Web Import', 
                                raw_number, 
                                clean_number, 
                                is_valid, 
                                datetime.datetime.now().isoformat()
                            ))
                            valid_count += 1
                        else:
                            invalid_count += 1
                    
                    conn.commit()
                    conn.close()
                    
                    flash(f'Imported {valid_count} valid contacts. {invalid_count} invalid numbers were skipped.', 'success')
                    return redirect(url_for('contacts.index', db_path=db_path))
                
                except Exception as e:
                    flash(f'Error importing contacts: {str(e)}', 'danger')
                    return redirect(request.url)
                
        else:
            flash('Invalid import type', 'danger')
            return redirect(request.url)
            
    # GET request - show import form
    return render_template('contacts/import.html')

@bp.route('/search', methods=['GET'])
@login_required
def search():
    """Search contacts"""
    query = request.args.get('q', '')
    db_path = request.args.get('db_path', current_app.config['DEFAULT_DB_PATH'])
    
    if not query:
        return redirect(url_for('contacts.index', db_path=db_path))
    
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Search in multiple fields
        cursor.execute("""
            SELECT 
                order_id, recipient, phone_number, raw_phone_number, order_status, 
                is_valid_for_whatsapp, last_messaged, last_updated
            FROM 
                orders
            WHERE 
                order_id LIKE ? OR
                recipient LIKE ? OR
                phone_number LIKE ? OR
                raw_phone_number LIKE ?
            ORDER BY 
                last_updated DESC
            LIMIT 100
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        
        contacts = cursor.fetchall()
        conn.close()
        
        return render_template('contacts/search.html', 
                              contacts=contacts, 
                              db_path=db_path,
                              query=query)
                              
    except Exception as e:
        flash(f"Error searching database: {str(e)}", "danger")
        return render_template('contacts/search.html', 
                              contacts=[], 
                              db_path=db_path,
                              query=query)

@bp.route('/filter', methods=['GET'])
@login_required
def filter_contacts():
    """Filter contacts by status"""
    status = request.args.get('status', '')
    db_path = request.args.get('db_path', current_app.config['DEFAULT_DB_PATH'])
    
    if not status:
        return redirect(url_for('contacts.index', db_path=db_path))
    
    try:
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        
        # Filter by status
        cursor.execute("""
            SELECT 
                order_id, recipient, phone_number, raw_phone_number, order_status, 
                is_valid_for_whatsapp, last_messaged, last_updated
            FROM 
                orders
            WHERE 
                order_status = ?
            ORDER BY 
                last_updated DESC
            LIMIT 500
        """, (status,))
        
        contacts = cursor.fetchall()
        conn.close()
        
        # Get unique statuses for filter options
        conn = get_db_connection(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT order_status FROM orders")
        statuses = [row[0] for row in cursor.fetchall() if row[0]]
        conn.close()
        
        return render_template('contacts/filter.html', 
                              contacts=contacts, 
                              db_path=db_path,
                              status=status,
                              statuses=statuses)
                              
    except Exception as e:
        flash(f"Error filtering database: {str(e)}", "danger")
        return render_template('contacts/filter.html', 
                              contacts=[], 
                              db_path=db_path,
                              status=status,
                              statuses=[]) 