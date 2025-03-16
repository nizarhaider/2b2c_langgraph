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

ACCOMODATIONS_SCHEMA = {
  "title": "accomodations_schema",
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "array",
  "items": {
    "type": "object",
    "properties": {
      "name": { "type": "string" },
      "location": { "type": "string" },
      "cost_per_night": { "type": "number", "minimum": 0 },
      "rating": { "type": "number", "minimum": 0, "maximum": 5 },
      "review_summary": { "type": "string" },
      "image_url": { "type": "string", "format": "uri" },
      "website_url": { "type": "string", "format": "uri" }
    },
    "required": ["name", "location", "cost_per_night"]
  }
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


