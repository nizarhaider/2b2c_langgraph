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