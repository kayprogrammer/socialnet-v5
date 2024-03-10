from jinja2 import Environment, PackageLoader
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.db.models.accounts import Otp
from app.core.config import settings
import os, smtplib

env = Environment(loader=PackageLoader("app", "templates"))


async def sort_email(user, email_type):
    template_file = "welcome.html"
    subject = "Account verified"
    data = {"template_file": template_file, "subject": subject}

    # Sort different templates and subject for respective email types
    if email_type == "activate":
        template_file = "email-activation.html"
        subject = "Activate your account"
        otp = await Otp.update_or_create(user_id=user.id)
        data = {"template_file": template_file, "subject": subject, "otp": otp.code}

    elif email_type == "reset":
        template_file = "password-reset.html"
        subject = "Reset your password"
        otp = await Otp.update_or_create(user_id=user.id)
        data = {"template_file": template_file, "subject": subject, "otp": otp.code}

    elif email_type == "reset-success":
        template_file = "password-reset-success.html"
        subject = "Password reset successfully"
        data = {"template_file": template_file, "subject": subject}

    return data


async def send_email(user, type):
    if os.environ.get("ENVIRONMENT") == "testing":
        return
    email_data = await sort_email(user, type)
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

    # Send email
    try:
        with smtplib.SMTP_SSL(
            host=settings.MAIL_SENDER_HOST, port=settings.MAIL_SENDER_PORT
        ) as server:
            server.login(settings.MAIL_SENDER_EMAIL, settings.MAIL_SENDER_PASSWORD)
            server.sendmail(
                settings.MAIL_SENDER_EMAIL, message["To"], message.as_string()
            )
    except Exception as e:
        print(f"Email Error - {e}")
