import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_real_email(to_email: str, subject: str, body: str):
    """
    Sends a real email using Gmail SMTP.
    Requires GMAIL_USER and GMAIL_APP_PASSWORD in .env
    """
    sender_email = os.getenv("GMAIL_USER")
    sender_password = os.getenv("GMAIL_APP_PASSWORD")
    
    if not sender_email or not sender_password:
        return "❌ Failed: Missing GMAIL_USER or GMAIL_APP_PASSWORD in .env"

    try:
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))

        # Standard Gmail SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.send_message(msg)
            
        return f"✅ Email sent successfully to {to_email}"
    except Exception as e:
        return f"❌ Email Error: {str(e)}"
