from langchain.agents import create_agent
from langchain_groq import ChatGroq


model =  ChatGroq(
    model=
)

email_agent = create_agent(

)



email_agent.invoke("hi")