"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""
import json 

from datetime import datetime
from typing import Dict, List, Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from langchain_core.messages.base import BaseMessage
from datetime import datetime 

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS
from react_agent.prompts import DESTINATION_SEARCH_PROMPT, REFLECTION_PROMPT, DESTINATION_SUMMARIZER_PROMPT
from react_agent.schemas import DESTINATION_SCHEMA, FLIGHTS_AND_HOTELS, REFLECTION_SCHEMA

llm = init_chat_model("gpt-4o", model_provider="openai")


def destination_search(
    state: State
) -> Dict[str, List[AIMessage]]:
    """Search the web for given query"""  # noqa: D202, D415

    system_message = DESTINATION_SEARCH_PROMPT.format(
        todays_date=datetime.today().date(),
        current_destination_json=state.destination_json,
        feedback=state.destination_feedback
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
    

    for tool_call in ai_msg.tool_calls:
        print(tool_call)
        tool_messages = [ToolMessage(content=tool_call, tool_id=tool_call.get('id'))]
        print(tool_messages)

    return {"messages": [ai_msg]}

def destination_summarizer(
        state: State
) -> dict:
    system_message = DESTINATION_SUMMARIZER_PROMPT

    llm_json = llm.with_structured_output(DESTINATION_SCHEMA)

    response = llm_json.invoke(
            [SystemMessage(content=system_message)] +
            [[msg for msg in state.messages if isinstance(msg, AIMessage)][-1]]         
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
            goto='flight_and_hotel_search'
        )
    else:
        return Command(
            goto='destination_search',
            update={
                "destination_feedback": response['feedback']
            }
        )

def human_editing(state: State):

    result = interrupt(
        # Interrupt information to surface to the client.
        # Can be any JSON serializable value.
        {
            "task": "Review the output from the LLM and make any necessary edits.",
            "llm_generated_summary": state.destination_json
        }
    )

    # Update the state with the edited text
    return Command(
        resume={'edited_text': result["edited_text"]},
        update={
        "llm_generated_summary": result["edited_text"]
    })

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(destination_search)
builder.add_node(destination_summarizer)
builder.add_node(reflection_node)
# builder.add_node(human_editing)
builder.add_node("tools", ToolNode(TOOLS))

builder.add_edge("__start__", "destination_search")
builder.add_edge("destination_search", "destination_summarizer")
builder.add_edge("destination_summarizer", "reflection_node")

# Add a conditional edge to determine the next step after `call_model`
builder.add_edge("tools", "destination_search")
builder.add_edge("reflection_node","__end__")


graph = builder.compile(
    interrupt_before=[],  # Add node names here to update state before they're called
    interrupt_after=[],  # Add node names here to update state after they're called
)
graph.name = "React Agent" 
