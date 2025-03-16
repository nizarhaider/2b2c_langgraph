"""This module provides example tools for web scraping and search functionality.

It includes a basic Tavily search function (as an example)

These tools are intended as free examples to get started. For production use,
consider implementing more robust and specialized tools tailored to your needs.
"""
import os
from typing import Any, Callable, List, Optional, cast

import aiohttp
import requests
from exa_py import Exa
from langchain_community.tools import GooglePlacesTool
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import InjectedToolArg, tool
from tavily import TavilyClient, AsyncTavilyClient
from typing_extensions import Annotated

from react_agent.configuration import Configuration

exa = Exa(api_key=os.environ["EXA_API_KEY"])
client = AsyncTavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


async def query_google_places(
        query: str,
        config: Annotated[RunnableConfig, InjectedToolArg]
) -> dict:
    """
    Queries the Google Places API using a text-based search to find places related to the provided query.

    This function interacts with the Google Places API and returns a list of places 
    matching the query string, along with additional details about each place. The API 
    response contains information such as location, rating, price range, photos, business status, 
    and more.

    Parameters:
    - query (str): The search query, typically a name or description of a place or landmark.
    - config (RunnableConfig): Configuration settings used to authenticate the API request. This 
      includes the API key and other relevant parameters for the Google Places API.

    Returns:
    - dict: The API response as a dictionary containing a list of places with detailed information.
      The data includes the place name, location, rating, address, and additional metadata like photos, 
      links to Google Maps, and business status.
      
    Example:
    >>> query_google_places("Colosseum Rome")
    {
        "results": [
            {
                "name": "Colosseum",
                "formatted_address": "Piazza del Colosseo, 1, 00184 Roma RM, Italy",
                "rating": 4.7,
                "price_level": 2,
                "types": ["tourist_attraction", "point_of_interest", "establishment"],
                "photos": [{"photo_reference": "A1z...", "width": 1024, "height": 768}],
                "website_uri": "https://www.coopculture.it/en/colosseo-e-shop.cfm"
            },
            ...
        ]
    }

    Notes:
    - The results are limited to a maximum of 5 places per query.
    - The search includes detailed attributes for each place, including user ratings, pricing details, 
      website URLs, and more.
    """  # noqa: D202, D212, D401
    async with aiohttp.ClientSession() as session:

        configuration = Configuration.from_runnable_config(config)

        url = "https://places.googleapis.com/v1/places:searchText"
        headers = {
            'X-Goog-Api-Key': configuration.google_places_api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
            "X-Goog-FieldMask": "places.attributions,places.id,places.displayName,places.googleMapsLinks,places.formattedAddress,places.businessStatus,places.types,places.location,places.internationalPhoneNumber,places.rating,places.priceLevel,places.priceRange,places.websiteUri,places.userRatingCount,places.websiteUri,places.goodForChildren,places.liveMusic,places.paymentOptions,places.servesBeer,places.servesVegetarianFood,places.reviews"
        }
        data = {
            "textQuery": query,
            "pageSize": 5
        }

        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()
            return await response.json()         

async def tavily_web_search(
        query: str,
        config: Annotated[RunnableConfig, InjectedToolArg]
) -> dict:
    """
    Performs a general web search using the Tavily search engine to retrieve trusted and comprehensive results.

    This function utilizes the Tavily search engine, which is designed to provide highly relevant, 
    accurate, and up-to-date results, especially for queries related to current events, travel destinations, 
    or other frequently changing information. The results include articles, blog posts, and other web content 
    that match the search query.

    Parameters:
    - query (str): The search query string, which can be a question or a topic that the user wants to research.
    - config (RunnableConfig): Configuration settings for the search, including parameters like the 
      maximum number of results to fetch and other filters for refining the search.

    Returns:
    - Optional[list[dict[str, Any]]]: A list of dictionaries containing the search results. Each dictionary 
      represents a single result and may contain keys such as the title, snippet, URL, and other metadata for 
      each item. If no results are found, the function will return `None`.

    Example:
    >>> tavily_web_search("best family-friendly attractions in Sri Lanka")
    [
        {
            "title": "Top 10 Family-Friendly Attractions in Sri Lanka",
            "snippet": "Sri Lanka offers a variety of family-friendly attractions, from wildlife safaris to beach resorts.",
            "url": "https://www.example.com/family-friendly-attractions-sri-lanka",
            "source": "Travel Blog"
        },
        ...
    ]

    Notes:
    - The search results may include a mix of sources, such as blogs, news articles, and other online content.
    - The search engine is optimized for current, real-time information and highly relevant content.
    - The results are enriched with extra details such as snippets, URLs, and source information to help users find valuable resources.
    """  # noqa: D202, D212, D401

    configuration = Configuration.from_runnable_config(config)

    response = await client.search(
        query=query,
        include_images=True,
        max_results=configuration.max_search_results,
        time_range='year'
    )
    return response

# async def tavily_web_search(
#     query: str, *, config: Annotated[RunnableConfig, InjectedToolArg]
# ) -> Optional[list[dict[str, Any]]]:
#     """
#     Performs a general web search using the Tavily search engine to retrieve trusted and comprehensive results.

#     This function utilizes the Tavily search engine, which is designed to provide highly relevant, 
#     accurate, and up-to-date results, especially for queries related to current events, travel destinations, 
#     or other frequently changing information. The results include articles, blog posts, and other web content 
#     that match the search query.

