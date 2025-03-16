"""Schemas."""

REFLECTION_SCHEMA={
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Destination",
  "type": "object",
  "required": ["areasOfAttraction", "activities", "cost"],
  "properties": {
    "is_satisfactory": {
      "type": "boolean"
    },
    "feedback": {
      "type": "string"
    },
  }
}

ITINERARY_SCHEMA = {
  "title": "itinerary_schema",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "destination": { "type": "string" },
    "country": { "type": "string" },
    "trip_duration": { "type": "integer", "minimum": 1 },
    "days": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "day_number": { "type": "integer", "minimum": 1 },
          "attractions": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": "string" },
                "type": { "type": "string" },
                "location": { "type": "string" },
                "cost": { 
                  "oneOf": [
                    { "type": "number", "minimum": 0 },
                    { "type": "string", "pattern": "^\\$[0-9]+(\\.[0-9]{1,2})?$" }
                  ]
                },
                "rating": { "type": "number", "minimum": 0, "maximum": 5 },
                "reviews": { "type": "string" },
                "website_url": { "type": "string" },
                "image_url": { "type": "string" },
                "weather": { "type": "string" },
                "tips": { "type": "string" }
              },
              "required": ["name", "type", "location"]
            }
          },
          "dining": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "name": { "type": "string" },
                "type": { "type": "string" },
                "location": { "type": "string" },
                "cost": { 
                  "oneOf": [
                    { "type": "number", "minimum": 0 },
                    { "type": "string", "pattern": "^\\$[0-9]+(\\.[0-9]{1,2})?( per person)?$" }
                  ]
                },
                "rating": { "type": "number", "minimum": 0, "maximum": 5 },
                "reviews": { "type": "string" },
                "website_url": { "type": "string", "format": "uri" },
                "image_url": { "type": "string", "format": "uri" }
              },
              "required": ["name", "type", "location"]
            }
          },
          "daily_cost_estimate": { "type": "number", "minimum": 0 }
        },
        "required": ["day_number", "attractions", "dining"]
      }
    },
    "general_tips": {
      "type": "object",
      "properties": {
        "transportation": { "type": "string" },
        "must_try_dishes": { "type": "array", "items": { "type": "string" } },
        "cultural_etiquette": { "type": "string" },
        "safety_tips": { "type": "string" },
        "useful_phrases": { "type": "object", "additionalProperties": { "type": "string" } }
      }
    },
    "total_estimated_cost": { "type": "number", "minimum": 0 }
  },
  "required": ["destination", "country", "trip_duration", "days"]
}

ACCOMMODATION_SCHEMA = {
  "title": "accommodation_schema",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "dest_id": {
      "type": "string", 
      "description": "Destination ID retrieved from searchDestination endpoint"
    },
    "search_type": {
      "type": "string", 
      "description": "Search type retrieved from searchDestination endpoint",
      "default": "CITY"
    },
    "arrival_date": {
      "type": "string", 
      "format": "date", 
      "description": "Check-in date in yyyy-mm-dd format"
    },
    "departure_date": {
      "type": "string", 
      "format": "date", 
      "description": "Check-out date in yyyy-mm-dd format"
    },
    "adults": {
      "type": "integer", 
      "minimum": 1, 
      "default": 1, 
      "description": "Number of guests 18 years or older"
    },
    "children_age": {
      "type": "array",
      "items": {
        "type": "integer", 
        "minimum": 0, 
        "maximum": 17
      },
      "description": "List of ages for children under 18 years",
      "default": []
    },
    "room_qty": {
      "type": "integer", 
      "minimum": 1, 
      "default": 1, 
      "description": "Number of rooms required"
    },
    "currency_code": {
      "type": "string", 
      "description": "Currency code for pricing (e.g., USD, EUR, GBP)", 
      "default": "USD"
    },
    "price_min": {
      "type": "number",
      "description": "Minimum price filter for search",
      "minimum": 0
    },
    "price_max": {
      "type": "number",
      "description": "Maximum price filter for search",
      "minimum": 0
    },
  },
  "required": [
    "dest_id", 
    "search_type", 
    "arrival_date", 
    "departure_date"
  ]
}

USER_SCHEMA = {
  "title": "user_schema",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "destination": {"type": "string", "default": "Sri Lanka"},
    "number_of_people": { "type": "integer", "minimum": 1, "default": 1 },
    "number_of_adults": { "type": "integer", "minimum": 1, "default": 1 },
    "number_of_kids": { "type": "integer", "minimum": 0, "default": 0 },
    "number_of_days": { "type": "integer", "minimum": 1, "default": 7 },
    "budget": { "type": "number", "minimum": 0, "default": 1000 },
    "currency": { "type": "string" },
    "has_kids": { "type": "boolean", "default": False },
    "has_disability": { "type": "boolean", "default": False },
    "has_pets": { "type": "boolean", "default": False },
    "is_vegetarian": { "type": "boolean", "default": False },
    "preferences": {
      "type": "array",
      "items": { "type": "string" },
      "default": []
    },
    "origin_country": { "type": "string" }
  },
  "required": ["number_of_people", "budget", "number_of_days", "destination"]
}
