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
from react_agent.prompts import VALIDATE_INPUT_PROMPT, GENERATE_ITINERARY_PROMPT, FORMAT_ITINERARY_PROMPT, REFLECTION_ITINERARY_PROMPT, USER_ACCOMODATIONS_INPUT_PROMPT
from react_agent.schemas import ITINERARY_SCHEMA, USER_SCHEMA, ACCOMMODATION_SCHEMA, REFLECTION_SCHEMA
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
    
    response = llm_json.invoke([SystemMessage(content=VALIDATE_INPUT_PROMPT)] + state.itinerary_messages)

    if not response.get('is_valid'):

        # Interrupt the flow to get user input
        user_response = interrupt({"prompt": response.get('response_message')})
        
        # Add the user's response to messages and directly return to validation
        # This is crucial - we're using a direct return instead of a Command
        return {
            "itinerary_messages": [
                AIMessage(content=response.get('response_message')),
                HumanMessage(content=user_response)
            ]
        }
    return {
        "itinerary_messages": [AIMessage(content=json.dumps(response))]
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
        ] +
        [msg for msg in state.itinerary_messages if isinstance(msg, HumanMessage)]
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
        messages=state.itinerary_messages,
        include_system=False,
        max_tokens=50000,
        allow_partial=False,
        token_counter=ChatOpenAI(model="gpt-4o"),
    )
    
    ai_msg = await llm_tools.ainvoke(
                [
                    SystemMessage(content=system_message)
                ] +
                trimmed_messages
                )
    
    return {
        "itinerary_messages": [ai_msg]
    }

def format_itinerary(
        state: State
) -> dict:
    # print(state.itinerary_messages)
    system_message = FORMAT_ITINERARY_PROMPT.format(
        USER_PROFILE=state.user_profile
    )

    llm_json = llm.with_structured_output(ITINERARY_SCHEMA)
    response = llm_json.invoke(
            [SystemMessage(content=system_message)] +
            [state.itinerary_messages[-1]]
    )

    return {
        "itinerary": response
    }

def review_itinerary(
    state: State
) -> Command[Literal['validate_itinerary', 'research_itinerary']]:
    """ Reflect on the web search agent output and return feedback."""

    llm_json = llm.with_structured_output(
        REFLECTION_SCHEMA
    )

    response = llm_json.invoke(
        [
            SystemMessage(content=REFLECTION_ITINERARY_PROMPT.format(
                ITINERARY_SCHEMA=ITINERARY_SCHEMA,
                USER_PROFILE=state.user_profile,
                PREVIOUS_FEEDBACK=state.itinerary_feedback
            )), 
            state.itinerary_messages[-1]
        ]
    )

    counter = state.iteration_counter

    if response['is_satisfactory'] or counter >= 2:
        return Command(
            goto='validate_itinerary'
        )
    else:
        return Command(
            goto='research_itinerary',
            update={
                "itinerary_feedback": response['feedback'],
                "iteration_counter": counter + 1,
                "itinerary_messages": [AIMessage(content=f'FEEDBACK based on last itinerary: {response['feedback']}')]
            }
        )

def validate_itinerary(state: State) -> dict:
    """Request more information from the user when the query is incomplete."""

    last_message = state.itinerary_messages[-1]

    if not isinstance(last_message, HumanMessage):
        # Interrupt the flow to get user input
        user_response = interrupt({
            "prompt": f'Does this look good to you? \n\n{state.itinerary} \n\nReply with Yes to continue or provide some feedback to improve on',
            }
        )

    if isinstance(last_message, HumanMessage):
        llm_json = llm.with_structured_output({
            "$schema": "https://json-schema.org/draft/2020-12/schema",
            "title": "itinerary_validation_schema",
            "$id": "https://example.com/product.schema.json",
            "type": "object",
            "properties": {
                "is_approved": {
                    "type": "boolean",
                    "description": "Indicates whether the user COMPLETELY approves or denies."
                },
                "valid_feedback": {
                    "type": "boolean",
                    "description": "Check if the feedback is sufficient to make a revision or more information is needed."
                },
                "llm_response": {
                    "type": "string",
                    "description": "Prompt user for more information if unapproved with no feedback. Else just thank them and carry on."
                }
            },

            "required": ["is_approved"]
        })
        
        response = llm_json.invoke(
            [
                SystemMessage(
                content="""Y
                Your job is to check if the user approved the itinerary or not.
                If they didn't approve it then make sure there is clear feedback on the itinerary.
                IF there is no feedback prompt the user kindly for more feedback and set valid_feedback to false
                """),
                state.itinerary_messages[-1]
            ]
        )
        
        if not response.get('is_approved') and response.get('valid_feedback'):

            state.itinerary_feedback = last_message.content

            print(f'ITINERARY FEEDBACK UPDATED: {last_message.content}')

            return {
                "itinerary_messages": [AIMessage(content=json.dumps(response))],
                "itinerary_feedback": last_message.content
            }
        
        return {
            "itinerary_messages": [AIMessage(content=json.dumps(response))]
        }

    return {
        "itinerary_messages": [
            AIMessage(content=f"Does this look good to you? \n\n{state.itinerary}"),
            HumanMessage(content=user_response)
        ]
    }

