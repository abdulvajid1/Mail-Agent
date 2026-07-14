from job_agent import MailAgent
import asyncio
 
async def main():
    agent = MailAgent()
    user_input = input("Start your Conversation")

    while user_input != "exit":
        out = await agent(user_input=user_input)
        user_input = input()

if __name__ == "__main__":
    asyncio.run(main())








