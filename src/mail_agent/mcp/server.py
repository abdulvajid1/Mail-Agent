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
async def send_mail(sender: str, subject: str, body: str, recipients: list[str], attachment: str | None):
    """Send mail from sender to recipients with specified body content. Use attachment if only user specified it's path else leave it empty"""
    try: 
        _send_mail(host=HOST, 
                   port=PORT, 
                   sender=sender, 
                   recipients=recipients, 
                   subject=subject, 
                   body=body, 
                   attachment=attachment)
        
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

Never invent email addresses or send emails with missing required information.
"""
    

def main():
    mcp.run(transport="stdio", show_banner=False)

if __name__ == "__main__":
    main()