# def get_accomodations_info(state: State) -> dict:
#     """Request more information from the user when the query is incomplete."""

#     last_message = state.itinerary_messages[-1]

#     if isinstance(last_message, AIMessage):
#         val_resp = json.loads(last_message.content)
#         if not val_resp.get('have_sufficient_info'):
#             user_response = interrupt({
#                 "prompt": val_resp.get("response_message"),
#             })

    
#     llm_json = llm.with_structured_output({
#         "$schema": "https://json-schema.org/draft/2020-12/schema",
#         "title": "validation_schema",
#         "$id": "https://example.com/product.schema.json",
#         "type": "object",
#         "properties": {
#             "have_sufficient_info": {
#                 "type": "boolean",
#                 "description": "Check to see if we have all the USER required columns"
#             },
#             "response_message": {
#                 "type": "string",
#                 "description": "Let the user know what more information we need casually. Keep it respectful.",
#             }
#         },
#         "required": ["is_valid", "response_message"]
#     })
#     response = llm.invoke(
#             [SystemMessage(content=USER_ACCOMODATIONS_INPUT_PROMPT.format(
#                 ITINERARY=state.itinerary,
#                 USER_PROFILE=state.user_profile,
#                 USER_ACCOMODATION_SCHEMA=ACCOMMODATION_SCHEMA,
#                 USER_ACCOMODATION=state.user_accomodation
#             ))] 
#         )

#     return {
#         "itinerary_messages": [AIMessage(content=response)]
#     }





###################BUILDERS#####################
builder = StateGraph(State, input=InputState, config_schema=Configuration)

# Define the two nodes we will cycle between
builder.add_node(validate_user_query)
builder.add_node(update_user_profile)

builder.add_node(research_itinerary)
builder.add_node(format_itinerary)
builder.add_node(review_itinerary)
builder.add_node(validate_itinerary)
# builder.add_node(get_accomodations_info)
builder.add_node("tools", ToolNode(TOOLS, messages_key="itinerary_messages"))

builder.add_edge("__start__", "validate_user_query")

def route_validation_logic(state: State) -> Literal["update_user_profile", "validate_user_query"]:
    """Determine the next node based on the model's output."""
    last_message = state.itinerary_messages[-1]

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
    last_message = state.itinerary_messages[-1]
    
    if isinstance(last_message, AIMessage):
        if '<FINAL_OUTPUT>' in last_message.content:
            return "format_itinerary"
    
    # Otherwise we execute the requested actions
    return "tools"

builder.add_conditional_edges(
    "research_itinerary",
    route_model_output,
)

def route_itinerary_validation_logic(state: State) -> Literal["validate_itinerary", "update_user_profile", "__end__"]:
    """Determine the next node based on the users output."""
    last_message = state.itinerary_messages[-1]

    if isinstance(last_message, AIMessage):
        val_resp = json.loads(last_message.content)

        if val_resp.get('is_approved'):
            return "__end__"

        if not val_resp.get('is_approved') and val_resp.get('valid_feedback'):
            return "update_user_profile"
    
        if not val_resp.get('is_approved') and not val_resp.get('valid_feedback'):
            return 'validate_itinerary'

    return 'validate_itinerary'
    
builder.add_conditional_edges(
    "validate_itinerary",
    route_itinerary_validation_logic
)

# def route_accomodation_validation_logic(state: State) -> Literal["get_accomodations_info", "__end__"]:
#     """Determine the next node based on the users output."""
#     last_message = state.itinerary_messages[-1]

#     if isinstance(last_message, AIMessage):
#         val_resp = json.loads(last_message.content)

#         if val_resp.get('have_sufficient_info'):
#             return "__end__"

#         if not val_resp.get('have_sufficient_info'):
#             return "get_accomodations_info"

#     return 'get_accomodations_info'

# builder.add_conditional_edges(
#     "get_accomodations_info",
#     route_accomodation_validation_logic
# )

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
