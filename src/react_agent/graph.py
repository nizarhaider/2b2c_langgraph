"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""
import json 
import os

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
from react_agent.prompts import VALIDATE_INPUT_PROMPT, GENERATE_ITINERARY_PROMPT, FORMAT_ITINERARY_PROMPT, REFLECTION_ITINERARY_PROMPT
from react_agent.schemas import ITINERARY_SCHEMA, USER_SCHEMA, ACCOMODATIONS_SCHEMA, REFLECTION_SCHEMA
from langgraph.checkpoint.memory import MemorySaver


llm = init_chat_model("gpt-4o", model_provider="openai")


def validate_user_query(
        state: State
):
    """An agent that validates if the user query is relevant and has enough information to continue."""

    response = llm.invoke([SystemMessage(content=VALIDATE_INPUT_PROMPT)] + state.messages)
    print(response)
    return {'messages': response}

def request_additional_info(state: State) -> dict:
    """Request more information from the user when the query is incomplete."""
    # Extract the validation response
    last_message = state.messages[-1]
    validation_result = json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content
    
    # Generate a helpful response asking for more information
    missing_info = validation_result.get('response_message', 'more details about your travel plans')
    prompt = f"I need a bit more information to create your itinerary. {missing_info}?"
    
    # Interrupt the flow to get user input
    user_response = interrupt({"prompt": prompt})
    
    # Add the user's response to messages and directly return to validation
    # This is crucial - we're using a direct return instead of a Command
    return {
        "messages": [HumanMessage(content=user_response)]
    }

def research_itinerary(
    state: State
):
    """An agent that researches a travel itinerary based on users query."""  # noqa: D202, D415

    system_message = GENERATE_ITINERARY_PROMPT.format(
        todays_date=datetime.today().date(),
        current_itinerary=state.itinerary,
        feedback=state.itinerary_feedback
    )

    llm_tools = llm.bind_tools(TOOLS)
    ai_msg = llm_tools.invoke(
                [
                    SystemMessage(content=system_message)
                ] +
                [*state.messages]
            )

    return {
        "messages": [ai_msg]
    }

def format_itinerary(
        state: State
) -> dict:
    # print(state.messages)
    system_message = FORMAT_ITINERARY_PROMPT

    llm_json = llm.with_structured_output(ITINERARY_SCHEMA)
    response = llm_json.invoke(
            [SystemMessage(content=system_message)] +
            [state.messages[-1]]
    )

    return {
        "itinerary": response
    }

def review_itinerary(
    state: State
) -> Command[Literal['__end__', 'research_itinerary']]:
    """ Reflect on the web search agent output and return feedback."""

    llm_json = llm.with_structured_output(REFLECTION_SCHEMA)

    response = llm_json.invoke(
        [
            SystemMessage(content=REFLECTION_ITINERARY_PROMPT.format(
                ITINERARY_SCHEMA=ITINERARY_SCHEMA
            )), 
            AIMessage(content=json.dumps(state.itinerary))
        ] + [[msg for msg in state.messages if isinstance(msg, HumanMessage)][-1]]
    )

    if response['is_satisfactory']:
        return Command(
            goto='__end__'
        )
    else:
        return Command(
            goto='research_itinerary',
            update={
                "itinerary_feedback": response['feedback']
            }
        )

def human_node(state: State) -> Command[Literal['__end__', 'research_itinerary']]:

    feedback = interrupt(
        # Interrupt information to surface to the client.
        # Can be any JSON serializable value.
        {
            "task": "Does this look good?. Reply with yes to confirm",
            "llm_generated_summary": state.itinerary
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
            resume={"itinerary_feedback": feedback},
            goto='research_itinerary',
            update={
            "itinerary_feedback": feedback
        })

builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(validate_user_query)
builder.add_node(request_additional_info)
builder.add_node(research_itinerary)
builder.add_node(format_itinerary)
builder.add_node(review_itinerary)
builder.add_node("tools", ToolNode(TOOLS))

builder.add_edge("__start__", "validate_user_query")

def route_validation_logic(state: State) -> Literal["research_itinerary", "request_additional_info"]:
    """Determine the next node based on the model's output."""
    last_message = state.messages[-1]
    
    val_resp = json.loads(last_message.content) if isinstance(last_message.content, str) else last_message.content

    if val_resp.get('is_valid'):
        return "research_itinerary"
    
    return "request_additional_info"

builder.add_conditional_edges(
    "validate_user_query",
    route_validation_logic,
)

builder.add_edge("request_additional_info", "validate_user_query")

def route_model_output(state: State) -> Literal["format_itinerary", "tools"]:
    """Determine the next node based on the model's output."""
    last_message = state.messages[-1]
    
    if isinstance(last_message, AIMessage):
        if '<FINAL_OUTPUT>' in last_message.content:
            return "format_itinerary"
    
    # Otherwise we execute the requested actions
    return "tools"

builder.add_conditional_edges(
    "research_itinerary",
    route_model_output,
)

builder.add_edge("tools", "research_itinerary")
# builder.add_edge("research_itinerary", "format_itinerary")
builder.add_edge("format_itinerary", "review_itinerary")
# builder.add_edge("review_itinerary","human_node")

checkpointer = MemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=[],  
    interrupt_after=[],  
)
graph.name = "React Agent" 
