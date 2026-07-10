import smtplib
from email.mime.text import MIMEText

from langchain.tools import tool

from job_agent.utils import getToken
from job_agent.utils import generate_oauth2_string


@tool
def send_dummy_mail(to: str, subject: str, body: str) -> str:
    """
    Send an email to the specified recipient with the given subject and body.

    Args:
        to (str): The recipient's email address.
        subject (str): The subject of the email.
        body (str): The body content of the email.

    Returns:
        str: A confirmation message indicating that the email has been sent.
    """
    # Here you would implement the actual email sending logic using an email library or service.
    # For demonstration purposes, we'll just return a confirmation message.
    return f"Email sent to {to} with subject '{subject}' and body '{body}'."


def send_email(host, port, subject, msg, sender, recipients):
    access_token = getToken()
    auth_string = generate_oauth2_string(sender, access_token, as_base64=True)

    msg = MIMEText(msg)
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)

    server = smtplib.SMTP(host, port)
    server.starttls()
    server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
    server.sendmail(sender, recipients, msg.as_string())
    server.quit()