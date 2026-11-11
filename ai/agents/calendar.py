
from langchain.agents import create_agent
from ai.model.llm_model import model
from ai.tools.calendar.tools import get_calendar_tools


async def calendar_agent(credentials, query: str):

    # 1. Current user ke credentials se tools create honge
    tools = get_calendar_tools(credentials)

    # 2. Calendar agent create hoga
    agent = create_agent(
        model=model,
        tools=tools,
        system_prompt="""
        You are a Google Calendar assistant.

        Your job is to help users manage their Google Calendar.

        You can:
        1. List upcoming events.
        2. Search events using keywords.
        3. Create new events.
        4. Update existing events.
        5. Delete existing events.

        Instructions:

        - Always use the appropriate tool for calendar operations.
        - Never invent event dates, times, or event IDs.
        - Use search_events or list_events to find an existing event
          before updating or deleting it.
        - For create_event, use the exact date and time provided by
          the user.
        - Use Asia/Kolkata timezone by default.
        - If required information is missing, ask the user instead
          of guessing.
        - Never claim an operation succeeded if the tool returned
          an error.
        - Deletion must follow the application's approval flow.
        """
    )

    # 3. User query agent ko send hogi
    response = await agent.ainvoke({
        "messages": [
            {"role": "user", "content": query}
        ]
    })

    # 4. Final response return hogi
    return response["messages"][-1].content
