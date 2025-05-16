from datetime import datetime
from app import db

class Template(db.Model):
    __tablename__ = 'whatsapp_templates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    template_sid = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    variables = db.Column(db.Text)  # JSON string of template variables
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    
    def __repr__(self):
        return f'<Template {self.name}>' 