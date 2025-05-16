"""
Templates routes
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required
from mojo_web import db
from mojo_web.models import Template
from mojo_core.twilio_client import twilio_client

bp = Blueprint('templates', __name__, url_prefix='/templates')

@bp.route('/')
@login_required
def index():
    """List all templates"""
    templates = Template.query.order_by(Template.name).all()
    
    # Generate direct HTML response
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Templates - MOJO WhatsApp Manager</title>
        
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
            
            .table th {
                background-color: var(--mojo-dark);
                color: white;
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
                    <h2>Templates</h2>
                    <p class="text-muted">Manage WhatsApp message templates</p>
                </div>
                <div class="col-md-6 text-end">
                    <a href="/templates/create" class="btn btn-primary">
                        <i class="fas fa-plus"></i> Sync Templates from Twilio
                    </a>
                </div>
            </div>
            
            <div class="card">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-striped">
                            <thead>
                                <tr>
                                    <th>Name</th>
                                    <th>Template SID</th>
                                    <th>Description</th>
                                    <th>Variables</th>
                                    <th>Status</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
    """
    
    # Add template rows
    if templates:
        for template in templates:
            variables = ", ".join(template.variables) if template.variables else "None"
            status = '<span class="badge bg-success">Active</span>' if template.is_active else '<span class="badge bg-secondary">Inactive</span>'
            
            html += f"""
                                <tr>
                                    <td>{template.name}</td>
                                    <td><code>{template.template_sid}</code></td>
                                    <td>{template.description or 'N/A'}</td>
                                    <td>{variables}</td>
                                    <td>{status}</td>
                                    <td>
                                        <a href="/templates/{template.id}/edit" class="btn btn-sm btn-outline-primary">
                                            <i class="fas fa-edit"></i>
                                        </a>
                                        <button type="button" class="btn btn-sm btn-outline-danger" 
                                                onclick="confirmDelete({template.id}, '{template.name}')">
                                            <i class="fas fa-trash"></i>
                                        </button>
                                    </td>
                                </tr>
            """
    else:
        html += """
                                <tr>
                                    <td colspan="6" class="text-center">No templates found. Click "Sync Templates from Twilio" to import templates.</td>
                                </tr>
        """
    
    html += """
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>
            
            <div class="row mt-4">
                <div class="col-md-12 text-center">
                    <p class="text-muted">MOJO WhatsApp Manager | Version 1.0</p>
                </div>
            </div>
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
                        Are you sure you want to delete the template <span id="templateName"></span>?
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
        
        <!-- Bootstrap JavaScript -->
        <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
        
        <script>
            function confirmDelete(id, name) {
                document.getElementById('deleteForm').action = `/templates/${id}/delete`;
                document.getElementById('templateName').textContent = name;
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
    """Create a new template"""
    if request.method == 'POST':
        name = request.form.get('name')
        template_sid = request.form.get('template_sid')
        description = request.form.get('description')
        variables = request.form.getlist('variables')
        
        if not name or not template_sid:
            flash('Name and Template SID are required.', 'danger')
            return render_template('templates/create.html')
        
        # Check if template already exists
        existing = Template.query.filter_by(template_sid=template_sid).first()
        if existing:
            flash('A template with this SID already exists.', 'danger')
            return render_template('templates/create.html')
        
        # Create new template
        template = Template(
            name=name,
            template_sid=template_sid,
            description=description,
        )
        template.variables = variables
        
        db.session.add(template)
        db.session.commit()
        
        flash('Template created successfully.', 'success')
        return redirect(url_for('templates.index'))
    
    # GET request
    # Get available templates from Twilio
    twilio_templates = []
    try:
        twilio_templates = twilio_client.get_templates()
    except Exception as e:
        flash(f"Could not fetch templates from Twilio: {str(e)}", "warning")
    
    return render_template('templates/create.html', twilio_templates=twilio_templates)

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    """Edit a template"""
    template = Template.query.get_or_404(id)
    
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        variables = request.form.getlist('variables')
        is_active = 'is_active' in request.form
        
        if not name:
            flash('Name is required.', 'danger')
            return render_template('templates/edit.html', template=template)
        
        # Update template
        template.name = name
        template.description = description
        template.variables = variables
        template.is_active = is_active
        
        db.session.commit()
        
        flash('Template updated successfully.', 'success')
        return redirect(url_for('templates.index'))
    
    return render_template('templates/edit.html', template=template)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    """Delete a template"""
    template = Template.query.get_or_404(id)
    
    # Check if template is in use by any campaigns
    if template.campaigns.count() > 0:
        flash('Cannot delete a template that is in use by campaigns.', 'danger')
        return redirect(url_for('templates.index'))
    
    db.session.delete(template)
    db.session.commit()
    
    flash('Template deleted successfully.', 'success')
    return redirect(url_for('templates.index')) 