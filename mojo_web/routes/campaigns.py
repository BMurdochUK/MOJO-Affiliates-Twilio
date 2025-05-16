"""
Campaigns routes
"""
from datetime import datetime
import json
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, make_response
from flask_login import login_required
from mojo_web import db, scheduler
from mojo_web.models import Template, Campaign, CampaignLog
from mojo_core.messaging import send_bulk_messages

bp = Blueprint('campaigns', __name__, url_prefix='/campaigns')

@bp.route('/')
@login_required
def index():
    """List all campaigns"""
    campaigns = Campaign.query.order_by(Campaign.updated_at.desc()).all()
    
    # Generate direct HTML response
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Campaigns - MOJO WhatsApp Manager</title>
        
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
            
            .campaign-card {
                transition: transform 0.2s;
            }
            
            .campaign-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 20px rgba(0,0,0,0.1);
            }
            
            .status-badge {
                text-transform: uppercase;
                font-size: 0.8rem;
                font-weight: bold;
            }
            
            .badge-draft {
                background-color: #6c757d;
            }
            
            .badge-scheduled {
                background-color: #ffc107;
                color: #212529;
            }
            
            .badge-running {
                background-color: #17a2b8;
            }
            
            .badge-completed {
                background-color: #28a745;
            }
            
            .badge-failed {
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
                    <h2>Campaigns</h2>
                    <p class="text-muted">Manage your WhatsApp message campaigns</p>
                </div>
                <div class="col-md-6 text-end">
                    <a href="/campaigns/create" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Create New Campaign
                    </a>
                </div>
            </div>
            
            <div class="row">
    """
    
    # Add campaign cards
    if campaigns:
        for campaign in campaigns:
            # Determine status badge class
            status_class = {
                'draft': 'badge-draft text-white',
                'scheduled': 'badge-scheduled',
                'running': 'badge-running text-white',
                'completed': 'badge-completed text-white',
                'failed': 'badge-failed text-white'
            }.get(campaign.status, 'badge-secondary')
            
            # Format next run time
            next_run_text = campaign.next_run.strftime('%Y-%m-%d %H:%M') if campaign.next_run else 'Not scheduled'
            
            # Determine if recurring
            recurring_text = '<span class="text-success"><i class="fas fa-sync-alt"></i> Recurring</span>' if campaign.is_recurring else ''
            
            # Get template name
            template_name = campaign.template.name if campaign.template else 'Unknown Template'
            
            html += f"""
                <div class="col-md-4 mb-4">
                    <div class="card campaign-card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <h5 class="mb-0">{campaign.name}</h5>
                            <span class="badge status-badge {status_class}">{campaign.status}</span>
                        </div>
                        <div class="card-body">
                            <p class="card-text">{campaign.description or 'No description provided'}</p>
                            
                            <div class="mb-2">
                                <small class="text-muted">Template:</small>
                                <div>{template_name}</div>
                            </div>
                            
                            <div class="mb-2">
                                <small class="text-muted">Next Run:</small>
                                <div>{next_run_text} {recurring_text}</div>
                            </div>
                            
                            <div class="mb-3">
                                <small class="text-muted">Last Updated:</small>
                                <div>{campaign.updated_at.strftime('%Y-%m-%d %H:%M')}</div>
                            </div>
                            
                            <div class="d-flex justify-content-between">
                                <div>
                                    <a href="/campaigns/{campaign.id}" class="btn btn-sm btn-outline-primary">
                                        <i class="fas fa-eye"></i> View
                                    </a>
                                    <a href="/campaigns/{campaign.id}/edit" class="btn btn-sm btn-outline-secondary">
                                        <i class="fas fa-edit"></i> Edit
                                    </a>
                                </div>
                                <div>
                                    <form method="POST" action="/campaigns/{campaign.id}/run" class="d-inline">
                                        <button type="submit" class="btn btn-sm btn-success">
                                            <i class="fas fa-play"></i> Run
                                        </button>
                                    </form>
                                    <button class="btn btn-sm btn-danger" onclick="confirmDelete({campaign.id}, '{campaign.name}')">
                                        <i class="fas fa-trash"></i>
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            """
    else:
        html += """
                <div class="col-12">
                    <div class="card">
                        <div class="card-body text-center py-5">
                            <i class="fas fa-bullhorn fa-5x text-muted mb-3"></i>
                            <h4>No Campaigns Found</h4>
                            <p>You haven't created any campaigns yet. Click the button below to create your first campaign.</p>
                            <a href="/campaigns/create" class="btn btn-primary">
                                <i class="fas fa-plus"></i> Create Campaign
                            </a>
                        </div>
                    </div>
                </div>
        """
    
    html += """
            </div>
            
            <!-- Delete Confirmation Modal -->
            <div class="modal fade" id="deleteModal" tabindex="-1" aria-hidden="true">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header bg-danger text-white">
                            <h5 class="modal-title">Confirm Delete</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                        </div>
                        <div class="modal-body">
                            Are you sure you want to delete the campaign <span id="campaignName"></span>?
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <form id="deleteForm" method="POST">
                                <button type="submit" class="btn btn-danger">Delete</button>
                            </form>
                        </div>
                    </div>
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
        
        <script>
            function confirmDelete(id, name) {
                document.getElementById('deleteForm').action = `/campaigns/${id}/delete`;
                document.getElementById('campaignName').textContent = name;
                new bootstrap.Modal(document.getElementById('deleteModal')).show();
            }
        </script>
    </body>
    </html>
    """
    
    return make_response(html)

@bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """Create a new campaign"""
    if request.method == 'POST':
        name = request.form.get('name')
        template_id = request.form.get('template_id')
        description = request.form.get('description')
        db_path = request.form.get('db_path') or current_app.config['DEFAULT_DB_PATH']
        filter_conditions = request.form.get('filter_conditions')
        order_status = request.form.get('order_status')
        recipient_limit = request.form.get('recipient_limit')
        force_flag = 'force_flag' in request.form
        
        # Parse campaign variables
        variables = {}
        for key, value in request.form.items():
            if key.startswith('var_'):
                var_name = key[4:]  # Remove 'var_' prefix
                variables[var_name] = value
        
        # Check required fields
        if not name or not template_id:
            flash('Name and Template are required.', 'danger')
            templates = Template.query.filter_by(is_active=True).all()
            return render_template('campaigns/create.html', templates=templates)
        
        # Create campaign
        campaign = Campaign(
            name=name,
            template_id=template_id,
            description=description,
            db_path=db_path,
            filter_conditions=filter_conditions,
            order_status=order_status,
            recipient_limit=recipient_limit if recipient_limit else None,
            force_flag=force_flag,
            status='draft'
        )
        
        # Set variables
        campaign.variables = variables
        
        # Check if it's a scheduled campaign
        scheduled_time = request.form.get('scheduled_time')
        is_recurring = 'is_recurring' in request.form
        recurrence_pattern = request.form.get('recurrence_pattern')
        
        if scheduled_time:
            try:
                # Parse scheduled time
                scheduled_time = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
                campaign.scheduled_time = scheduled_time
                campaign.status = 'scheduled'
                campaign.next_run = scheduled_time
                
                # Handle recurrence
                if is_recurring and recurrence_pattern:
                    campaign.is_recurring = True
                    campaign.recurrence_pattern = recurrence_pattern
                    
                    # Additional recurrence data
                    recurrence_data = {}
                    
                    if recurrence_pattern == 'weekly':
                        days = request.form.getlist('recurrence_days')
                        recurrence_data['days'] = days
                    elif recurrence_pattern == 'monthly':
                        day_of_month = request.form.get('day_of_month')
                        recurrence_data['day_of_month'] = day_of_month
                    
                    campaign.recurrence_data = json.dumps(recurrence_data)
            except ValueError:
                flash('Invalid scheduled time format.', 'danger')
                templates = Template.query.filter_by(is_active=True).all()
                return render_template('campaigns/create.html', templates=templates)
        
        db.session.add(campaign)
        db.session.commit()
        
        # Schedule the campaign if it's scheduled
        if campaign.status == 'scheduled':
            schedule_campaign_job(campaign)
            flash('Campaign scheduled successfully.', 'success')
        else:
            flash('Campaign created successfully.', 'success')
        
        return redirect(url_for('campaigns.index'))
    
    # GET request
    templates = Template.query.filter_by(is_active=True).all()
    return render_template('campaigns/create.html', templates=templates)

@bp.route('/<int:id>')
@login_required
def view(id):
    """View campaign details"""
    campaign = Campaign.query.get_or_404(id)
    logs = campaign.logs.order_by(CampaignLog.created_at.desc()).all()
    return render_template('campaigns/view.html', campaign=campaign, logs=logs)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a campaign"""
    campaign = Campaign.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        db_path = request.form.get('db_path') or current_app.config['DEFAULT_DB_PATH']
        filter_conditions = request.form.get('filter_conditions')
        order_status = request.form.get('order_status')
        recipient_limit = request.form.get('recipient_limit')
        force_flag = 'force_flag' in request.form
        is_active = 'is_active' in request.form
        
        # Parse campaign variables
        variables = {}
        for key, value in request.form.items():
            if key.startswith('var_'):
                var_name = key[4:]  # Remove 'var_' prefix
                variables[var_name] = value
        
        # Check required fields
        if not name:
            flash('Name is required.', 'danger')
            templates = Template.query.filter_by(is_active=True).all()
            return render_template('campaigns/edit.html', campaign=campaign, templates=templates)
        
        # Update campaign
        campaign.name = name
        campaign.description = description
        campaign.db_path = db_path
        campaign.filter_conditions = filter_conditions
        campaign.order_status = order_status
        campaign.recipient_limit = recipient_limit if recipient_limit else None
        campaign.force_flag = force_flag
        campaign.is_active = is_active
        
        # Set variables
        campaign.variables = variables
        
        # Check if it's a scheduled campaign
        scheduled_time = request.form.get('scheduled_time')
        is_recurring = 'is_recurring' in request.form
        recurrence_pattern = request.form.get('recurrence_pattern')
        
        # If campaign was already scheduled, unschedule it
        if campaign.status == 'scheduled':
            try:
                scheduler.remove_job(f'campaign_{campaign.id}')
            except Exception:
                pass
        
        if scheduled_time:
            try:
                # Parse scheduled time
                scheduled_time = datetime.strptime(scheduled_time, '%Y-%m-%dT%H:%M')
                campaign.scheduled_time = scheduled_time
                campaign.status = 'scheduled'
                campaign.next_run = scheduled_time
                
                # Handle recurrence
                if is_recurring and recurrence_pattern:
                    campaign.is_recurring = True
                    campaign.recurrence_pattern = recurrence_pattern
                    
                    # Additional recurrence data
                    recurrence_data = {}
                    
                    if recurrence_pattern == 'weekly':
                        days = request.form.getlist('recurrence_days')
                        recurrence_data['days'] = days
                    elif recurrence_pattern == 'monthly':
                        day_of_month = request.form.get('day_of_month')
                        recurrence_data['day_of_month'] = day_of_month
                    
                    campaign.recurrence_data = json.dumps(recurrence_data)
                else:
                    campaign.is_recurring = False
                    campaign.recurrence_pattern = None
                    campaign.recurrence_data = None
            except ValueError:
                flash('Invalid scheduled time format.', 'danger')
                templates = Template.query.filter_by(is_active=True).all()
                return render_template('campaigns/edit.html', campaign=campaign, templates=templates)
        else:
            campaign.scheduled_time = None
            campaign.status = 'draft'
            campaign.next_run = None
            campaign.is_recurring = False
            campaign.recurrence_pattern = None
            campaign.recurrence_data = None
        
        db.session.commit()
        
        # Schedule the campaign if it's scheduled
        if campaign.status == 'scheduled':
            schedule_campaign_job(campaign)
            flash('Campaign updated and scheduled successfully.', 'success')
        else:
            flash('Campaign updated successfully.', 'success')
        
        return redirect(url_for('campaigns.index'))
    
    # GET request
    templates = Template.query.filter_by(is_active=True).all()
    return render_template('campaigns/edit.html', campaign=campaign, templates=templates)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a campaign"""
    campaign = Campaign.query.get_or_404(id)
    
    # Unschedule if it's scheduled
    if campaign.status == 'scheduled':
        try:
            scheduler.remove_job(f'campaign_{campaign.id}')
        except Exception:
            pass
    
    # Delete the campaign
    db.session.delete(campaign)
    db.session.commit()
    
    flash('Campaign deleted successfully.', 'success')
    return redirect(url_for('campaigns.index'))

@bp.route('/<int:id>/run', methods=['POST'])
@login_required
def run(id):
    """Run a campaign immediately"""
    campaign = Campaign.query.get_or_404(id)
    
    # Update campaign status
    campaign.status = 'running'
    db.session.commit()
    
    # Run the campaign in a background thread
    execute_campaign(campaign.id)
    
    flash('Campaign execution started.', 'success')
    return redirect(url_for('campaigns.view', id=id))

def schedule_campaign_job(campaign):
    """Schedule a campaign for execution"""
    job_id = f'campaign_{campaign.id}'
    
    # Remove existing job if any
    try:
        scheduler.remove_job(job_id)
    except Exception:
        pass
    
    # Schedule the job
    if campaign.is_recurring:
        if campaign.recurrence_pattern == 'daily':
            scheduler.add_job(
                id=job_id,
                func=execute_campaign,
                args=[campaign.id],
                trigger='cron',
                hour=campaign.scheduled_time.hour,
                minute=campaign.scheduled_time.minute
            )
        elif campaign.recurrence_pattern == 'weekly':
            recurrence_data = json.loads(campaign.recurrence_data or '{}')
            days = recurrence_data.get('days', [])
            
            day_map = {
                'monday': 0, 'tuesday': 1, 'wednesday': 2, 'thursday': 3,
                'friday': 4, 'saturday': 5, 'sunday': 6
            }
            
            day_of_week = ','.join(str(day_map.get(day.lower(), 0)) for day in days)
            
            scheduler.add_job(
                id=job_id,
                func=execute_campaign,
                args=[campaign.id],
                trigger='cron',
                day_of_week=day_of_week,
                hour=campaign.scheduled_time.hour,
                minute=campaign.scheduled_time.minute
            )
        elif campaign.recurrence_pattern == 'monthly':
            recurrence_data = json.loads(campaign.recurrence_data or '{}')
            day_of_month = recurrence_data.get('day_of_month', 1)
            
            scheduler.add_job(
                id=job_id,
                func=execute_campaign,
                args=[campaign.id],
                trigger='cron',
                day=day_of_month,
                hour=campaign.scheduled_time.hour,
                minute=campaign.scheduled_time.minute
            )
    else:
        # One-time schedule
        scheduler.add_job(
            id=job_id,
            func=execute_campaign,
            args=[campaign.id],
            trigger='date',
            run_date=campaign.scheduled_time
        )

def execute_campaign(campaign_id):
    """Execute a campaign"""
    # Get the campaign
    with current_app.app_context():
        campaign = Campaign.query.get(campaign_id)
        if not campaign:
            return
        
        # Update campaign status
        campaign.status = 'running'
        campaign.last_run = datetime.now()
        db.session.commit()
        
        # Get template
        template = Template.query.get(campaign.template_id)
        if not template:
            # Log error
            log = CampaignLog(
                campaign_id=campaign.id,
                status='failure',
                error_message='Template not found'
            )
            db.session.add(log)
            campaign.status = 'failed'
            db.session.commit()
            return
        
        # Execute the campaign
        try:
            # Parameters for sending
            params = {
                'db_path': campaign.db_path,
                'content_sid': template.template_sid,
                'content_variables': campaign.variables,
                'filter_conditions': campaign.filter_conditions,
                'order_status': campaign.order_status,
                'limit': campaign.recipient_limit,
                'force': campaign.force_flag,
                'dry_run': False
            }
            
            # Send messages
            result = send_bulk_messages(**params)
            
            # Create log entry
            log = CampaignLog(
                campaign_id=campaign.id,
                status='success' if result.get('success', False) else 'failure',
                recipients_total=result.get('total', 0),
                recipients_success=result.get('successful', 0),
                recipients_failed=result.get('failed', 0),
                report_path=result.get('report_path'),
                execution_time=result.get('elapsed_time', 0),
                error_message=result.get('error')
            )
            db.session.add(log)
            
            # Update campaign status
            campaign.status = 'completed'
            
            # Calculate next run time if it's recurring
            if campaign.is_recurring:
                # Set next run time (simplified logic, actual logic would be more complex)
                # In a real app, you'd need to calculate this based on recurrence pattern
                campaign.status = 'scheduled'
            
        except Exception as e:
            # Log error
            log = CampaignLog(
                campaign_id=campaign.id,
                status='failure',
                error_message=str(e)
            )
            db.session.add(log)
            campaign.status = 'failed'
        
        # Save changes
        db.session.commit() 