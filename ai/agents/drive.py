
from langchain.agents import create_agent
from ai.model.llm_model import model
from ai.tools.drive.tools import get_drive_tools


async def drive_agent(credentials, query: str):

    # Create tools using the current user's credentials
    tools = get_drive_tools(credentials)

    # Create Drive ReAct agent
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="""
        You are a Google Drive assistant.

        Your job is to perform Google Drive operations based on the user's request.

        Available operations:
        - List files and folders
        - Search files by name
        - Upload files
        - Download files
        - Read Google Docs text content

        For searching files:
        - Use Google Drive API query syntax.
        - For filename search, use: name contains 'filename'
        - Do not add trashed = false because the search tool handles it.
        - Never wrap an existing Drive query inside another name contains condition.

        Instructions:
        1. Understand the user's request carefully.
        2. Select the appropriate tool.
        3. Use the tool only when required.
        4. If a file ID is required, search for the file first.
        5. Never invent file IDs or file information.
        6. Explain the tool result clearly to the user.
        7. If an operation fails, explain the error.
        8. Never claim an operation succeeded unless the tool confirms it.
        """
    )

    # Execute agent
    response = await agent.ainvoke({
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    })

    # Extract final response
    return response["messages"][-1].content
