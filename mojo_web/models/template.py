"""
Template model for the web app
"""
from datetime import datetime
import json
from mojo_web import db

class Template(db.Model):
    """WhatsApp message template model"""
    __tablename__ = 'templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    template_sid = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text, nullable=True)
    variables_json = db.Column(db.Text, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with campaigns
    campaigns = db.relationship('Campaign', back_populates='template', lazy='dynamic')
    
    @property
    def variables(self):
        """Get template variables as a list"""
        if not self.variables_json:
            return []
        return json.loads(self.variables_json)
    
    @variables.setter
    def variables(self, variables_list):
        """Set template variables from a list"""
        self.variables_json = json.dumps(variables_list)
    
    def __repr__(self):
        return f'<Template {self.name}>' 