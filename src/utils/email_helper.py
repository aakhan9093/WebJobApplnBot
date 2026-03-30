import os
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
logger = logging.getLogger(__name__)

def send_job_bot_email(recipient, subject, content, attachment_paths=None):
    """
    Send an email with the job bot results.
    
    Args:
        recipient (str): Email address of the recipient
        subject (str): Email subject
        content (str): Markdown content or body text
        attachment_paths (list): List of Path objects or strings to files to attach
    """
    gmail_user = os.getenv("GMAIL_USER")
    gmail_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not gmail_user or not gmail_password:
        logger.error("Gmail credentials not found in environment variables.")
        return False
        
    try:
        msg = MIMEMultipart()
        msg['From'] = gmail_user
        msg['To'] = recipient
        msg['Subject'] = subject
        
        msg.attach(MIMEText(content, 'plain'))
        
        # Attach files
        if attachment_paths:
            for path in attachment_paths:
                path = Path(path)
                if path.exists():
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), Name=path.name)
                        part['Content-Disposition'] = f'attachment; filename="{path.name}"'
                        msg.attach(part)
                else:
                    logger.warning(f"Attachment not found: {path}")
        
        # Send
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(gmail_user, gmail_password)
        server.send_message(msg)
        server.quit()
        
        logger.info(f"Email successfully sent to {recipient}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
