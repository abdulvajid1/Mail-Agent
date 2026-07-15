from job_agent import MailAgent
import asyncio
 
async def main():
    agent = MailAgent()
    await agent.intialize()
    user_input = input("User: ")

    while user_input != "exit":
        print("Assistent: ", end="", flush=True)
        async for msg in agent.stream(user_input=user_input):
            print(msg, end="", flush=True)

        user_input = input("\nUser: ")


def main_cli():
    asyncio.run(main())  

if __name__ == "__main__":
    main_cli()
    








