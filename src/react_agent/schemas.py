"""Schemas."""

DESTINATION_SCHEMA={
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "Destination",
  "type": "object",
  "required": ["areasOfAttraction", "activities", "cost"],
  "properties": {
    "name": {
      "type": "string"
    },
    "areasOfAttraction": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "description": { "type": "string" }
        }
      }
    },
    "activities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "cost": { "type": "number" }
        }
      }
    },
    "cost": {
      "type": "object",
      "properties": {
        "currency": { "type": "string" },
        "averageDailyCost": { "type": "number" }
      }
    }
  }
}

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

FLIGHTS_AND_HOTELS = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "FlightsAndHotels",
  "type": "object",
  "required": ["dates", "airlines", "cost"],
  "properties": {
    "dates": {
      "type": "object",
      "properties": {
        "departureDate": { "type": "string", "format": "date" },
        "returnDate": { "type": "string", "format": "date" }
      }
    },
    "airlines": {
      "type": "array",
      "items": {
        "type": "string"
      }
    },
    "hotels": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "checkInDate": { "type": "string", "format": "date" },
          "checkOutDate": { "type": "string", "format": "date" }
        }
      }
    },
    "cost": {
      "type": "object",
      "properties": {
        "flights": { "type": "number" },
        "hotels": { "type": "number" },
        "total": { "type": "number" }
      }
    }
  }
}


ITINERARY_SCHEMA = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "day": { "type": "integer", "minimum": 1 },
    "date": { "type": "string", "format": "date" },
    "activities": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "name": { "type": "string" },
          "type": { "type": "string", "enum": ["attraction", "dining"] },
          "location": { "type": "string" },
          "cost": { "type": "number", "minimum": 0 },
          "rating": { "type": "number", "minimum": 0, "maximum": 5 },
          "review_summary": { "type": "string" },
          "image_url": { "type": "string", "format": "uri" },
          "website_url": { "type": "string", "format": "uri" },
          "weather_prediction": { "type": "string" },
          "tips": { "type": "string" }
        },
        "required": ["name", "type", "location", "cost"]
      }
    },
    "daily_cost": { "type": "number", "minimum": 0 }
  },
  "required": ["day", "activities", "daily_cost"]
}

ACCOMODATIONS_SCHEMA = {
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
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "destination": {"type": "string", "default": "Sri Lanka"},
    "number_of_people": { "type": "integer", "minimum": 1, "default": 1 },
    "number_of_adults": { "type": "integer", "minimum": 1, "default": 1 },
    "number_of_kids": { "type": "integer", "minimum": 0, "default": 0 },
    "number_of_days": { "type": "integer", "minimum": 1, "default": 7 },
    "budget": { "type": "number", "minimum": 0, "default": 1000 },
    "currency": { "type": "string", "default": "USD" },
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


