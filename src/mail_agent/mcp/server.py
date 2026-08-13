from fastmcp import FastMCP
from mail_agent.tools import _send_mail, _read_mail
from mail_agent.utils import load_config
import logging
logging.basicConfig(level=logging.ERROR)
# or, more targeted:
logging.getLogger("mcp").setLevel(logging.ERROR)
logging.getLogger("fastmcp").setLevel(logging.ERROR)
logging.getLogger("mcp.server").setLevel(logging.ERROR)

mcp = FastMCP('gmail',
              client_log_level='error', )

HOST = "smtp.gmail.com"
PORT = 587

@mcp.tool()
async def send_mail(sender: str, 
                    subject: str, 
                    recipients: list[str], 
                    body: str,  
                    attachment: str, 
                    is_draft: bool
                ):

    """ 
    Send or draft an email.

    Use this tool whenever the user wants to send an email, compose an email,
    draft an email, reply to an email, or send a message to one or more recipients.

    Parameters:
    - sender: Email address of the authenticated account sending the email.
    - subject: Subject line of the email.
    - recipients: List of recipient email addresses.
    - body: Complete email body content. Generate a professional and well-formatted
      message when the user provides instructions rather than the final text.
    - attachment: File path of an attachment only when the user explicitly requests
      attaching a file or provides a file path. Otherwise use "" (empty string).
    - is_draft:
        * True  -> Save the email as a draft without sending it.
        * False -> Send the email immediately.

    Guidelines:
    - Use is_draft=True when the user says things such as:
      "draft an email", "create a draft", "prepare an email", "save as draft",
      or when they ask to review the email before sending.

    - Use is_draft=False when the user clearly wants the email delivered,
      such as:
      "send an email", "email them", "notify them", "send this message".

    - Do not invent recipient addresses.
    - Do not invent attachments.
    """
   
    try: 
        _send_mail(sender=sender, 
                   recipients=recipients, 
                   subject=subject, 
                   body=body, 
                   attachment=attachment,
                   is_draft=is_draft)
        
        if is_draft:
            return "Mail Drafted Successfully"
        else:
            return "Mail Send Successfully"
    except Exception as e:
        return f"Issue in sending in mail:\n\n {e}"
 
@mcp.tool()    
async def read_mail(num_mails: int):
    try:
       results = _read_mail(num_emails=num_mails)
       # print('Successfully read'), how to show this in ui
       return results
    except Exception as e:
        return f"Some error occured while reading mails{e}"
        
    

@mcp.prompt
async def system_prompt() -> str:
    config = load_config()
    user_mail = config.get('user_mail', None)
    if not user_mail:
        raise Exception("No User mail for System Prompt")
    return f"""You are Mail Agent, a reliable assistant for reading, writing, and sending emails.

Default sender email: {user_mail}

If the user does not specify a sender email, use the default sender email above. Use a different sender only if the user explicitly provides one.

Never invent email addresses or attachment path.

Ask user if you are missing information, if user told you to send with attachment but didn't provide attachment file name, ask for user for informations.
"""
    

def main():
    mcp.run(transport="stdio", show_banner=False)

if __name__ == "__main__":
    main()