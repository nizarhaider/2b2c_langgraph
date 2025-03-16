"""Define a custom Reasoning and Action agent.

Works with a chat model with tool calling support.
"""
import json 
import os

from datetime import datetime
from typing import Dict, List, Literal

from langchain.chat_models import init_chat_model
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage, trim_messages
from langchain_core.runnables import RunnableConfig
from langchain_openai import ChatOpenAI
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.types import interrupt, Command
from langchain_core.messages.base import BaseMessage
from datetime import datetime 

from pydantic import BaseModel, Field

from react_agent.configuration import Configuration
from react_agent.state import InputState, State
from react_agent.tools import TOOLS
from react_agent.prompts import VALIDATE_INPUT_PROMPT, GENERATE_ITINERARY_PROMPT, FORMAT_ITINERARY_PROMPT, REFLECTION_ITINERARY_PROMPT
from react_agent.schemas import ITINERARY_SCHEMA, USER_SCHEMA, ACCOMODATIONS_SCHEMA, REFLECTION_SCHEMA
from langgraph.checkpoint.memory import MemorySaver

llm = init_chat_model("gpt-4o", model_provider="openai")


def validate_user_query(state: State) -> dict:
    """Request more information from the user when the query is incomplete."""

    llm_json = llm.with_structured_output({
        "$schema": "https://json-schema.org/draft/2020-12/schema",
        "title": "validation_schema",
        "$id": "https://example.com/product.schema.json",
        "type": "object",
        "properties": {
            "is_valid": {
                "type": "boolean",
                "description": "Indicates whether the user query is valid or not."
            },
            "response_message": {
                "type": "string",
                "description": "Only fill if user query is invalid",
            }
        },
        "required": ["is_valid", "response_message"]
    })
    
    response = llm_json.invoke([SystemMessage(content=VALIDATE_INPUT_PROMPT)] + state.messages)

    if not response.get('is_valid'):

        # Interrupt the flow to get user input
        user_response = interrupt({"prompt": response.get('response_message')})
        
        # Add the user's response to messages and directly return to validation
        # This is crucial - we're using a direct return instead of a Command
        return {
            "messages": [
                AIMessage(content=response.get('response_message')),
                HumanMessage(content=user_response)
            ]
        }
    return {
        "messages": [AIMessage(content=json.dumps(response))]
    }

def update_user_profile(state: State) -> dict:

    llm_json = llm.with_structured_output(USER_SCHEMA)
    response = llm_json.invoke(
        [SystemMessage(
            content=f"""
            Use the message history to update the user profile. 
            Do not make any assumptions and be accurate at ALL TIMES.
            
            Here is the schema with its default values:
            {USER_SCHEMA}

            Use the default values for the fields if the user hasn't provided theirs.
            Assume all people are adults unless mentioned otherwise.

            Make sure to double check if user info doesn't have any typos.
            If currency not given, assume currency of destination.
            Today is {datetime.today().date().isoformat()}
            """
        ),
        *state.messages]
    )

    return {"user_profile": response}

async def research_itinerary(
    state: State
):
    """An agent that researches a travel itinerary based on users query."""  # noqa: D202, D415

    system_message = GENERATE_ITINERARY_PROMPT.format(
        todays_date=datetime.today().date(),
        USER_PROFILE=state.user_profile,
        FEEDBACK=state.itinerary_feedback,
        CURRENT_ITINERARY=state.itinerary
    )

    llm_tools = llm.bind_tools(TOOLS)

    trimmed_messages = trim_messages(
        messages= state.messages,
        include_system=False,
        max_tokens=20000,
        allow_partial=False,
        token_counter=ChatOpenAI(model="gpt-4o")
    )
    
    ai_msg = await llm_tools.ainvoke(
                [
                    SystemMessage(content=system_message)
                ] +
                trimmed_messages
            )
    
    return {
        "messages": [ai_msg]
    }

def format_itinerary(
        state: State
) -> dict:
    # print(state.messages)
    system_message = FORMAT_ITINERARY_PROMPT.format(
        USER_PROFILE=state.user_profile
    )

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

    llm_json = llm.with_structured_output(
        REFLECTION_SCHEMA
    )

    response = llm_json.invoke(
        [
            SystemMessage(content=REFLECTION_ITINERARY_PROMPT.format(
                ITINERARY_SCHEMA=ITINERARY_SCHEMA,
                USER_PROFILE=state.user_profile
            )), 
            state.messages[-1]
        ]
    )

    counter = state.iteration_counter

    if response['is_satisfactory'] or counter > 3:
        return Command(
            goto='__end__'
        )
    else:
        return Command(
            goto='research_itinerary',
            update={
                "itinerary_feedback": response['feedback'],
                "iteration_counter": counter + 1,
                "messages": [AIMessage(content=f'FEEDBACK based on last itinerary: {response['feedback']}')]
            }
        )





builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(validate_user_query)
builder.add_node(update_user_profile)

builder.add_node(research_itinerary)
builder.add_node(format_itinerary)
builder.add_node(review_itinerary)
builder.add_node("tools", ToolNode(TOOLS))

builder.add_edge("__start__", "validate_user_query")

def route_validation_logic(state: State) -> Literal["update_user_profile", "validate_user_query"]:
    """Determine the next node based on the model's output."""
    last_message = state.messages[-1]

    if isinstance(last_message, AIMessage):
        val_resp = json.loads(last_message.content)

        # If last message is Ai and is_valid then pass
        if val_resp.get('is_valid'):
            return "update_user_profile"
        
    return 'validate_user_query'
    

builder.add_conditional_edges(
    "validate_user_query",
    route_validation_logic,
)


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


builder.add_edge("update_user_profile", "research_itinerary")
builder.add_edge("tools", "research_itinerary")
builder.add_edge("format_itinerary", "review_itinerary")

checkpointer = MemorySaver()

graph = builder.compile(
    checkpointer=checkpointer,
    interrupt_before=[],  
    interrupt_after=[],  
)
graph.name = "React Agent" 
