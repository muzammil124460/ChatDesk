import os
import asyncio
from dotenv import load_dotenv
from ai.tools.notion.connection import NotionConnection

load_dotenv()


async def main():

    token = os.getenv("NOTION_TOKEN")

    if not token:
        raise ValueError("NOTION_TOKEN not found")

    notion = NotionConnection(token)

    try:
        result = await notion.request(
            method="GET",
            endpoint="/users/me"
        )

        print(result)

    finally:
        await notion.close()


asyncio.run(main())