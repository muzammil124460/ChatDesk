
from ai_main import graph
from fastapi import HTTPException
from pydantic_model.agent_contexts import Agent_context



async def chat_controller(query,credentials):

    print("chat controller activated")
    print("query",query.query,"type",type(query.query))

    

    try:


        context = Agent_context(credentials)

        response = await graph.ainvoke({
            "inputs": query.query,
            
            "approval_required": False
        },

        context=context
) 
       


        return response["result"]
    except Exception as e:

        print("AI error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="AI execution failed"
        )
    

