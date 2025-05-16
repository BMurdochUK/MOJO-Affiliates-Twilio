"""
Dashboard routes
"""
from flask import Blueprint, render_template, make_response
from flask_login import login_required
from mojo_web import db
from mojo_web.models import Template, Campaign, CampaignLog

bp = Blueprint('dashboard', __name__)

@bp.route('/')
@login_required
def index():
    """Dashboard homepage"""
    # Get dashboard statistics
    stats = {
        'templates': Template.query.count(),
        'campaigns': Campaign.query.count(),
        'completed_campaigns': Campaign.query.filter_by(status='completed').count(),
        'scheduled_campaigns': Campaign.query.filter_by(status='scheduled').count()
    }
    
    # Get recent campaign logs
    recent_logs = CampaignLog.query.order_by(CampaignLog.created_at.desc()).limit(5).all()
    
    # Get upcoming scheduled campaigns
    upcoming_campaigns = Campaign.query.filter_by(status='scheduled').order_by(Campaign.next_run).limit(5).all()
    
    # Basic dashboard HTML
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Dashboard - MOJO WhatsApp Manager</title>
        
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
            
            .card-stats {
                transition: transform 0.3s;
                cursor: pointer;
            }
            
            .card-stats:hover {
                transform: translateY(-5px);
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
                <a href="/auth/logout" class="logout-btn">
                    <i class="fas fa-sign-out-alt"></i> Logout
                </a>
            </div>
        </nav>
        
        <!-- Main Content -->
        <div class="container mt-4">
            <div class="row mb-4">
                <div class="col">
                    <h2 class="mb-0">Dashboard</h2>
                    <p class="text-muted">Welcome to the MOJO WhatsApp Manager</p>
                </div>
            </div>
            
            <!-- Stats -->
            <div class="row mb-4">
    """
    
    # Add stats cards
    html += f"""
                <div class="col-md-3 mb-3">
                    <div class="card card-stats bg-primary text-white">
                        <div class="card-body text-center">
                            <h5 class="card-title"><i class="fas fa-file-alt"></i> Templates</h5>
                            <p class="display-4">{stats['templates']}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card card-stats bg-success text-white">
                        <div class="card-body text-center">
                            <h5 class="card-title"><i class="fas fa-bullhorn"></i> Campaigns</h5>
                            <p class="display-4">{stats['campaigns']}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card card-stats bg-info text-white">
                        <div class="card-body text-center">
                            <h5 class="card-title"><i class="fas fa-check-circle"></i> Completed</h5>
                            <p class="display-4">{stats['completed_campaigns']}</p>
                        </div>
                    </div>
                </div>
                <div class="col-md-3 mb-3">
                    <div class="card card-stats bg-warning text-white">
                        <div class="card-body text-center">
                            <h5 class="card-title"><i class="fas fa-clock"></i> Scheduled</h5>
                            <p class="display-4">{stats['scheduled_campaigns']}</p>
                        </div>
                    </div>
                </div>
    """
    
    html += """
            </div>
            
            <!-- Quick Actions -->
            <div class="row mb-4">
                <div class="col-12">
                    <div class="card">
                        <div class="card-body">
                            <h5 class="card-title mb-3">Quick Actions</h5>
                            <div class="row">
                                <div class="col-md-3 col-6 mb-3">
                                    <a href="/templates" class="btn btn-outline-primary w-100">
                                        <i class="fas fa-file-alt mb-2"></i><br>
                                        Templates
                                    </a>
                                </div>
                                <div class="col-md-3 col-6 mb-3">
                                    <a href="/campaigns" class="btn btn-outline-primary w-100">
                                        <i class="fas fa-bullhorn mb-2"></i><br>
                                        Campaigns
                                    </a>
                                </div>
                                <div class="col-md-3 col-6 mb-3">
                                    <a href="/contacts" class="btn btn-outline-primary w-100">
                                        <i class="fas fa-address-book mb-2"></i><br>
                                        Contacts
                                    </a>
                                </div>
                                <div class="col-md-3 col-6 mb-3">
                                    <a href="/reports" class="btn btn-outline-primary w-100">
                                        <i class="fas fa-chart-bar mb-2"></i><br>
                                        Reports
                                    </a>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="row">
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
    
    return make_response(html) 