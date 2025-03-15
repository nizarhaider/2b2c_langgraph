"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""
import json 

from datetime import datetime
from typing import Dict, List, Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from langchain_core.messages.base import BaseMessage
from datetime import datetime 

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS
from react_agent.prompts import DESTINATION_SEARCH_PROMPT, REFLECTION_PROMPT, DESTINATION_SUMMARIZER_PROMPT
from react_agent.schemas import DESTINATION_SCHEMA, FLIGHTS_AND_HOTELS, REFLECTION_SCHEMA
from langgraph.checkpoint.memory import MemorySaver

llm = init_chat_model("gpt-4o", model_provider="openai")


def destination_search(
    state: State
):
    """Search the web for given query"""  # noqa: D202, D415

    system_message = DESTINATION_SEARCH_PROMPT.format(
        todays_date=datetime.today().date(),
        current_destination_json=state.destination_json,
        feedback=state.destination_feedback
    )

    last_message = state.messages[-1]

    if isinstance(last_message, ToolMessage):
        return Command(
            goto="destination_summarizer"
        )

    llm_tools = llm.bind_tools(TOOLS)
    ai_msg = llm_tools.invoke(
                [
                    SystemMessage(content=system_message)
                ] +
                [
                    [msg for msg in state.messages if isinstance(msg, HumanMessage)][-1]
                ]
            )

    return {
        "messages": [ai_msg]
    }

def destination_summarizer(
        state: State
) -> dict:
    # print(state.messages)
    system_message = DESTINATION_SUMMARIZER_PROMPT

    llm_json = llm.with_structured_output(DESTINATION_SCHEMA)
    response = llm_json.invoke(
            [SystemMessage(content=system_message)] +
            [[msg for msg in state.messages if isinstance(msg, AIMessage)][-1]] +     
            [[msg for msg in state.messages if isinstance(msg, ToolMessage)][-1]]     
    )

    return {
        "destination_json": response
    }

def reflection_node(
    state: State
) -> Command[Literal['__end__', 'destination_search']]:
    """ Reflect on the web search agent output and return feedback."""

    llm_json = llm.with_structured_output(REFLECTION_SCHEMA)

    response = llm_json.invoke(
        [
            SystemMessage(content=REFLECTION_PROMPT.format(
                WEB_SEARCH_SCHEMA=DESTINATION_SCHEMA
            )), 
            AIMessage(content=json.dumps(state.destination_json))
        ] + [[msg for msg in state.messages if isinstance(msg, HumanMessage)][-1]]
    )

    if response['is_satisfactory']:
        return Command(
            goto='__end__'
        )
    else:
        return Command(
            goto='destination_search',
            update={
                "destination_feedback": response['feedback']
            }
        )

def human_node(state: State) -> Command[Literal['__end__', 'destination_search']]:

    feedback = interrupt(
        # Interrupt information to surface to the client.
        # Can be any JSON serializable value.
        {
            "task": "Does this look good?. Reply with yes to confirm",
            "llm_generated_summary": state.destination_json
        }
    )

    print(f'FEEDBACK IS {feedback}')

    # If satisfactory then return to end
    if feedback.lower() in ['yes', 'YES', 'y', 'Yes'] or len(feedback) < 5:
        return Command(
            goto='__end__'
        )
    else:
        # Update the state with the edited text
        return Command(
            resume={"destination_feedback": feedback},
            goto='destination_search',
            update={
            "destination_feedback": feedback
        })

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(destination_search)
builder.add_node(destination_summarizer)
builder.add_node(reflection_node)
# builder.add_node(human_node)
builder.add_node("tools", ToolNode(TOOLS))

builder.add_edge("__start__", "destination_search")

def route_model_output(state: State) -> Literal["destination_summarizer", "tools"]:
    """Determine the next node based on the model's output."""
    last_message = state.messages[-1]
    
    if isinstance(last_message, ToolMessage):
        return "destination_summarizer"
    
    # Otherwise we execute the requested actions
    return "tools"

builder.add_conditional_edges(
    "destination_search",
    route_model_output,
)
builder.add_edge("tools", "destination_search")
# builder.add_edge("destination_search", "destination_summarizer")
builder.add_edge("destination_summarizer", "reflection_node")
# builder.add_edge("reflection_node","human_node")

checkpointer = MemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=[],  
    interrupt_after=[],  
)
graph.name = "React Agent" 
