from langchain.tools import tool


@tool
def send_mail(to: str, subject: str, body: str) -> str:
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