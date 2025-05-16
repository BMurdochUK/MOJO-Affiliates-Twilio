"""
Authentication routes
"""
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response
from flask_login import login_user, logout_user, login_required
from mojo_web import db
from mojo_web.models import User

bp = Blueprint('auth', __name__, url_prefix='/auth')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    """Login route"""
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        
        user = User.query.filter_by(username=username).first()
        
        # Check if user exists
        if not user:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check if account is locked
        if user.is_account_locked():
            remaining_time = (user.locked_until - datetime.now()).total_seconds()
            flash(f'Account is locked. Try again in {int(remaining_time)} seconds.', 'danger')
            return redirect(url_for('auth.login'))
        
        # Check password
        if not user.check_password(password):
            user.record_login_attempt(successful=False)
            flash('Invalid username or password', 'danger')
            return redirect(url_for('auth.login'))
        
        # Successful login
        user.record_login_attempt(successful=True)
        login_user(user)
        flash('Login successful', 'success')
        return redirect(url_for('dashboard.index'))
    
    # Get flash messages
    from flask import get_flashed_messages
    messages = []
    categories = []
    flashed_messages = get_flashed_messages(with_categories=True)
    for cat, msg in flashed_messages:
        messages.append(msg)
        categories.append(cat)
    
    # Direct HTML response
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Login - MOJO WhatsApp Manager</title>
        
        <!-- Bootstrap CSS -->
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
        
        <style>
            body {
                background-color: #272D45;
                height: 100vh;
                display: flex;
                align-items: center;
                justify-content: center;
            }
            
            .card {
                background-color: #343a40;
                color: white;
                border-radius: 10px;
                max-width: 400px;
                width: 100%;
                box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
            }
            
            .btn-primary {
                background-color: #E60517;
                border-color: #E60517;
            }
            
            .btn-primary:hover {
                background-color: #87000A;
                border-color: #87000A;
            }
            
            .logo-placeholder {
                color: white;
                background-color: #E60517;
                width: 80px;
                height: 80px;
                margin: 0 auto;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 20px;
                margin-bottom: 20px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="row justify-content-center">
                <div class="col-md-6">
                    <div class="card">
                        <div class="card-body p-4">
                            <div class="text-center mb-4">
                                <div class="logo-placeholder">MOJO</div>
                                <h3>MOJO WhatsApp Manager</h3>
                                <p class="text-muted">Please log in to access the dashboard</p>
                            </div>
                            
                            <!-- Flash Messages -->
    """
    
    # Add flash messages
    for i in range(len(messages)):
        html += f'<div class="alert alert-{categories[i]}">{messages[i]}</div>'
    
    html += """
                            <form method="POST">
                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                <div class="mb-3">
                                    <label for="username" class="form-label">Username</label>
                                    <input type="text" class="form-control" id="username" name="username" required>
                                </div>
                                <div class="mb-3">
                                    <label for="password" class="form-label">Password</label>
                                    <input type="password" class="form-control" id="password" name="password" required>
                                </div>
                                <div class="d-grid">
                                    <button type="submit" class="btn btn-primary">Login</button>
                                </div>
                            </form>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Bootstrap JavaScript -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    </body>
    </html>
    """
    
    # Replace the csrf_token placeholder
    html = html.replace("{{ csrf_token() }}", current_app.jinja_env.globals['csrf_token']())
    
    response = make_response(html)
    return response

@bp.route('/logout')
@login_required
def logout():
    """Logout route"""
    logout_user()
    flash('You have been logged out', 'info')
    return redirect(url_for('auth.login')) 