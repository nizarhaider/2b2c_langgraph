"""Default prompts used by the agent."""

DESTINATION_SEARCH_PROMPT = """
Your job is to search the web for travel destination related data based on the user query and output your result in JSON.
If there is feedback from the reflection agent, use it to improve your previous search results.

Todays date is {todays_date}.

The previous search results are:
{current_destination_json}

The feedback is:
{feedback}
"""

DESTINATION_SUMMARIZER_PROMPT = """
Your job is to summarize the destination search agents output into JSON format.
"""

REFLECTION_PROMPT = """
Your job is to reflect on the output of the web search agent compared to what the user queried for.

Keep in mind that the web search json schema is {WEB_SEARCH_SCHEMA} and so keep your critisisms within it.

After reflecting you will share feedback on how to improve the web search results.
"""

HOTELS_SEARCH_PROMPT = """
Your job is to look up for nearby hotels based on the locations in:
{destinations}.

Use your hotel booking tool to find the hotels and return their information. 
"""
