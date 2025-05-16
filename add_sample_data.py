#!/usr/bin/env python3
"""
Sample data initialization for MOJO WhatsApp Manager
"""
from datetime import datetime, timedelta
import json
from mojo_web import create_app, db
from mojo_web.models import Template, Campaign, CampaignLog

def add_sample_data():
    """Add sample data to the database"""
    # Create app context
    app = create_app()
    with app.app_context():
        # Check if we already have data
        if Template.query.count() > 0 or Campaign.query.count() > 0:
            print("Sample data already exists. Skipping.")
            return
            
        # Create sample templates
        template1 = Template(
            name="Order Confirmation",
            template_sid="TM123456789",
            description="Sent when an order is confirmed",
            variables_json=json.dumps(["name", "order_id"]),
            is_active=True,
            created_at=datetime.now()
        )
        
        template2 = Template(
            name="Shipping Notification",
            template_sid="TM987654321",
            description="Sent when an order ships",
            variables_json=json.dumps(["name", "order_id", "tracking_number"]),
            is_active=True,
            created_at=datetime.now()
        )
        
        db.session.add(template1)
        db.session.add(template2)
        db.session.commit()
        
        # Create sample campaigns
        campaign1 = Campaign(
            name="Welcome Campaign",
            description="Send welcome messages to new customers",
            template_id=template1.id,
            db_path="affiliates.db",
            status="completed",
            last_run=datetime.now() - timedelta(days=1),
            created_at=datetime.now() - timedelta(days=2)
        )
        
        campaign2 = Campaign(
            name="Shipping Updates",
            description="Notify customers when orders ship",
            template_id=template2.id,
            db_path="affiliates.db",
            status="scheduled",
            next_run=datetime.now() + timedelta(days=1),
            created_at=datetime.now()
        )
        
        db.session.add(campaign1)
        db.session.add(campaign2)
        db.session.commit()
        
        # Create sample campaign logs
        log1 = CampaignLog(
            campaign_id=campaign1.id,
            status="success",
            recipients_total=100,
            recipients_success=95,
            recipients_failed=5,
            execution_time=120.5,
            created_at=datetime.now() - timedelta(days=1)
        )
        
        log2 = CampaignLog(
            campaign_id=campaign1.id,
            status="success",
            recipients_total=150,
            recipients_success=142,
            recipients_failed=8,
            execution_time=180.3,
            created_at=datetime.now() - timedelta(days=1, hours=12)
        )
        
        db.session.add(log1)
        db.session.add(log2)
        db.session.commit()
        
        print("Sample data added successfully.")

if __name__ == "__main__":
    add_sample_data() 