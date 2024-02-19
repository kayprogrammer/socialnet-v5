from jinja2 import Environment, PackageLoader
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.db.models.accounts import Otp
from .threads import EmailThread
from app.core.config import settings
import os

env = Environment(loader=PackageLoader("app", "templates"))

async def sort_email(db, user, email_type):
    template_file = "welcome.html"
    subject = "Account verified"
    data = {"template_file": template_file, "subject": subject}

    # Sort different templates and subject for respective email types
    if email_type == "activate":
        template_file = "email-activation.html"
        subject = "Activate your account"
        otp = Otp.get_or_create(user_id=user.id)
        data = {"template_file": template_file, "subject": subject, "otp": otp.code}

    elif email_type == "reset":
        template_file = "password-reset.html"
        subject = "Reset your password"
        otp = Otp.get_or_create(user_id=user.id)
        data = {"template_file": template_file, "subject": subject, "otp": otp.code}

    elif email_type == "reset-success":
        template_file = "password-reset-success.html"
        subject = "Password reset successfully"
        data = {"template_file": template_file, "subject": subject}

    return data


async def send_email(db, user, type):
    if os.environ["ENVIRONMENT"] == "testing":
        return
    email_data = await sort_email(db, user, type)
    template_file = email_data["template_file"]
    subject = email_data["subject"]

    context = {"name": user.first_name}
    otp = email_data.get("otp")
    if otp:
        context["otp"] = otp

    # Render the email template using jinja
    template = env.get_template(template_file)
    html = template.render(context)

    # Create a message with the HTML content
    message = MIMEMultipart()
    message["From"] = settings.MAIL_SENDER_EMAIL
    message["To"] = user.email
    message["Subject"] = subject
    message.attach(MIMEText(html, "html"))

    # Send email in background
    EmailThread(message).start()