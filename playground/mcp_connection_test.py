from job_agent.mcp import connect_to_mcp
import asyncio

async def main():
    client = connect_to_mcp()
    # async with client: # client session connection
    #     print(f'Client Connection Status: {client.is_connected()}')
    #     await client.ping()
    #     tools = await client.list_tools()
    #     print("No. of tools Available: ", len(tools))

    #     # check if it's langchain compatible
    #     print(dir(tools[0]))
    tools = await client.get_tools()
    print(tools)
    

if __name__ == "__main__":
    asyncio.run(main())