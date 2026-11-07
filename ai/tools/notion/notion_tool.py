
from fastapi import HTTPException
from langchain_core.tools import tool
from ai.tools.notion.connection import NotionConnection


async def create_notion_tools(access_token: str):

    # Common helper: Notion API request handle karega
    async def call_notion(method: str, endpoint: str, **kwargs):

        notion = NotionConnection(access_token)

        try:
            result = await notion.request(
                method=method,
                endpoint=endpoint,
                **kwargs
            )
            return result

        finally:
            await notion.close()

    # 1. SEARCH PAGES
    @tool
    async def search_pages(query: str) -> dict:
        """Search for pages in the user's Notion workspace."""

        return await call_notion(
            "POST",
            "/search",
            json={
                "query": query,
                "page_size": 10,
                "filter": {
                    "property": "object",
                    "value": "page"
                }
            }
        )

    # 2. READ PAGE
    @tool
    async def read_page(page_id: str) -> dict:
        """Read the details and properties of a Notion page."""

        return await call_notion(
            "GET",
            f"/pages/{page_id}"
        )

    # 3. GET PAGE BLOCKS
    @tool
    async def get_page_blocks(
        page_id: str,
        page_size: int = 100
    ) -> dict:
        """Read the content blocks inside a Notion page."""

        return await call_notion(
            "GET",
            f"/blocks/{page_id}/children",
            params={
                "page_size": page_size
            }
        )

    # 4. CREATE PAGE
    @tool
    async def create_page(
        parent_page_id: str,
        title: str,
        content: str = ""
    ) -> dict:
        """Create a new page inside an existing Notion page."""

        body = {
            "parent": {
                "page_id": parent_page_id
            },
            "properties": {
                "title": {
                    "title": [
                        {
                            "text": {
                                "content": title
                            }
                        }
                    ]
                }
            }
        }

        if content:
            body["children"] = [
                {
                    "object": "block",
                    "type": "paragraph",
                    "paragraph": {
                        "rich_text": [
                            {
                                "type": "text",
                                "text": {
                                    "content": content
                                }
                            }
                        ]
                    }
                }
            ]

        return await call_notion(
            "POST",
            "/pages",
            json=body
        )

    # 5. UPDATE PAGE
    @tool
    async def update_page(
        page_id: str,
        title: str
    ) -> dict:
        """Update the title of a Notion page."""

        return await call_notion(
            "PATCH",
            f"/pages/{page_id}",
            json={
                "properties": {
                    "title": {
                        "title": [
                            {
                                "text": {
                                    "content": title
                                }
                            }
                        ]
                    }
                }
            }
        )

    # 6. APPEND BLOCK
    @tool
    async def append_block(
        page_id: str,
        content: str
    ) -> dict:
        """Append a paragraph of text to an existing Notion page."""

        block = {
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [
                    {
                        "type": "text",
                        "text": {
                            "content": content
                        }
                    }
                ]
            }
        }

        return await call_notion(
            "PATCH",
            f"/blocks/{page_id}/children",
            json={
                "children": [block]
            }
        )

    # 7. SEARCH DATABASE
    @tool
    async def search_database(query: str) -> dict:
        """Search for databases in the user's Notion workspace."""

        return await call_notion(
            "POST",
            "/search",
            json={
                "query": query,
                "page_size": 10,
                "filter": {
                    "property": "object",
                    "value": "database"
                }
            }
        )

    # 8. CREATE DATABASE ENTRY
    @tool
    async def create_database_entry(
        database_id: str,
        properties: dict
    ) -> dict:
        """
        Create a new entry inside a Notion database.

        properties must match the database's property schema.
        """

        return await call_notion(
            "POST",
            "/pages",
            json={
                "parent": {
                    "database_id": database_id
                },
                "properties": properties
            }
        )

    # All 8 tools return as a list
    return [
        search_pages,
        read_page,
        get_page_blocks,
        create_page,
        update_page,
        append_block,
        search_database,
        create_database_entry
    ]
