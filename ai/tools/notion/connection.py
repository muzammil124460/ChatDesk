import httpx


class NotionConnection:

    BASE_URL = "https://api.notion.com/v1"

    def __init__(self, access_token: str):

        self.headers = {
            "Authorization": f"Bearer {access_token}",
            "Notion-Version": "2022-06-28",
            "Content-Type": "application/json"
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