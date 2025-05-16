"""
Reports routes for viewing message and campaign reports
"""
import os
import re
from datetime import datetime, timedelta
from flask import Blueprint, render_template, request, send_file, abort, current_app, make_response
from flask_login import login_required
from mojo_web import db
from mojo_web.models import Campaign, CampaignLog
import os
from twilio.rest import Client

bp = Blueprint('reports', __name__, url_prefix='/reports')

@bp.route('/')
@login_required
def index():
    """Reports dashboard showing message reports and campaign logs"""
    # Generate direct HTML
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reports - MOJO WhatsApp Manager</title>
        
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
            
            .nav-tabs .nav-link.active {
                background-color: white;
                color: var(--mojo-dark);
                font-weight: bold;
            }
            
            .nav-tabs .nav-link {
                color: var(--mojo-dark);
            }
            
            .card {
                border: none;
                box-shadow: 0 0.125rem 0.25rem rgba(0,0,0,0.075);
                margin-bottom: 1.5rem;
            }
            
            .card-header {
                background-color: var(--mojo-dark);
                color: white;
                font-weight: bold;
            }
            
            .card .card-body {
                text-center py-4;
            }
            
            .card-body h2 {
                margin-bottom: 5px;
            }
            
            /* Make all stat boxes the same height */
            .row .card {
                height: 100%;
            }
            
            .status-sent {
                color: #28a745;
            }
            
            .status-delivered {
                color: #28a745;
                font-weight: bold;
            }
            
            .status-read {
                color: #218838;
                font-weight: bold;
            }
            
            .status-failed, .status-undelivered {
                color: #dc3545;
            }
            
            .status-queued {
                color: #ffc107;
            }
            
            .refresh-button {
                position: fixed;
                bottom: 20px;
                right: 20px;
                z-index: 1000;
            }
            
            .message-tabs .nav-link {
                font-weight: bold;
                padding: 10px 20px;
            }
            
            .message-count {
                display: inline-block;
                background-color: var(--mojo-red);
                color: white;
                border-radius: 50%;
                padding: 2px 8px;
                font-size: 12px;
                margin-left: 5px;
            }
            
            .percentage {
                font-size: 14px;
                opacity: 0.8;
                margin-left: 5px;
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
                <div class="col">
                    <h2>Reports Dashboard</h2>
                    <p class="text-muted">View message delivery reports and campaign logs</p>
                </div>
            </div>
            
            <ul class="nav nav-tabs mb-4" id="reportsTabs" role="tablist">
                <li class="nav-item" role="presentation">
                    <button class="nav-link active" id="delivery-tab" data-bs-toggle="tab" data-bs-target="#delivery" type="button" role="tab" aria-controls="delivery" aria-selected="true">
                        <i class="fas fa-paper-plane"></i> Message Delivery
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="campaigns-tab" data-bs-toggle="tab" data-bs-target="#campaigns" type="button" role="tab" aria-controls="campaigns" aria-selected="false">
                        <i class="fas fa-bullhorn"></i> Campaign Logs
                    </button>
                </li>
                <li class="nav-item" role="presentation">
                    <button class="nav-link" id="files-tab" data-bs-toggle="tab" data-bs-target="#files" type="button" role="tab" aria-controls="files" aria-selected="false">
                        <i class="fas fa-file-alt"></i> Report Files
                    </button>
                </li>
            </ul>
            
            <div class="tab-content" id="reportsTabsContent">
                <!-- Delivery Reports Tab -->
                <div class="tab-pane fade show active" id="delivery" role="tabpanel" aria-labelledby="delivery-tab">
                    <div class="card">
                        <div class="card-header d-flex justify-content-between align-items-center">
                            <span>Recent Message Delivery</span>
                            <div>
                                <select id="timeRangeFilter" class="form-select form-select-sm" style="width: auto; display: inline-block;">
                                    <option value="24">Last 24 Hours</option>
                                    <option value="48">Last 48 Hours</option>
                                    <option value="168">Last 7 Days</option>
                                </select>
                            </div>
                        </div>
                        <div class="card-body">
                            <div class="row mb-4">
                                <div class="col-md-3">
                                    <div class="card bg-primary text-white">
                                        <div class="card-body text-center">
                                            <h5>Total Messages</h5>
                                            <h2 id="total-messages">...</h2>
                                            <small>All messages sent and received</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-info text-white">
                                        <div class="card-body text-center">
                                            <h5>Affiliate Responses</h5>
                                            <h2 id="inbound-messages">...</h2>
                                            <small>Incoming messages received from customers</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-secondary text-white">
                                        <div class="card-body text-center">
                                            <h5>Delivered</h5>
                                            <h2 id="delivered-messages">...</h2>
                                            <span id="delivered-percent" class="percentage">0%</span>
                                            <small>Outbound messages confirmed delivered to handset</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-success text-white">
                                        <div class="card-body text-center">
                                            <h5>Read</h5>
                                            <h2 id="read-messages">...</h2>
                                            <span id="read-percent" class="percentage">0%</span>
                                            <small>WhatsApp: Message opened by recipient</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <div class="row mb-4">
                                <div class="col-md-3">
                                    <div class="card bg-info text-white">
                                        <div class="card-body text-center">
                                            <h5>Sent</h5>
                                            <h2 id="sent-messages">...</h2>
                                            <span id="sent-percent" class="percentage">0%</span>
                                            <small>Messages accepted by upstream carrier</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-danger text-white">
                                        <div class="card-body text-center">
                                            <h5>Failed</h5>
                                            <h2 id="failed-messages">...</h2>
                                            <span id="failed-percent" class="percentage">0%</span>
                                            <small>Messages failed during processing</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-warning text-white">
                                        <div class="card-body text-center">
                                            <h5>Received</h5>
                                            <h2 id="received-messages">...</h2>
                                            <span id="received-percent" class="percentage">0%</span>
                                            <small>Inbound messages received and processed</small>
                                        </div>
                                    </div>
                                </div>
                                <div class="col-md-3">
                                    <div class="card bg-danger text-white">
                                        <div class="card-body text-center">
                                            <h5>Undelivered</h5>
                                            <h2 id="undelivered-messages">...</h2>
                                            <span id="undelivered-percent" class="percentage">0%</span>
                                            <small>Messages that couldn't be delivered</small>
                                        </div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Message tabs -->
                            <ul class="nav nav-tabs message-tabs mb-3" role="tablist">
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link active" id="outbound-tab" data-bs-toggle="tab" data-bs-target="#outbound-messages" type="button" role="tab" aria-controls="outbound-messages" aria-selected="true">
                                        Outbound Messages <span id="outbound-count" class="message-count">0</span>
                                    </button>
                                </li>
                                <li class="nav-item" role="presentation">
                                    <button class="nav-link" id="inbound-tab" data-bs-toggle="tab" data-bs-target="#inbound-messages" type="button" role="tab" aria-controls="inbound-messages" aria-selected="false">
                                        Affiliate Responses <span id="responses-count" class="message-count">0</span>
                                    </button>
                                </li>
                            </ul>
                            
                            <div class="tab-content">
                                <!-- Outbound Messages Tab -->
                                <div class="tab-pane fade show active" id="outbound-messages" role="tabpanel">
                                    <div class="table-responsive">
                                        <table class="table table-striped" id="delivery-table">
                                            <thead>
                                                <tr>
                                                    <th>Date</th>
                                                    <th>To</th>
                                                    <th>Buyer Username</th>
                                                    <th>Recipient</th>
                                                    <th>Order ID</th>
                                                    <th>Message Body</th>
                                                    <th>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody id="delivery-body">
                                                <tr>
                                                    <td colspan="8" class="text-center">Loading outbound message data...</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                                
                                <!-- Inbound Messages Tab -->
                                <div class="tab-pane fade" id="inbound-messages" role="tabpanel" aria-labelledby="inbound-tab">
                                    <div class="table-responsive">
                                        <table class="table table-striped" id="inbound-table">
                                            <thead>
                                                <tr>
                                                    <th>Date</th>
                                                    <th>From</th>
                                                    <th>Buyer Username</th>
                                                    <th>Recipient</th>
                                                    <th>Order ID</th>
                                                    <th>Message Body</th>
                                                    <th>Status</th>
                                                </tr>
                                            </thead>
                                            <tbody id="inbound-body">
                                                <tr>
                                                    <td colspan="7" class="text-center">Loading customer responses...</td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Campaign Logs Tab -->
                <div class="tab-pane fade" id="campaigns" role="tabpanel" aria-labelledby="campaigns-tab">
                    <div class="card">
                        <div class="card-header">
                            <span>Recent Campaign Logs</span>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Campaign</th>
                                            <th>Status</th>
                                            <th>Recipients</th>
                                            <th>Success</th>
                                            <th>Failed</th>
                                            <th>Time (s)</th>
                                            <th></th>
                                        </tr>
                                    </thead>
                                    <tbody>
    """
    
    # Add campaign logs
    campaign_logs = CampaignLog.query.order_by(CampaignLog.created_at.desc()).limit(20).all()
    
    if campaign_logs:
        for log in campaign_logs:
            status_class = "text-success" if log.status == "success" else "text-danger"
            success_rate = f"{(log.recipients_success / log.recipients_total * 100):.1f}%" if log.recipients_total > 0 else "0%"
            
            html += f"""
                                        <tr>
                                            <td>{log.created_at.strftime('%Y-%m-%d %H:%M')}</td>
                                            <td>{log.campaign.name if log.campaign else 'Unknown'}</td>
                                            <td class="{status_class}">{log.status}</td>
                                            <td>{log.recipients_total}</td>
                                            <td>{log.recipients_success} ({success_rate})</td>
                                            <td>{log.recipients_failed}</td>
                                            <td>{log.execution_time:.1f}s</td>
                                            <td>
                                                <a href="/reports/campaign/{log.campaign_id}" class="btn btn-sm btn-outline-primary">
                                                    <i class="fas fa-eye"></i>
                                                </a>
                                            </td>
                                        </tr>
            """
    else:
        html += """
                                        <tr>
                                            <td colspan="8" class="text-center">No campaign logs found.</td>
                                        </tr>
        """
    
    # Add file reports section
    html += """
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Report Files Tab -->
                <div class="tab-pane fade" id="files" role="tabpanel" aria-labelledby="files-tab">
                    <div class="card">
                        <div class="card-header">
                            <span>Message Report Files</span>
                        </div>
                        <div class="card-body">
                            <div class="table-responsive">
                                <table class="table table-striped">
                                    <thead>
                                        <tr>
                                            <th>Date</th>
                                            <th>Filename</th>
                                            <th>Status</th>
                                            <th>Type</th>
                                            <th></th>
                                        </tr>
                                    </thead>
                                    <tbody>
    """
    
    # Get file reports
    reports_dir = os.path.join(current_app.root_path, '..', 'reports')
    file_reports = []
    
    if os.path.exists(reports_dir):
        files = [f for f in os.listdir(reports_dir) if f.endswith('.txt')]
        
        for file in files:
            # Extract date from filename (format: message_report_*_DD-MM-YY_HH-MM-SS.txt)
            match = re.search(r'(\d{2}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', file)
            if match:
                date_str = match.group(1)
                try:
                    date = datetime.strptime(date_str, '%d-%m-%y_%H-%M-%S')
                    
                    # Extract status from filename if present
                    status_match = re.search(r'status_([A-Z]+)', file)
                    status = status_match.group(1) if status_match else None
                    
                    # Check if it's a dry run
                    is_dry_run = 'dry_run' in file
                    
                    file_reports.append({
                        'filename': file,
                        'date': date,
                        'status': status,
                        'is_dry_run': is_dry_run
                    })
                except Exception:
                    # Skip files with invalid date format
                    continue
        
        # Sort by date (newest first)
        file_reports.sort(key=lambda x: x['date'], reverse=True)
        
        # Limit to 20 most recent
        file_reports = file_reports[:20]
    
    if file_reports:
        for report in file_reports:
            run_type = "Dry Run" if report['is_dry_run'] else "Live Run"
            status_text = report['status'] if report['status'] else "Unknown"
            
            html += f"""
                                        <tr>
                                            <td>{report['date'].strftime('%Y-%m-%d %H:%M')}</td>
                                            <td>{report['filename']}</td>
                                            <td>{status_text}</td>
                                            <td>{run_type}</td>
                                            <td>
                                                <a href="/reports/view/{report['filename']}" class="btn btn-sm btn-outline-primary me-1">
                                                    <i class="fas fa-eye"></i>
                                                </a>
                                                <a href="/reports/download/{report['filename']}" class="btn btn-sm btn-outline-secondary">
                                                    <i class="fas fa-download"></i>
                                                </a>
                                            </td>
                                        </tr>
            """
    else:
        html += """
                                        <tr>
                                            <td colspan="5" class="text-center">No report files found.</td>
                                        </tr>
        """
    
    html += """
                                    </tbody>
                                </table>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Auto-refresh button -->
            <button class="btn btn-primary rounded-circle refresh-button" id="refreshButton" title="Refresh data">
                <i class="fas fa-sync-alt"></i>
            </button>
            
            <div class="row mt-4">
                <div class="col-md-12 text-center">
                    <p class="text-muted">MOJO WhatsApp Manager | Version 1.0</p>
                </div>
            </div>
        </div>
        
        <!-- Bootstrap JavaScript -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        
        <script>
            // Initialize page
            document.addEventListener('DOMContentLoaded', function() {
                let activeOutboundMessages = [];
                let activeInboundMessages = [];

                // Function to populate outbound messages table
                function renderOutboundTable() {
                    const outboundBody = document.getElementById('delivery-body');
                    outboundBody.innerHTML = ''; // Clear existing
                    let newHtml = '';
                    if (activeOutboundMessages.length === 0) {
                        newHtml = '<tr><td colspan="7" class="text-center">No outbound messages found for the selected time period.</td></tr>';
                    } else {
                        activeOutboundMessages.forEach(msg => {
                            const statusClass = getStatusClass(msg.status);
                            const date = new Date(msg.date_sent || msg.date_created);
                            const buyerUsername = msg.buyer_username ? 
                                `<a href="https://www.tiktok.com/@${msg.buyer_username}" target="_blank">@${msg.buyer_username}</a>` : '-';
                            newHtml += `
                                <tr>
                                    <td>${date.toLocaleString()}</td>
                                    <td>${msg.to}</td>
                                    <td>${buyerUsername}</td>
                                    <td>${msg.recipient || '-'}</td>
                                    <td>${msg.order_id || '-'}</td>
                                    <td>${msg.body.substring(0, 50)}${msg.body.length > 50 ? '...' : ''}</td>
                                    <td class="${statusClass}">${msg.status}</td>
                                </tr>
                            `;
                        });
                    }
                    outboundBody.innerHTML = newHtml;
                    setTimeout(() => { outboundBody.innerHTML = newHtml; }, 10); // Re-assert content
                    console.log("Rendered outbound table. HTML:", outboundBody.innerHTML.substring(0, 200) + "...");
                }

                // Function to populate inbound messages table
                function renderInboundTable() {
                    // Locate the parent container that holds the table
                    const tableContainer = document.querySelector('#inbound-messages .table-responsive');
                    if (!tableContainer) {
                        console.error("Could not find table container in #inbound-messages");
                        return;
                    }
                    
                    // Create completely new table HTML
                    let tableHtml = `
                        <table class="table table-striped" id="inbound-table">
                            <thead>
                                <tr>
                                    <th>Date</th>
                                    <th>From</th>
                                    <th>Buyer Username</th>
                                    <th>Recipient</th>
                                    <th>Order ID</th>
                                    <th>Message Body</th>
                                    <th>Status</th>
                                </tr>
                            </thead>
                            <tbody id="inbound-body">
                    `;
                    
                    if (activeInboundMessages.length === 0) {
                        tableHtml += '<tr><td colspan="7" class="text-center">No affiliate responses found for the selected time period.</td></tr>';
                    } else {
                        activeInboundMessages.forEach(msg => {
                            const statusClass = getStatusClass(msg.status);
                            const date = new Date(msg.date_sent || msg.date_created);
                            const buyerUsername = msg.buyer_username ? 
                                `<a href="https://www.tiktok.com/@${msg.buyer_username}" target="_blank">@${msg.buyer_username}</a>` : '-';
                            tableHtml += `
                                <tr>
                                    <td>${date.toLocaleString()}</td>
                                    <td>${msg.from}</td>
                                    <td>${buyerUsername}</td>
                                    <td>${msg.recipient || '-'}</td>
                                    <td>${msg.order_id || '-'}</td>
                                    <td>${msg.body.substring(0, 50)}${msg.body.length > 50 ? '...' : ''}</td>
                                    <td class="${statusClass}">${msg.status}</td>
                                </tr>
                            `;
                        });
                    }
                    
                    tableHtml += `
                            </tbody>
                        </table>
                    `;
                    
                    // Replace the entire table HTML
                    tableContainer.innerHTML = tableHtml;
                    
                    // Log the new table HTML for debugging
                    console.log("Completely rebuilt inbound table. Container HTML:", tableContainer.innerHTML.substring(0, 200) + "...");
                    
                    // Force a repaint/reflow - extreme measures
                    setTimeout(() => {
                        const tempNode = document.createTextNode('');
                        tableContainer.appendChild(tempNode);
                        tableContainer.removeChild(tempNode);
                        console.log("Forced DOM refresh");
                    }, 20);
                }

                // Function to load message delivery data
                function loadMessageData(timeRange) {
                    fetch('/reports/api/deliverability?hours=' + timeRange)
                        .then(response => response.json())
                        .then(data => {
                            // Update stats (this part remains the same)
                            document.getElementById('total-messages').textContent = data.stats.total;
                            document.getElementById('delivered-messages').textContent = data.stats.delivered;
                            document.getElementById('delivered-percent').textContent = `(${data.stats.delivered_pct}%)`;
                            document.getElementById('sent-messages').textContent = data.stats.sent;
                            document.getElementById('sent-percent').textContent = `(${data.stats.sent_pct}%)`;
                            document.getElementById('failed-messages').textContent = data.stats.failed;
                            document.getElementById('failed-percent').textContent = `(${data.stats.failed_pct}%)`;
                            document.getElementById('read-messages').textContent = data.stats.read;
                            document.getElementById('read-percent').textContent = `(${data.stats.read_pct}%)`;
                            document.getElementById('received-messages').textContent = data.stats.received;
                            document.getElementById('received-percent').textContent = `(${data.stats.received_pct}%)`;
                            document.getElementById('undelivered-messages').textContent = data.stats.undelivered;
                            document.getElementById('undelivered-percent').textContent = `(${data.stats.undelivered_pct}%)`;
                            document.getElementById('inbound-messages').textContent = data.stats.inbound;

                            // Filter messages for outbound and inbound tables
                            activeOutboundMessages = data.messages.filter(msg => msg.direction === 'outbound-api');
                            console.log("Filtered outbound messages (activeOutboundMessages):", activeOutboundMessages);

                            activeInboundMessages = data.inbound_messages.filter(msg => msg.direction === 'inbound');
                            console.log("Filtered inbound messages (activeInboundMessages):", activeInboundMessages);

                            // Update counts in tabs
                            document.getElementById('outbound-count').textContent = activeOutboundMessages.length;
                            document.getElementById('responses-count').textContent = activeInboundMessages.length;

                            // Determine which tab is currently active and render its table
                            // This is important for the initial load and auto-refresh
                            if (document.getElementById('outbound-tab').classList.contains('active')) {
                                renderOutboundTable();
                            } else if (document.getElementById('inbound-tab').classList.contains('active')) {
                                renderInboundTable();
                            }

                        })
                        .catch(error => {
                            console.error('Error fetching data:', error);
                            document.getElementById('delivery-body').innerHTML = 
                                '<tr><td colspan="7" class="text-center text-danger">Error loading message data. Please try again.</td></tr>';
                            document.getElementById('inbound-body').innerHTML = 
                                '<tr><td colspan="7" class="text-center text-danger">Error loading message data. Please try again.</td></tr>';
                        });
                }
            
                // Helper function to get status class
                function getStatusClass(status) {
                    switch(status.toLowerCase()) {
                        case 'delivered':
                            return 'status-delivered';
                        case 'sent':
                            return 'status-sent';
                        case 'queued':
                        case 'sending':
                        case 'processing':
                            return 'status-queued';
                        case 'failed':
                        case 'undelivered':
                            return 'status-failed';
                        case 'read':
                            return 'status-read';
                        case 'received':
                            return 'status-sent';
                        default:
                            return '';
                    }
                }
            
                // Load initial data
                const timeRange = document.getElementById('timeRangeFilter').value;
                loadMessageData(timeRange);
                
                // Set up change listener for time range filter
                document.getElementById('timeRangeFilter').addEventListener('change', function() {
                    loadMessageData(this.value);
                });
                
                // Set up auto-refresh button
                document.getElementById('refreshButton').addEventListener('click', function() {
                    this.classList.add('rotate-animation');
                    const timeRange = document.getElementById('timeRangeFilter').value;
                    loadMessageData(timeRange);
                    setTimeout(() => {
                        this.classList.remove('rotate-animation');
                    }, 1000);
                });
                
                // Set up auto-refresh every 120 seconds
                setInterval(function() {
                    const timeRange = document.getElementById('timeRangeFilter').value;
                    loadMessageData(timeRange);
                    const refreshButton = document.getElementById('refreshButton');
                    refreshButton.classList.add('rotate-animation');
                    setTimeout(() => {
                        refreshButton.classList.remove('rotate-animation');
                    }, 1000);
                }, 120000);

                // --- NEW DIAGNOSTIC CODE FOR TABS ---
                const outboundTabButton = document.getElementById('outbound-tab');
                const inboundTabButton = document.getElementById('inbound-tab');
                const outboundPane = document.getElementById('outbound-messages');
                const inboundPane = document.getElementById('inbound-messages');

                if (outboundTabButton && outboundPane) {
                    outboundTabButton.addEventListener('show.bs.tab', function (event) {
                        console.warn('Event: show.bs.tab for Outbound. Target:', event.target.id, 'RelatedTarget:', event.relatedTarget ? event.relatedTarget.id : 'null');
                    });
                    outboundTabButton.addEventListener('shown.bs.tab', function (event) {
                        console.warn('Event: shown.bs.tab for Outbound. Target:', event.target.id, 'RelatedTarget:', event.relatedTarget ? event.relatedTarget.id : 'null');
                        outboundPane.classList.add('active', 'show');
                        if (inboundPane) inboundPane.classList.remove('active', 'show');
                        renderOutboundTable();
                        console.log('Outbound Pane classes after shown:', outboundPane.className);
                        if (inboundPane) console.log('Inbound Pane classes after Outbound shown:', inboundPane.className);
                    });
                }

                if (inboundTabButton && inboundPane) {
                    inboundTabButton.addEventListener('show.bs.tab', function (event) {
                        console.warn('Event: show.bs.tab for Inbound. Target:', event.target.id, 'RelatedTarget:', event.relatedTarget ? event.relatedTarget.id : 'null');
                    });
                    inboundTabButton.addEventListener('shown.bs.tab', function (event) {
                        console.warn('Event: shown.bs.tab for Inbound. Target:', event.target.id, 'RelatedTarget:', event.relatedTarget ? event.relatedTarget.id : 'null');
                        inboundPane.classList.add('active', 'show');
                        if (outboundPane) outboundPane.classList.remove('active', 'show');
                        renderInboundTable();
                        
                        // BRUTE FORCE APPROACH - Create a completely new element to display inbound messages
                        console.log("Implementing brute force display solution...");
                        
                        // Create a container div with forced visibility
                        const forceContainer = document.createElement('div');
                        forceContainer.id = 'force-inbound-container';
                        forceContainer.style.cssText = `
                            position: relative;
                            top: 0;
                            left: 0;
                            width: 100%;
                            background-color: white;
                            z-index: 1000;
                            padding: 20px;
                            border: 2px solid #E60517;
                            box-shadow: 0 0 10px rgba(0,0,0,0.2);
                            margin-top: 10px;
                        `;
                        
                        // Create a table with simple styling
                        let tableHTML = `
                            <h4>Affiliate Responses (Force Display)</h4>
                            <table style="width:100%; border-collapse: collapse; margin-top: 10px;">
                                <thead>
                                    <tr style="background-color: #f2f2f2;">
                                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Date</th>
                                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">From</th>
                                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Buyer Username</th>
                                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Message</th>
                                        <th style="padding: 8px; text-align: left; border: 1px solid #ddd;">Status</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        
                        // Add each message to the table
                        if (activeInboundMessages && activeInboundMessages.length > 0) {
                            activeInboundMessages.forEach(msg => {
                                const date = new Date(msg.date_sent || msg.date_created);
                                const buyerUsername = msg.buyer_username ? 
                                    `<a href="https://www.tiktok.com/@${msg.buyer_username}" target="_blank" style="color: #E60517;">@${msg.buyer_username}</a>` : '-';
                                
                                tableHTML += `
                                    <tr style="border-bottom: 1px solid #ddd;">
                                        <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">${date.toLocaleString()}</td>
                                        <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">${msg.from}</td>
                                        <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">${buyerUsername}</td>
                                        <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">${msg.body.substring(0, 50)}${msg.body.length > 50 ? '...' : ''}</td>
                                        <td style="padding: 8px; text-align: left; border: 1px solid #ddd;">${msg.status}</td>
                                    </tr>
                                `;
                            });
                        } else {
                            tableHTML += `
                                <tr>
                                    <td colspan="5" style="padding: 8px; text-align: center; border: 1px solid #ddd;">No affiliate responses found</td>
                                </tr>
                            `;
                        }
                        
                        tableHTML += `
                                </tbody>
                            </table>
                        `;
                        
                        forceContainer.innerHTML = tableHTML;
                        
                        // Remove any existing forced container
                        const existingContainer = document.getElementById('force-inbound-container');
                        if (existingContainer) {
                            existingContainer.remove();
                        }
                        
                        // Insert the new container right after the tab content
                        const tabContent = document.getElementById('delivery');
                        if (tabContent) {
                            tabContent.appendChild(forceContainer);
                            console.log("Force display container added to the DOM");
                        } else {
                            console.error("Could not find #delivery element to append force container");
                            // Plan B: append to the inbound-messages div
                            inboundPane.appendChild(forceContainer);
                        }
                        
                        console.log('Inbound Pane classes after shown:', inboundPane.className);
                        if (outboundPane) console.log('Outbound Pane classes after Inbound shown:', outboundPane.className);
                    });
                    
                    // Also handle cleanup when switching back to outbound tab
                    if (outboundTabButton) {
                        outboundTabButton.addEventListener('shown.bs.tab', function(event) {
                            // Remove the forced container when switching to outbound tab
                            const existingContainer = document.getElementById('force-inbound-container');
                            if (existingContainer) {
                                existingContainer.remove();
                                console.log("Force display container removed");
                            }
                        });
                    }
                }
                // --- END NEW DIAGNOSTIC CODE ---
            });
            
            // Add rotation animation for refresh button
            document.head.insertAdjacentHTML('beforeend', `
                <style>
                    @keyframes rotate {
                        from { transform: rotate(0deg); }
                        to { transform: rotate(360deg); }
                    }
                    .rotate-animation {
                        animation: rotate 1s linear;
                    }
                </style>
            `);
        </script>
    </body>
    </html>
    """
    
    return make_response(html)

@bp.route('/api/deliverability')
@login_required
def api_deliverability():
    """API endpoint to get message delivery data from Twilio"""
    # Get time range parameter (in hours)
    hours = request.args.get('hours', '24')
    try:
        hours = int(hours)
    except ValueError:
        hours = 24
    
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(hours=hours)
    
    # For today's date (for percentage calculations)
    today_start = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    
    # Log for debugging
    current_app.logger.debug(f"Getting messages from {start_date} to {end_date}")
    
    # Initialize Twilio client
    account_sid = current_app.config.get('TWILIO_ACCOUNT_SID')
    auth_token = current_app.config.get('TWILIO_AUTH_TOKEN')
    
    if not account_sid or not auth_token:
        return {
            'error': 'Twilio credentials not configured',
            'messages': [],
            'inbound_messages': [],
            'stats': {
                'total': 0,
                'delivered': 0,
                'delivered_pct': 0,
                'failed': 0,
                'received': 0,
                'received_pct': 0,
                'read': 0,
                'read_pct': 0,
                'undelivered_pct': 0,
                'inbound': 0
            }
        }
    
    client = Client(account_sid, auth_token)
    
    try:
        # Get messages within the date range
        messages = client.messages.list(
            date_sent_after=start_date,
            date_sent_before=end_date,
            limit=100
        )
        
        # Log basic info for debugging
        current_app.logger.debug(f"Found {len(messages)} total messages from Twilio")
        
        # Debug: Log all message directions to see what's available
        directions = [msg.direction for msg in messages]
        current_app.logger.info(f"Message directions found: {set(directions)}")
        
        # Count by status
        total = len(messages)
        delivered = sum(1 for msg in messages if msg.status == 'delivered')
        sent = sum(1 for msg in messages if msg.status == 'sent')
        failed = sum(1 for msg in messages if msg.status == 'failed')
        undelivered = sum(1 for msg in messages if msg.status == 'undelivered')
        received = sum(1 for msg in messages if msg.status == 'received')
        read = sum(1 for msg in messages if msg.status == 'read')
        
        # Count by direction
        inbound = sum(1 for msg in messages if msg.direction == 'inbound')
        outbound = sum(1 for msg in messages if msg.direction == 'outbound-api')
        
        # Log direction counts
        current_app.logger.info(f"Direction counts - inbound: {inbound}, outbound: {outbound}")
        
        # Today's counts for percentage calculations
        today_messages = [msg for msg in messages if msg.date_created and msg.date_created.replace(tzinfo=None) >= today_start]
        today_total = len(today_messages)
        today_delivered = sum(1 for msg in today_messages if msg.status == 'delivered')
        today_sent = sum(1 for msg in today_messages if msg.status == 'sent')
        today_failed = sum(1 for msg in today_messages if msg.status == 'failed')
        today_received = sum(1 for msg in today_messages if msg.status == 'received')
        today_read = sum(1 for msg in today_messages if msg.status == 'read')
        today_undelivered = sum(1 for msg in today_messages if msg.status == 'undelivered')
        
        # Calculate percentages
        delivered_pct = (today_delivered / today_total * 100) if today_total > 0 else 0
        sent_pct = (today_sent / today_total * 100) if today_total > 0 else 0
        failed_pct = (today_failed / today_total * 100) if today_total > 0 else 0
        received_pct = (today_received / today_total * 100) if today_total > 0 else 0
        read_pct = (today_read / today_total * 100) if today_total > 0 else 0
        undelivered_pct = (today_undelivered / today_total * 100) if today_total > 0 else 0
        
        # Log status and direction counts for debugging
        current_app.logger.debug(f"Message status counts - delivered: {delivered}, failed: {failed}, queued: {sent}, received: {received}")
        current_app.logger.debug(f"Message direction counts - outbound: {outbound}, inbound: {inbound}")
        
        # Log a sample message for debugging
        if messages:
            sample = messages[0]
            current_app.logger.debug(f"Sample message - SID: {sample.sid}, Status: {sample.status}, Direction: {sample.direction}")
            current_app.logger.debug(f"From: {sample.from_}, To: {sample.to}, Body: {sample.body}")
        
        # Format messages for JSON response
        formatted_messages = []
        inbound_messages = []
        
        # Debug counts before processing
        current_app.logger.info(f"Messages by direction before processing - inbound: {sum(1 for msg in messages if msg.direction == 'inbound')}, outbound-api: {sum(1 for msg in messages if msg.direction == 'outbound-api')}")
        
        # Connect to the database - use SQLAlchemy session
        import sqlite3
        conn = sqlite3.connect('affiliates.db')
        conn.row_factory = sqlite3.Row
        
        for msg in messages:
            # Debug: Log each message direction for troubleshooting
            current_app.logger.debug(f"Processing message {msg.sid} - Direction: {msg.direction}, Status: {msg.status}")
            
            # Skip messages that aren't inbound or outbound-api
            if msg.direction not in ['inbound', 'outbound-api']:
                current_app.logger.debug(f"Skipping message {msg.sid} with direction {msg.direction}")
                continue
                
            # Get the phone number, stripping off any whatsapp: prefix
            phone_number = (msg.to if msg.direction == 'outbound-api' else msg.from_)
            if phone_number:
                # Strip the whatsapp: prefix and any leading +
                stripped_phone = phone_number.replace('whatsapp:', '').replace('+', '')
                
                try:
                    # Query for buyer information
                    cursor = conn.cursor()
                    cursor.execute(
                        "SELECT buyer_username, order_id, recipient FROM orders WHERE phone_number = ? OR phone_number = ? OR phone_number = ? ORDER BY last_updated DESC LIMIT 1",
                        (stripped_phone, phone_number, '+' + stripped_phone)
                    )
                    buyer_info = cursor.fetchone()
                    
                    buyer_username = buyer_info['buyer_username'] if buyer_info else None
                    order_id = buyer_info['order_id'] if buyer_info else None
                    recipient = buyer_info['recipient'] if buyer_info else None
                    
                    message_data = {
                        'sid': msg.sid,
                        'to': msg.to,
                        'from': msg.from_,
                        'body': msg.body,
                        'status': msg.status,
                        'direction': msg.direction,
                        'error_code': msg.error_code,
                        'error_message': msg.error_message,
                        'date_created': msg.date_created.isoformat() if msg.date_created else None,
                        'date_sent': msg.date_sent.isoformat() if msg.date_sent else None,
                        'date_updated': msg.date_updated.isoformat() if msg.date_updated else None,
                        'price': msg.price,
                        'buyer_username': buyer_username,
                        'recipient': recipient,
                        'order_id': order_id
                    }
                    
                    # Add to appropriate list based on direction - strictly enforce the direction check
                    if msg.direction == 'inbound':
                        inbound_messages.append(message_data)
                        current_app.logger.debug(f"Added message {msg.sid} to inbound_messages")
                    elif msg.direction == 'outbound-api':
                        formatted_messages.append(message_data)
                        current_app.logger.debug(f"Added message {msg.sid} to formatted_messages")
                
                except Exception as e:
                    current_app.logger.debug(f"DEBUG ERROR: {str(e)}")
                    # Add the message even if we can't get buyer info
                    message_data = {
                        'sid': msg.sid,
                        'to': msg.to,
                        'from': msg.from_,
                        'body': msg.body,
                        'status': msg.status,
                        'direction': msg.direction,
                        'error_code': msg.error_code,
                        'error_message': msg.error_message,
                        'date_created': msg.date_created.isoformat() if msg.date_created else None,
                        'date_sent': msg.date_sent.isoformat() if msg.date_sent else None,
                        'date_updated': msg.date_updated.isoformat() if msg.date_updated else None,
                        'price': msg.price,
                        'buyer_username': None,
                        'recipient': None,
                        'order_id': None
                    }
                    
                    # Add to appropriate list based on direction - strictly enforce the direction check
                    if msg.direction == 'inbound':
                        inbound_messages.append(message_data)
                        current_app.logger.debug(f"Added message {msg.sid} to inbound_messages (error handling)")
                    elif msg.direction == 'outbound-api':
                        formatted_messages.append(message_data)
                        current_app.logger.debug(f"Added message {msg.sid} to formatted_messages (error handling)")
                    else:
                        current_app.logger.debug(f"Message {msg.sid} with direction {msg.direction} not added to any list (error handling)")
        
        # Close the database connection
        conn.close()
        
        # Log final counts for debugging
        current_app.logger.info(f"Final counts - outbound: {len(formatted_messages)}, inbound: {len(inbound_messages)}")
        
        return {
            'messages': formatted_messages,
            'inbound_messages': inbound_messages,
            'stats': {
                'total': total,
                'delivered': delivered,
                'delivered_pct': round(delivered_pct, 1),
                'sent': sent,
                'sent_pct': round(sent_pct, 1),
                'failed': failed,
                'failed_pct': round(failed_pct, 1),
                'undelivered': undelivered,
                'received': received,
                'received_pct': round(received_pct, 1),
                'read': read,
                'read_pct': round(read_pct, 1),
                'undelivered_pct': round(undelivered_pct, 1),
                'inbound': inbound
            }
        }
    except Exception as e:
        current_app.logger.error(f"Error in API: {str(e)}")
        return {
            'error': str(e),
            'messages': [],
            'inbound_messages': [],
            'stats': {
                'total': 0,
                'delivered': 0,
                'delivered_pct': 0,
                'failed': 0,
                'received': 0,
                'received_pct': 0,
                'read': 0,
                'read_pct': 0,
                'undelivered_pct': 0,
                'inbound': 0
            }
        }

@bp.route('/campaigns')
@login_required
def campaigns():
    """List all campaign reports"""
    # Get filter parameters
    status = request.args.get('status')
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    # Parse dates
    now = datetime.now()
    if start_date_str:
        try:
            start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
        except ValueError:
            start_date = now - timedelta(days=30)
    else:
        start_date = now - timedelta(days=30)
        
    if end_date_str:
        try:
            end_date = datetime.strptime(end_date_str, '%Y-%m-%d')
            # Make it inclusive by setting to end of day
            end_date = end_date.replace(hour=23, minute=59, second=59)
        except ValueError:
            end_date = now
    else:
        end_date = now
    
    # Build query
    query = CampaignLog.query.filter(CampaignLog.created_at.between(start_date, end_date))
    
    if status:
        query = query.filter(CampaignLog.status == status)
        
    # Execute query
    logs = query.order_by(CampaignLog.created_at.desc()).all()
    
    # Calculate statistics
    total_recipients = sum(log.recipients_total for log in logs)
    total_success = sum(log.recipients_success for log in logs)
    total_failed = sum(log.recipients_failed for log in logs)
    success_rate = round(total_success / total_recipients * 100, 1) if total_recipients > 0 else 0
    
    return render_template('reports/campaigns.html',
                          logs=logs,
                          start_date=start_date,
                          end_date=end_date,
                          status=status,
                          total_recipients=total_recipients,
                          total_success=total_success,
                          total_failed=total_failed,
                          success_rate=success_rate)

@bp.route('/files')
@login_required
def files():
    """List all file reports"""
    # Get all report files
    reports_dir = os.path.join(current_app.root_path, '..', 'reports')
    if not os.path.exists(reports_dir):
        return render_template('reports/files.html', reports=[])
    
    files = [f for f in os.listdir(reports_dir) if f.endswith('.txt')]
    reports = []
    
    for file in files:
        # Extract date from filename
        match = re.search(r'(\d{2}-\d{2}-\d{2}_\d{2}-\d{2}-\d{2})', file)
        if match:
            date_str = match.group(1)
            try:
                date = datetime.strptime(date_str, '%d-%m-%y_%H-%M-%S')
                
                # Extract status from filename if present
                status_match = re.search(r'status_([A-Z]+)', file)
                status = status_match.group(1) if status_match else None
                
                # Check if it's a dry run
                is_dry_run = 'dry_run' in file
                
                # Check if force mode was used
                force_mode = 'force' in file
                
                reports.append({
                    'filename': file,
                    'date': date,
                    'status': status,
                    'is_dry_run': is_dry_run,
                    'force_mode': force_mode
                })
            except Exception:
                # Skip files with invalid date format
                continue
    
    # Sort by date (newest first)
    reports.sort(key=lambda x: x['date'], reverse=True)
    
    return render_template('reports/files.html', reports=reports)

@bp.route('/view/<filename>')
@login_required
def view_report(filename):
    """View a specific report file"""
    # Sanitize filename to prevent directory traversal
    if '..' in filename or '/' in filename:
        abort(404)
        
    reports_dir = os.path.join(current_app.root_path, '..', 'reports')
    file_path = os.path.join(reports_dir, filename)
    
    if not os.path.exists(file_path):
        abort(404)
    
    # Read file content
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Parse the report content
    report_info = {
        'filename': filename,
        'content': content
    }
    
    # Try to extract metadata
    meta = {}
    try:
        lines = content.split('\n')
        # Extract report type (Live or Dry Run)
        for line in lines:
            if 'Mode:' in line:
                meta['mode'] = line.split('Mode:')[1].strip()
            elif 'Generated:' in line:
                meta['generated'] = line.split('Generated:')[1].strip()
            elif 'Orders with status:' in line:
                meta['status'] = line.split('Orders with status:')[1].strip()
                
        # Extract summary
        summary_section = content.split('SUMMARY:')
        if len(summary_section) > 1:
            summary_lines = summary_section[1].strip().split('\n')
            for line in summary_lines:
                if ':' in line:
                    key, value = line.split(':', 1)
                    meta[key.strip().lower().replace(' ', '_')] = value.strip()
    except Exception:
        # If parsing fails, just use the raw content
        pass
    
    report_info['meta'] = meta
    
    return render_template('reports/view.html', report=report_info)

@bp.route('/download/<filename>')
@login_required
def download_report(filename):
    """Download a report file"""
    # Sanitize filename to prevent directory traversal
    if '..' in filename or '/' in filename:
        abort(404)
        
    reports_dir = os.path.join(current_app.root_path, '..', 'reports')
    file_path = os.path.join(reports_dir, filename)
    
    if not os.path.exists(file_path):
        abort(404)
    
    return send_file(file_path, as_attachment=True)

@bp.route('/campaign/<int:id>')
@login_required
def campaign_report(id):
    """View a specific campaign report"""
    campaign = Campaign.query.get_or_404(id)
    logs = campaign.logs.order_by(CampaignLog.created_at.desc()).all()
    
    # Calculate statistics
    total_recipients = sum(log.recipients_total for log in logs)
    total_success = sum(log.recipients_success for log in logs)
    total_failed = sum(log.recipients_failed for log in logs)
    success_rate = round(total_success / total_recipients * 100, 1) if total_recipients > 0 else 0
    
    return render_template('reports/campaign.html',
                          campaign=campaign,
                          logs=logs,
                          total_recipients=total_recipients,
                          total_success=total_success,
                          total_failed=total_failed,
                          success_rate=success_rate) 