"""An Agent."""

from langgraph.prebuilt import create_react_agent
from langchain_openai import ChatOpenAI
from langgraph_supervisor import create_supervisor
from langchain_community.tools import TavilySearchResults

from datetime import datetime 


model = ChatOpenAI(
    model="gpt-4o-mini"
)

def add(a: float, b: float) -> float:
    """Add two numbers."""
    return a + b

def multiply(a: float, b: float) -> float:
    """Multiply two numbers."""
    return a * b

web_search = TavilySearchResults(
        max_results=5,
        search_depth="advanced",
        include_answer=True,
        include_raw_content=True,
        include_images=False,
        # include_domains=[...],
        # exclude_domains=[...],
        # name="...",            # overwrite default tool name
        # description="...",     # overwrite default tool description
        # args_schema=...,       # overwrite default args_schema: BaseModel
    )

math_agent = create_react_agent(
    model=model,
    tools=[add, multiply],
    name="math_expert",
    prompt="You are a math expert. Always use one tool at a time."
)

web_search_agent = create_react_agent(
    model=model,
    tools=[web_search],
    name="web_search_expert",
    prompt="You are a web search expert expected to help with up to date events."
)


# Create supervisor workflow
workflow = create_supervisor(
    [web_search_agent, math_agent],
    model=model,
    prompt=(
        "You are a team supervisor managing a web search expert and a weather api. "
        "For current events, use research_agent. "
        "For math problems, use math_agent."
    )
)

# graph = create_react_agent(
#     model,
#     tools=[],
#     prompt="You are a friendly, curious, geeky AI.",
# )
