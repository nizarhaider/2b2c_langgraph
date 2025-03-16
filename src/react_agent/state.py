"""Define the state structures for the agent."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Sequence, List

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from langgraph.managed import IsLastStep
from typing_extensions import Annotated
from langchain_core.messages.base import BaseMessage


@dataclass
class InputState:
    """Defines the input state for the agent, representing a narrower interface to the outside world.

    This class is used to define the initial state and structure of incoming data.
    """
    
    messages: Annotated[List[BaseMessage], add_messages]


@dataclass
class State(InputState):
    """Represents the complete state of the agent, extending InputState with additional attributes.

    This class can be used to store any information needed throughout the agent's lifecycle.
    """
    
    user_profile: dict = field(default_factory=dict)
    itinerary: dict = field(default_factory=dict)
    itinerary_feedback: str = field(default="")
    iteration_counter: int = field(default=0)
