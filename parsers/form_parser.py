import re
from .base import BaseParser
# import config  # Removed hardcoded config
from datetime import datetime
from utils import format_name, format_phone

class FormParser(BaseParser):
    def parse(self, email_msg):
        # Determine if this is a form submission
        # This logic might need retuning based on actual email subjects
        subject = email_msg.subject.lower()
        if "form" not in subject and "submission" not in subject and "new lead" not in subject:
            # Fallback: check if body looks like a form
            pass

        # Exclude common report emails
        if "report" in subject or "dashboard" in subject or "analytics" in subject:
            return []
            
        body = email_msg.text or email_msg.html
        if not body:
            return []

        # Strict Check: Ensure the email is actually for this client
        client_name = self.client_config.get('client_name', '').lower()
        if client_name not in subject and client_name not in body.lower():
            return []

        # Simple extraction logic (can be improved with specific regex from user samples)
        # Looking for "Name:", "Email:", "Phone:" patterns
        
        # Regex for Name
        name_match = re.search(r'(?:Name|Full Name):\s*(.*)', body, re.IGNORECASE)
        name = name_match.group(1).strip() if name_match else ""

        # Regex for Email
        email_match = re.search(r'(?:Email|E-mail):\s*([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', body, re.IGNORECASE)
        email = email_match.group(1).strip() if email_match else ""

        # Regex for Phone
        phone_match = re.search(r'(?:Phone|Mobile|Cell):\s*([\d\+\-\.\(\)\s]+)', body, re.IGNORECASE)
        phone = phone_match.group(1).strip() if phone_match else ""



        # Regex for Message (Body)
        # Capture content after "Message:" but stop at "---" or "Date:" or end of string
        message_match = re.search(r'(?:Message|Comment|Comments|Questions):\s*(.*?)(?:\n\s*-{3,}|\nDate:|\nPage URL:|$)', body, re.IGNORECASE | re.DOTALL)
        
        message_content = ""
        if message_match:
             potential_msg = message_match.group(1).strip()
             message_content = potential_msg[:500]

        # If we found at least a name, email, OR phone, consider it a lead
        if name or email or phone:
            # --- FILTER TEST LEADS ---
            to_ignore = self.client_config.get('parser_settings', {}).get('ignored_emails', [])
            if email.lower() in to_ignore:
                print(f"DEBUG: Ignoring test lead from {email}")
                return []
            
            # Check body for "test" and "netgain"
            if "test" in body.lower() and "netgain" in body.lower():
                 print("DEBUG: Ignoring test lead (detected 'test' and 'netgain' in body)")
                 return []
            # -------------------------

            return [{
                'Date': email_msg.date.strftime("%Y-%m-%d"),
                'Client Name': format_name(name) if name else "Unknown",
                'Email': email,
                'Phone': format_phone(phone),
                'Platform': 'Website',
                'Lead Type': 'Form Submission',
                'Sold?': '',
                'Forecasted Revenue': '',
                'Notes': message_content # Correctly placed in Notes (Column I)
            }]
        
        return []
