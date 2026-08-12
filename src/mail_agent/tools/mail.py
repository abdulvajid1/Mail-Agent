import os
from pathlib import Path
import smtplib
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from langsmith import traceable

from mail_agent.utils import authorize_google_mail
from mail_agent.utils import generate_oauth2_string
from mail_agent.utils import load_config, save_config

import imaplib
import email
from email.header import decode_header
from email.utils import parsedate_to_datetime
from email import encoders
from email.message import Message

from mail_agent.utils import authorize_google_mail
from mail_agent.utils import generate_oauth2_string

def get_attachment_path(attachment_path):
    attachment_dir = load_config()['attachment_dir']

    if not attachment_dir:
        return "User didn't setup attachment dir, Setup using job-agent setup" # type: igno
    
    attachment_path = Path(attachment_dir) / attachment_path
    if not attachment_path.exists():
        return f"Attachment path {attachment_path} does not exit, make sure the user have the {attachment_path} in {attachment_dir}" # type: ignore
    
    return attachment_path

def _get_attachment_mail_part(attachment_path: Path):
    
    payload = MIMEBase('application', 'octate-stream', Name=attachment_path.name)
    
    with open(attachment_path, 'rb') as f:
        payload.set_payload(f.read())
    
    encoders.encode_base64(payload)
    
    # add header 
    payload.add_header('Content-Decomposition', 'attachment', filename=attachment_path.name)
    return payload

@traceable    
def _send_mail(
        host: str,
        port: int, 
        subject: str, 
        body: str, 
        sender: str, 
        recipients: list[str],
        attachment: str | None
    ):

    access_token = authorize_google_mail()
    auth_string = generate_oauth2_string(sender, access_token, as_base64=True)
    
    msg = MIMEMultipart()
    msg.attach(MIMEText(body, 'plain'))
    msg['Subject'] = subject
    msg['From'] = sender
    msg['To'] = ', '.join(recipients)
    
    if attachment:
        attachment_path = get_attachment_path(attachment)
        if not attachment_path:
            return f"Didn't find attachment in {attachment_path}"
        
        # retrieve attachment from dir create mail part to attach with main msg
        attachment_payload = _get_attachment_mail_part(attachment_path)
        msg.attach(attachment_payload)

    server = smtplib.SMTP(host, port)
    server.starttls()
    server.docmd('AUTH', 'XOAUTH2 ' + auth_string)
    server.sendmail(sender, recipients, msg.as_string())
    server.quit()



def _decode_header_value(value: str) -> str:
    """Decode possibly-encoded email headers (e.g. '=?UTF-8?B?...?=') into plain text."""
    if not value:
        return ""
    parts = decode_header(value)
    decoded = ""
    for text, enc in parts:
        if isinstance(text, bytes):
            decoded += text.decode(enc or "utf-8", errors="replace")
        else:
            decoded += text
    return decoded


def _get_body(msg: Message) -> str:
    """Extract plain-text body, falling back to stripped HTML if no plain part exists."""
    if msg.is_multipart():
        # Prefer text/plain; fall back to text/html
        plain, html = None, None
        for part in msg.walk():
            content_type = part.get_content_type()
            disposition = str(part.get("Content-Disposition", ""))
            if "attachment" in disposition:
                continue
            if content_type == "text/plain" and plain is None:
                plain = part.get_payload(decode=True)
            elif content_type == "text/html" and html is None:
                html = part.get_payload(decode=True)
        raw = plain or html
        if raw is None:
            return ""
        charset = msg.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace") # type: ignore
    else:
        raw = msg.get_payload(decode=True)
        if raw is None:
            return ""
        charset = msg.get_content_charset() or "utf-8"
        return raw.decode(charset, errors="replace") # type: ignore

@traceable
def _read_mail(
    num_emails: int,
    host: str = "imap.gmail.com",
    port: int = 993,
    mailbox: str = "INBOX",
) -> list[dict]:
    """
    Read the last `num_emails` emails from `mailbox` and return them as a
    structured list suitable for LLM input.

    Args:
        num_emails: how many recent emails to fetch.
        sender: the mailbox's own email address (used for OAuth2 auth).
        host: IMAP host.
        port: IMAP SSL port.
        mailbox: which mailbox/folder to read from.

    Returns:
        List of dicts: [{"from": ..., "subject": ..., "date": ..., "body": ...}, ...]
        ordered newest-first.
    """
    user = load_config()['user_mail']
    access_token = authorize_google_mail()
    auth_string = generate_oauth2_string(user, access_token, as_base64=False)

    imap = imaplib.IMAP4_SSL(host, port)
    imap.authenticate("XOAUTH2", lambda _: auth_string.encode() if isinstance(auth_string, str) else auth_string)
    imap.select(mailbox)

    status, data = imap.search(None, "ALL")
    if status != "OK":
        imap.logout()
        return []

    all_ids = data[0].split()
    target_ids = all_ids[-num_emails:]  # last N, oldest-to-newest
    target_ids.reverse()  # newest-first

    results = []
    for msg_id in target_ids:
        status, msg_data = imap.fetch(msg_id, "(RFC822)")
        if status != "OK":
            continue

        raw_email = msg_data[0][1] # type: ignore
        msg = email.message_from_bytes(raw_email) # type: ignore

        date_str = msg.get("Date")
        try:
            parsed_date = parsedate_to_datetime(date_str).isoformat() if date_str else None
        except Exception:
            parsed_date = date_str

        results.append({
            "from": _decode_header_value(msg.get("From", "")),
            "subject": _decode_header_value(msg.get("Subject", "")),
            "date": parsed_date,
            "body": _get_body(msg).strip(),
        })

    imap.logout()
    return results




   
        