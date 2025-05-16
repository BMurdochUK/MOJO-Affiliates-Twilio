"""
Settings routes
"""
import os
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

bp = Blueprint('settings', __name__, url_prefix='/settings')

@bp.route('/')
def index():
    """Settings page"""
    # Get current settings from config
    settings = {
        'twilio_account_sid': current_app.config.get('TWILIO_ACCOUNT_SID', ''),
        'twilio_auth_token': current_app.config.get('TWILIO_AUTH_TOKEN', ''),
        'twilio_whatsapp_number': current_app.config.get('TWILIO_WHATSAPP_NUMBER', ''),
        'twilio_messaging_service_sid': current_app.config.get('TWILIO_MESSAGING_SERVICE_SID', ''),
        'default_db_path': current_app.config.get('DEFAULT_DB_PATH', 'affiliates.db')
    }
    
    # Partially mask sensitive info
    if settings['twilio_account_sid']:
        settings['twilio_account_sid_masked'] = settings['twilio_account_sid'][:4] + ''.join(['*' for _ in range(len(settings['twilio_account_sid']) - 8)]) + settings['twilio_account_sid'][-4:]
    
    if settings['twilio_auth_token']:
        settings['twilio_auth_token_masked'] = ''.join(['*' for _ in range(len(settings['twilio_auth_token']))])
    
    # Get available databases
    db_files = []
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.db'):
                db_files.append(os.path.join(root, file))
    
    return render_template('settings/index.html', 
                          settings=settings,
                          db_files=db_files)

@bp.route('/update', methods=['POST'])
def update():
    """Update settings"""
    # Note: In a real app, this would save to a config file or database
    # For this demo, we'll just show a success message
    flash('Settings updated successfully. Note: In the demo, settings are not actually saved persistently.', 'success')
    return redirect(url_for('settings.index')) 