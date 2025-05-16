"""
Twilio API client wrapper
"""
import os
from twilio.rest import Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class TwilioClient:
    """Twilio API client wrapper"""

    def __init__(self):
        # Get credentials from environment
        self.account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
        self.auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
        self.whatsapp_number = os.environ.get("TWILIO_WHATSAPP_NUMBER", "whatsapp:+15551234567")
        self.messaging_service_sid = os.environ.get("TWILIO_MESSAGING_SERVICE_SID")
        
        # Validate credentials
        if not self.account_sid or not self.auth_token:
            raise ValueError("TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN must be set in environment variables or .env file.")
        
        # Initialize client
        self.client = Client(self.account_sid, self.auth_token)
    
    def send_whatsapp_message(self, to, content_sid, content_variables=None, order_id=None):
        """
        Send a WhatsApp message using Twilio Content API
        
        Args:
            to (str): Recipient's WhatsApp number
            content_sid (str): Content template SID
            content_variables (dict): Variables for the template
            order_id (str): Order ID for tracking
            
        Returns:
            twilio.rest.api.v2010.account.message.MessageInstance: Twilio message instance
        """
        import json
        
        if content_variables is None:
            content_variables = {}
            
        # Format 'to' number for WhatsApp if needed
        if to and not to.startswith('whatsapp:'):
            to = f"whatsapp:{to}"
        
        # Prepare message parameters
        message_params = {
            "content_sid": content_sid,
            "content_variables": json.dumps(content_variables),
            "to": to
        }
        
        # Add either messaging_service_sid or from_
        if self.messaging_service_sid:
            message_params["messaging_service_sid"] = self.messaging_service_sid
        else:
            message_params["from_"] = self.whatsapp_number
        
        # Send message
        return self.client.messages.create(**message_params)
    
    def get_templates(self):
        """
        List all content templates
        
        Returns:
            list: List of content templates
        """
        return self.client.content.v1.contents.list()

# Singleton instance
twilio_client = TwilioClient() 