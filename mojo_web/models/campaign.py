"""
Campaign model for scheduling message sends
"""
from datetime import datetime
import json
from mojo_web import db

class Campaign(db.Model):
    """WhatsApp message campaign model"""
    __tablename__ = 'campaigns'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    template_id = db.Column(db.Integer, db.ForeignKey('templates.id'), nullable=False)
    db_path = db.Column(db.String(255), nullable=False)
    filter_conditions = db.Column(db.Text, nullable=True)
    order_status = db.Column(db.String(50), nullable=True)
    recipient_limit = db.Column(db.Integer, nullable=True)
    variables_json = db.Column(db.Text, nullable=True)
    force_flag = db.Column(db.Boolean, default=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Scheduling fields
    scheduled_time = db.Column(db.DateTime, nullable=True)
    is_recurring = db.Column(db.Boolean, default=False)
    recurrence_pattern = db.Column(db.String(50), nullable=True)  # daily, weekly, monthly
    recurrence_data = db.Column(db.Text, nullable=True)  # JSON with additional recurrence data
    
    # Status fields
    status = db.Column(db.String(20), default='draft')  # draft, scheduled, running, completed, failed
    last_run = db.Column(db.DateTime, nullable=True)
    next_run = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    template = db.relationship('Template', back_populates='campaigns')
    logs = db.relationship('CampaignLog', back_populates='campaign', lazy='dynamic')
    
    @property
    def variables(self):
        """Get campaign variables as a dict"""
        if not self.variables_json:
            return {}
        return json.loads(self.variables_json)
    
    @variables.setter
    def variables(self, variables_dict):
        """Set campaign variables from a dict"""
        self.variables_json = json.dumps(variables_dict)
    
    def __repr__(self):
        return f'<Campaign {self.name}>'

class CampaignLog(db.Model):
    """Log entry for campaign execution"""
    __tablename__ = 'campaign_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    campaign_id = db.Column(db.Integer, db.ForeignKey('campaigns.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False)  # success, failure
    recipients_total = db.Column(db.Integer, default=0)
    recipients_success = db.Column(db.Integer, default=0)
    recipients_failed = db.Column(db.Integer, default=0)
    report_path = db.Column(db.String(255), nullable=True)
    execution_time = db.Column(db.Float, nullable=True)  # seconds
    error_message = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    campaign = db.relationship('Campaign', back_populates='logs')
    
    def __repr__(self):
        return f'<CampaignLog {self.id} ({self.status})>' 