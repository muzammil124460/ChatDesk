from langgraph.graph import StateGraph,START,END
from ai.state.agent_state import Agent_state
from ai.agents.input import input_agent
from ai.agents.email import chat_controller
from langgraph.runtime import Runtime

import json
from pydantic_model.agent_contexts import Agent_context
from fastapi import HTTPException
from ai.tools.notion.notion_tool import create_notion_tools
from ai.agents.notion import notion_agent
from dotenv import load_dotenv
import os
load_dotenv()


def input_node(state):

    print("input node activated")

# user input 
    user_input = state.inputs

    ai_response = input_agent.invoke({

    "messages": [
        {"role": "user", "content": user_input}
    ]

})


    final_response = ai_response["messages"][-1].content

    print("final input res",final_response)

    converted = json.loads(final_response)

  
    return {
       "tasks": converted["tasks"]

    }

def supervised_node(state):
    print("supervised node activated")

    tasks = state.tasks

    for task in tasks:

        if task.status == "pending":

            state.current_task = task.task_id

            if task.agent == "gmail":
                return "email_node"

            if task.agent == "notion":
                 return "notion_node"


async def email_node(state, runtime: Runtime[Agent_context]):

    print("email node activated")

    try:

        
        response = await chat_controller(
                          runtime.context.credentials,
                          state.inputs
                      )

        

        updated_tasks = []

        for task in state.tasks:

            if task.task_id == state.current_task:

                updated_task = task.model_copy(
                    update={
                        "status": "completed",
                        "result": [str(response)]
                    }
                )

                updated_tasks.append(updated_task)

            else:
                updated_tasks.append(task)

        return {
            "tasks": updated_tasks,
            "result": {
                "gmail_agent": response
            },
            "completed_task": [state.current_task],
            "current_task": None
        }

    except Exception as e:

        print("Email error:", repr(e))

        raise HTTPException(
            status_code=500,
            detail="Error from email node"
        )
    

async def notion_node(state,runtime:Runtime[Agent_context]):
      print("motion node activated")

      print("email node activated")
      
      try:
      
              response = await notion_agent(
                          token= os.getenv("NOTION_TOKEN"),
                          query=state.inputs
                      )

              final_res =response["messages"][-1].content
      
              updated_tasks = []
      
              for task in state.tasks:
      
                  if task.task_id == state.current_task:
      
                      updated_task = task.model_copy(
                          update={
                              "status": "completed",
                              "result": [str(final_res)]
                          }
                      )
      
                      updated_tasks.append(updated_task)
      
                  else:
                      updated_tasks.append(task)
      
              return {
                  "tasks": updated_tasks,
                  "result": {
                      "notion_agent": final_res
                  },
                  "completed_task": [state.current_task],
                  "current_task": None
              }

      except Exception as e:

        print("Notion error:", repr(e))

        updated_tasks = []

        for task in state.tasks:

            if task.task_id == state.current_task:

                updated_task = task.model_copy(
                    update={
                        "status": "failed",
                        "error": str(e)
                    }
                )

                updated_tasks.append(updated_task)

            else:
                updated_tasks.append(task)

        return {
            "tasks": updated_tasks,
            "failed_task": [state.current_task],
            "current_task": None
        }
      
          













builder = StateGraph(
    Agent_state,
    context_schema=Agent_context
    )





builder.add_node("input_node",input_node)
builder.add_node("email_node",email_node)
builder.add_node("notion_node",notion_node)





builder.add_edge(START,"input_node")
builder.add_conditional_edges("input_node",supervised_node)

builder.add_edge("email_node",END)
builder.add_edge("notion_node",END)

graph = builder.compile()



