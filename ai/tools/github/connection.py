
import os
import httpx
from dotenv import load_dotenv


load_dotenv()


class GitHubConnection:

    BASE_URL = "https://api.github.com"

    def __init__(self):

        self.token = os.getenv("GITHUB_TOKEN")

        if not self.token:
            raise ValueError("GITHUB_TOKEN is missing in .env")

        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }

        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self.headers,
            timeout=30.0
        )

    async def request(self, method: str, endpoint: str, **kwargs):

        response = await self.client.request(
            method=method,
            url=endpoint,
            **kwargs
        )

        response.raise_for_status()

        if response.content:
            return response.json()

        return None

    async def close(self):

        await self.client.aclose()
