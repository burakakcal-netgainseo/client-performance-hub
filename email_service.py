from imap_tools import MailBox, AND, OR
import app_config as config
from datetime import date, timedelta
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

class EmailService:
    def __init__(self, user, password):
        self.user = user
        self.password = password
        self.imap_url = 'imap.gmail.com'
        self.smtp_url = 'smtp.gmail.com'
        self.smtp_port = 587

    def send_notification_email(self, subject, body, report_recipient_str, is_html=False, logos=None):
        try:
            from email.mime.image import MIMEImage
            import os

            # Parse recipients
            to_list = []
            bcc_list = []
            
            raw_recipients = [r.strip() for r in report_recipient_str.split(',')]
            for r in raw_recipients:
                if r.lower().startswith('bcc:'):
                    bcc_list.append(r[4:].strip())
                else:
                    to_list.append(r)

            msg = MIMEMultipart()
            msg['From'] = self.user
            msg['To'] = ", ".join(to_list)
            msg['Subject'] = subject

            subtype = 'html' if is_html else 'plain'
            msg.attach(MIMEText(body, subtype))

            if logos:
                for cid, path in logos.items():
                    if os.path.exists(path):
                        with open(path, 'rb') as f:
                            img = MIMEImage(f.read())
                            img.add_header('Content-ID', f'<{cid}>')
                            img.add_header('Content-Disposition', 'inline', filename=os.path.basename(path))
                            msg.attach(img)

            all_recipients = list(set(to_list + bcc_list))
            print(f"Sending {'HTML' if is_html else 'plain text'} notification email to To: {to_list} | BCC: {bcc_list}...")
            
            server = smtplib.SMTP(self.smtp_url, self.smtp_port)
            server.starttls()
            server.login(self.user, self.password)
            
            text = msg.as_string()
            server.sendmail(self.user, all_recipients, text)
            server.quit()
            print("Notification email sent successfully.")
        except Exception as e:
            print(f"Failed to send notification email: {e}")

    def fetch_emails(self, client_config, days=1):
        """
        Fetch emails from the last 'days' days based on client config keywords.
        """
        client_name = client_config.get('client_name', '')
        search_keywords = client_config.get('search_keywords', [])
        
        search_date = date.today() - timedelta(days=days)
        
        print(f"Connecting to {self.imap_url} as {self.user}...")
        
        try:
            with MailBox(self.imap_url).login(self.user, self.password) as mailbox:
                # Dynamically build OR criteria for keywords
                # Note: imap_tools OR takes multiple arguments
                keyword_criteria = []
                for kw in search_keywords:
                    keyword_criteria.append(AND(subject=kw))
                    keyword_criteria.append(AND(body=kw))
                
                # Special cases for CTM
                keyword_criteria.append(AND(subject="Call Log Export"))
                keyword_criteria.append(AND(from_="no-reply@calltrackingmetrics.com"))

                criteria = AND(
                    OR(*keyword_criteria),
                    date_gte=search_date
                )
                
                print(f"Searching emails since {search_date} for {client_name} keywords...")
                msgs = mailbox.fetch(criteria)
                
                relevant_emails = []
                for msg in msgs:
                    relevant_emails.append(msg)
                        
                print(f"Found {len(relevant_emails)} potential emails.")
                return relevant_emails
                
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []
