from mcp.server.fastmcp import FastMCP
from job_agent.tools import send_email

mcp = FastMCP('gmail')

HOST = "smtp.gmail.com"
PORT = 587

@mcp.tool()
async def send_mail(sender, subject, body, recipients):
    try: 
        send_email(host=HOST, port=PORT, sender=sender, recipients=recipients, subject=subject, msg=body)
        return "Mail Send Successfully"
    except Exception as e:
        return f"Issue in sending in mail:\n\n {e}"
    

def main():
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()