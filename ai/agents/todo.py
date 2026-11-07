from langchain.agents import create_agent


from ai.model.llm_model import model


todo_agent = create_agent(
    model=model,
    system_prompt="""
just return some small output by the name of todo agent
"""
)