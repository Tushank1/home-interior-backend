import smtplib
from email.mime.text import MIMEText
from app.config.settings import settings

def send_resend_email(to_email: str,token: str):
    reset_link = f"{settings.web_url}/{token}"
    
    subject = "Reset your password"
    body = f"Click the link to reset your password:\n\n{reset_link}"
    
    message = MIMEText(body)
    message["Subject"] = subject
    message["From"] = settings.smtp_username
    message["To"] = to_email
    
    with smtplib.SMTP(settings.smtp_server,settings.smtp_port) as server:
        server.starttls()
        server.login(settings.smtp_from_address, settings.smtp_password)
        server.sendmail(settings.smtp_from_address,to_email,message.as_string())
        
def email_events(to_email: str,body_content: str,events: str):
    pass