import os
import smtplib
from email.message import EmailMessage
from jinja2 import Environment, FileSystemLoader
from dotenv import load_dotenv

load_dotenv()

env = Environment(loader=FileSystemLoader("templates"))

def send_otp_email(receiver_email, otp):
    # Get credentials from .env
    sender_email = os.getenv("EMAIL_USER")
    sender_password = os.getenv("EMAIL_PASS")
    template = env.get_template("otp_temp.html")
    html_content = template.render(otp=otp)

    # Create the email content
    msg = EmailMessage()
    msg['Subject'] = "Verify Your Business Account"
    msg['From'] = sender_email
    msg['To'] = receiver_email

    msg.set_content("Your email client does not support HTML emails.")
    msg.add_alternative(html_content, subtype="html")

    try:
        # Connect to Gmail's SMTP server
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(sender_email, sender_password)
            smtp.send_message(msg)   
    except Exception as e:
        print(f"Error sending email: {e}")
