from job_agent import MailAgent
import asyncio
 
async def main():
    agent = MailAgent()
    agent = await agent.intialize()
    user_input = input("User Turn: ")

    while user_input != "exit":
        print("Assistent turn: ", end="", flush=True)
        out = await agent(user_input=user_input)
        user_input = input("\nUser Turn: ")


def main_cli():
    asyncio.run(main())

if __name__ == "__main__":
    main_cli()
    