#     Parameters:
#     - query (str): The search query string, which can be a question or a topic that the user wants to research.
#     - config (RunnableConfig): Configuration settings for the search, including parameters like the 
#       maximum number of results to fetch and other filters for refining the search.

#     Returns:
#     - Optional[list[dict[str, Any]]]: A list of dictionaries containing the search results. Each dictionary 
#       represents a single result and may contain keys such as the title, snippet, URL, and other metadata for 
#       each item. If no results are found, the function will return `None`.

#     Example:
#     >>> tavily_web_search("best family-friendly attractions in Sri Lanka")
#     [
#         {
#             "title": "Top 10 Family-Friendly Attractions in Sri Lanka",
#             "snippet": "Sri Lanka offers a variety of family-friendly attractions, from wildlife safaris to beach resorts.",
#             "url": "https://www.example.com/family-friendly-attractions-sri-lanka",
#             "source": "Travel Blog"
#         },
#         ...
#     ]

#     Notes:
#     - The search results may include a mix of sources, such as blogs, news articles, and other online content.
#     - The search engine is optimized for current, real-time information and highly relevant content.
#     - The results are enriched with extra details such as snippets, URLs, and source information to help users find valuable resources.
#     """  # noqa: D212, D401
#     configuration = Configuration.from_runnable_config(config)
#     wrapped = TavilySearchResults(max_results=configuration.max_search_results, include_images=True)
#     result = await wrapped.ainvoke({"query": query})
#     return cast(list[dict[str, Any]], result)


# def exa_web_search(query: str):
    """Search for webpages based on the query and retrieve their contents."""
    return exa.search_and_contents(
        query, use_autoprompt=True, num_results=10, text=True, highlights=True
    )

async def get_hotel_currencies(
        config: Annotated[RunnableConfig, InjectedToolArg],
) -> dict:
    """
    Get available hotel currencies from this API 
    
    Returns:
    --------
    dict
        JSON response containing currency code results.
    """  # noqa: D212, D415
    async with aiohttp.ClientSession() as session:
        configuration = Configuration.from_runnable_config(config)
        
        url = "https://booking-com15.p.rapidapi.com/api/v1/meta/getCurrency"
    
        headers = {
            "x-rapidapi-key": configuration.booking_api_key,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

        async with session.get(url, headers=headers) as response:
            response.raise_for_status()
            return await response.json()

async def get_hotel_location_id(
        location_query: str,
        config: Annotated[RunnableConfig, InjectedToolArg]
) -> dict:
    """Use to get all hotel_location_ids based on location query."""
    async with aiohttp.ClientSession() as session:

        configuration = Configuration.from_runnable_config(config)

        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchDestination"

        querystring = {"query":{location_query}}

        headers = {
            "x-rapidapi-key": configuration.booking_api_key,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

        async with session.get(url, headers=headers, params=querystring) as response:
            response.raise_for_status()

            return await response.json() 

async def get_hotel_ids(
        config: Annotated[RunnableConfig, InjectedToolArg],
        dest_id: str,
        search_type: str,
        arrival_date: str,
        departure_date: str,
        adults: int = 1,
        children_ages: list[int] = None,
        room_qty: int = 1,
        currency_code: str = None
) -> dict:
    """
    Get hotel search results based on location and search criteria.
    
    Parameters:
    -----------
    config : RunnableConfig
        Configuration object containing API keys and settings.
    dest_id : str
        Destination ID retrieved from 'api/v1/hotels/searchDestination' endpoint.
    search_type : str
        Search type retrieved from 'api/v1/hotels/searchDestination' endpoint.
    arrival_date : str
        Check-in date in 'yyyy-mm-dd' format.
    departure_date : str
        Check-out date in 'yyyy-mm-dd' format.
    adults : int, optional
        Number of guests who are 18 years of age or older. Default is 1.
    children_age : list[int], optional
        List of ages for children under 18 years. For example: [0, 1, 17].
    room_qty : int, optional
        Number of rooms required. Default is 1.
    currency_code : str, optional
        Currency code for pricing. Can be retrieved from 'api/v1/meta/getCurrency' endpoint.
        
    Returns:
    --------
    dict
        JSON response containing hotel search results.
    """  # noqa: D212
    async with aiohttp.ClientSession() as session:
        configuration = Configuration.from_runnable_config(config)
        
        url = "https://booking-com15.p.rapidapi.com/api/v1/hotels/searchHotels"
        

        querystring = {
            "dest_id": dest_id,
            "search_type": search_type,
            "arrival_date": arrival_date,
            "departure_date": departure_date,
            "adults": adults,
            "room_qty": room_qty,
            "page_number": "1",
            "units": "metric",
            "temperature_unit": "c",
            "languagecode": "en-us",
        }
        
        # Add optional parameters only if they are provided
        if children_ages:
            querystring["children_age"] = children_ages
        if currency_code:
            querystring["currency_code"] = currency_code

        headers = {
            "x-rapidapi-key": configuration.booking_api_key,
            "x-rapidapi-host": "booking-com15.p.rapidapi.com"
        }

        async with session.get(url, headers=headers, params=querystring) as response:
            response.raise_for_status()
            return await response.json()

TOOLS: List[Callable[..., Any]] = [tavily_web_search, query_google_places]