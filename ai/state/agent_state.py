from langgraph.graph import StateGraph
from pydantic import BaseModel,Field
from typing import Any

class Tasks(BaseModel):
    task_id:str
    agent:str
    instruction:str
    status:str
    result:list[str] | None= None
    error:list[str] | None = None

class Agent_state(BaseModel):

    inputs : str

    tasks : list[Tasks] = Field(default_factory=list)

    current_task : str | None = None

    completed_task : list[str] | None = None

    failed_task : list[str] | None = None

    result : dict[str , Any]=Field(default_factory=dict)

    # human approval

    approval_required:bool = False
    approval_status : str | None=None

    finale_result : str | None = None
    error_result : str | None = None


