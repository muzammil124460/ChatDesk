
import asyncio

from ai.tools.github.connection import GitHubConnection


async def main():

    github = GitHubConnection()

    try:

        user = await github.request(
            method="GET",
            endpoint="/user"
        )

        print("GitHub Connected Successfully!")

        print("Username:", user["login"])
        print("Name:", user["name"])
        print("Profile:", user["html_url"])

    except Exception as e:

        print("GitHub Connection Failed:", e)

    finally:

        await github.close()


asyncio.run(main())
