"""Prompts used by the agent."""

VALIDATE_INPUT_PROMPT = """
Your job is to perform the following checks:

- Relevant to travelling
- Has mentioned all of ["number_of_people", "budget", "number_of_days", "destination"] atleast.

Prompt the user again in cases of missing or irrelevant information. 

If the user query satisfies all checks then return a json response like:
{
    "is_valid": true
}

If any check fails then return the JSON response:
{
    "is_valid": false,
    "response_message": ""
}
"""

GENERATE_ITINERARY_PROMPT = """
You are an agent tasked with gathering detailed travel data to create a complete itinerary for a user.

### Steps:
1. **User Query Understanding**:
    - The user has provided a destination, a general number of days, and a budget.
    - Your job is to find and collect the most relevant information that will be needed for the **itinerary summarizer** to later structure the itinerary into a detailed plan.

2. **Attractions Search**:
    - Search for **attractions** based on the user's destination, preferences (e.g., family-friendly, adventure, cultural), and the time of year.
    - For each attraction, collect the following details:
        - **Name** of the attraction
        - **Type** (e.g., cultural, adventure, natural)
        - **Location** (city, country)
        - **Cost** (if applicable)
        - **Rating** (e.g., 4.5 stars)
        - **Review summary** (short description or sentiment from reviews)
        - **Website URL** (for booking, more information)
        - **Image URL** (for display purposes)
        - **Seasonal weather prediction** (just a general prediction based on the season)
        - **Tips** for visiting (e.g., best time to visit, things to know, etc.)

3. **Dining Search**:
    - Search for **dining options** based on the destination and the user’s preferences.
    - For each restaurant or dining spot, gather the following details:
        - **Name** of the restaurant
        - **Type** (e.g., casual, fine dining, local cuisine)
        - **Location** (city, country)
        - **Cost** (estimated meal cost per person)
        - **Rating** (e.g., 4.7 stars)
        - **Review summary** (short description or sentiment from reviews)
        - **Website URL** (for booking or more information)
        - **Image URL** (for display purposes)

4. **General Tips and Advice**:
    - Provide any **general tips or advice** for the destination, activities, or dining. This could include:
        - Travel advice (e.g., local transportation, must-try dishes, etc.)
        - Safety tips
        - Cultural etiquette
        - Useful phrases or local customs to know

5. **Organize by Day**:
    - Organize the information into a rough daily schedule with the following structure:
        - **Attractions**: List at least **2-3 attractions per day** (morning, afternoon, evening options).
        - **Dining**: Suggest **2-3 dining options per day** that are close to the attractions.
        - For each day, make sure you distribute the activities and dining options evenly, considering travel time between them.

6. **Include Budget Information**:
    - Include a rough cost breakdown for **attractions** and **dining** for each day (rough cost estimate in the user’s currency or in USD).
    - You do not need to calculate the total budget at this step, just provide estimated costs for each activity.

7. **Provide Image URLs**:
    - For each **attraction** and **dining option**, make sure to include a **link to an image** (ideally an external URL for easy access). These images will be used in the final itinerary for display purposes.

8. **Expected Weather**:
    - Provide **seasonal weather predictions** for each activity location. For example, mention if it will be typically sunny, rainy, or chilly during that time of year. This will help the summarizer decide what to include in the itinerary.

### Example Output (Raw Data):
Your response should contain a detailed list of all the attractions, dining options, tips, and relevant information organized by day (7 days in total), like the example below:

Day 1:
- **Attractions**:
    1. **Attraction Name** - Type: Cultural, Location: City, Country, Cost: $20, Rating: 4.5, Reviews: "A beautiful historic site.", Website: [link], Image: [image link], Weather: "Sunny, pleasant", Tips: "Arrive early to avoid crowds."
    2. **Attraction Name** - Type: Natural, Location: City, Country, Cost: Free, Rating: 4.7, Reviews: "Fantastic view of the mountains.", Website: [link], Image: [image link], Weather: "Mild, occasional rain", Tips: "Bring a jacket for the evening breeze."
    
- **Dining**:
    1. **Restaurant Name** - Type: Local Cuisine, Location: City, Country, Cost: $30, Rating: 4.8, Reviews: "Authentic flavors.", Website: [link], Image: [image link]
    2. **Restaurant Name** - Type: Casual, Location: City, Country, Cost: $20, Rating: 4.6, Reviews: "Great for families.", Website: [link], Image: [image link]

Day 2:
- (Continue with the same format)

...

### Final Output Format:
- Do **not** structure this in JSON format yet. This is the raw data that will be passed to the summarizer.
- Keep the data in an easy-to-read, human-readable format (you can use bullet points or numbered lists for easy understanding).

### Context:
- The user's budget, preferences, and destination details are provided.
- You will be passing this raw data to the summarizer agent, which will organize it into a structured itinerary.
- Your output must be as detailed as possible with accurate and relevant information for each attraction and dining option.

### Today's date:
{todays_date}

### User’s Destination Information:
{current_itinerary}

### Reflection Agent’s Feedback:
{feedback}

If the feedback contains suggestions for improvement, revise the itinerary accordingly.
"""

