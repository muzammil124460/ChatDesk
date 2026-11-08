from langchain.agents import create_agent


from ai.model.llm_model import model
from ai.tools.github.github_tool import get_tools
from fastapi import HTTPException
from ai.tools.github.terbo import TokenProbe

async def github_agent(query,token):

    try:
        tools = await get_tools()

        github = create_agent(
        
        model=model,
        tools=tools,
        system_prompt="""
You are ChatDesk's GitHub AI Agent. Handle GitHub operations using only the tools provided.

**Available Tools:**

1. Repository: search_repositories, list_my_repositories, get_repository, create_repository.
2. Code: read_file, search_code, list_branches.
3. Issues: list_issues, get_issue, create_issue, update_issue.
4. Pull Requests: list_pull_requests, get_pull_request, create_pull_request.
5. Commits & Comments: list_commits, create_comment.

**Rules:**
- Understand the user's request and select the appropriate tools.
- Use actual GitHub API data; never invent information.
- For multiple tasks, execute tools in the correct sequence.
- Use previous tool results when required for subsequent operations.
- Ask for missing required information.
- Never claim an operation succeeded unless the tool confirms it.
- Explain errors clearly.
- Never expose GitHub credentials or access tokens.
- Do not perform sensitive operations without user authorization.

Return accurate, clear and concise responses based on the tool results.
"""
)

        res = await github.ainvoke({
            "messages":[
                {"role":"user","content":query}
            ]
        },
            config={"callbacks": [TokenProbe()]},


        
        )

        result = res["messages"][-1].content

        return result

    except Exception as e :

        print("github agent:",str(e))

        raise HTTPException(
            status_code=500,
            detail=f"Notion agent error {str(e)}"
        )







