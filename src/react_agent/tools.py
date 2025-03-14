"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""

from typing import Any, Callable, List, Optional, cast

from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg
from typing_extensions import Annotated
from langchain_core.tools.base import InjectedToolCallId

from react_agent.configuration import Configuration


async def search(
    query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
):
    """Search for general web results."""
    
    configuration = Configuration.from_runnable_config(config)
    wrapped = TavilySearchResults(max_results=configuration.max_search_results)
    result = await wrapped.ainvoke({"query": query})

    return {
        "result": cast(list[dict[str, Any]], result),
        "messages": [result]
    }
    


TOOLS: List[Callable[..., Any]] = [search]