FORMAT_ITINERARY_PROMPT = """
Your task is to summarize the detailed raw travel data into a structured 7-day itinerary for the user. You will be working with the information provided by the generate_itinerary agent.

### Steps:
1. **Day-by-Day Breakdown**:
    - Organize the collected attractions and dining options by day. For each day:
        - **Attractions**: List at least **2-3 attractions per day** with the following details:
            - Name, Type (e.g., cultural, adventure, natural), Location, Cost, Rating, Review Summary, Weather Prediction, Tips, Image URL, Website URL.
        - **Dining**: Suggest **2-3 dining options per day** that are close to the attractions with the following details:
            - Name, Type (e.g., casual, fine dining, local cuisine), Location, Cost, Rating, Review Summary, Image URL, Website URL.

2. **Budget Alignment**:
    - Ensure the total cost of each day's activities (including attractions and dining) aligns with the user's budget. Provide a **rough cost breakdown** for each day in USD or the user's preferred currency.

3. **Daily Structure**:
    - Distribute activities and dining options evenly across the day (morning, afternoon, and evening). Ensure that the **attractions** and **dining** do not overlap in time and are geographically feasible for the user to visit.
    
4. **Tips and Advice**:
    - Include any general **tips** for the destination or specific **tips** for visiting each attraction or dining spot.

5. **Weather Predictions**:
    - Include **seasonal weather predictions** for each attraction (e.g., sunny, rainy, chilly), helping the user understand what kind of weather to expect during their visit.

6. **User Preferences**:
    - Incorporate any **user preferences** such as family-friendly activities, luxury experiences, or adventure into the itinerary.

### Final Output Format:
Your output should be a **structured JSON format**.

Ensure that all the required information (attractions, dining, tips, etc.) is included in the output.
"""

REFLECTION_ITINERARY_PROMPT = """
You are tasked with evaluating the output of the travel itinerary summarizer based on the user’s query and preferences.

Use the tools at your disposal to retrieve the information.

Here is what the json schema is supposed to look like:

{ITINERARY_SCHEMA}


### Points to Reflect On:
1. **Alignment with User's Budget**:
    - Does the itinerary fit within the user's provided **budget** for each day (activities + dining)?
    - Ensure that the total **daily cost** is reasonable and matches the user's expectations.
    
2. **Preferences**:
    - Did the summarizer respect the user’s preferences (e.g., family-friendly, luxury, budget, adventure)?
    - Are the activities and dining options suitable for the family’s needs (if applicable)?

3. **Balance of Activities**:
    - Is there a **good balance** of activities (attractions) and dining (e.g., not too many attractions in one day, sufficient time for dining)?
    - Are the **daily itineraries** evenly structured (morning, afternoon, evening)?

4. **Weather Predictions**:
    - Are the **seasonal weather predictions** for each attraction relevant and correctly aligned with the user's expected travel time?

5. **Quality of Suggestions**:
    - Are the **attractions** and **dining options** highly rated, appropriately located, and suitable for the type of trip the user is planning?

6. **Completeness**:
    - Are all the necessary details (cost, rating, weather, tips) included for each activity and dining spot?
    - Is there any missing or insufficient information that would be helpful for the user?

### Feedback:
- Based on your reflections, provide feedback to help improve the summarizer's output. 
- If needed, suggest **adjustments to the activities** or **rearranging the itinerary** to better fit the user’s budget, preferences, or time constraints.

"""




HOTELS_SEARCH_PROMPT = """
Your job is to look up for nearby hotels based on the locations in:
{destinations}.

Use your hotel booking tool to find the hotels and return their information. 
"""
