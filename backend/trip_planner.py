"""
AI Trip Planner Service - STANDARD OPENAI VERSION
Uses standard OpenAI API instead of Emergent wrapper.
"""
import os
import httpx
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import json
from openai import AsyncOpenAI  # Changed from emergentintegrations

# Models for Trip Planning (Kept exactly the same)
class TripPlanRequest(BaseModel):
    destination: str
    start_date: str
    end_date: str
    num_travelers: int = 1
    budget_preference: str = "moderate"
    currency: str = "INR"
    interests: List[str] = []
    accommodation_type: str = "hotel"
    include_flights: bool = True
    departure_city: Optional[str] = None
    compare_prices: bool = True

class WeatherData(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    precipitation_probability: int
    weather_description: str

class PriceComparison(BaseModel):
    category: str
    item_name: str
    prices: List[Dict[str, Any]]
    best_deal: Dict[str, Any]
    savings_potential: float

class DayItinerary(BaseModel):
    day: int
    date: str
    weather: Optional[WeatherData] = None
    activities: List[Dict[str, Any]]
    estimated_cost: float
    tips: str

class CostBreakdown(BaseModel):
    flights: float
    accommodation: float
    food: float
    activities: float
    transportation: float
    miscellaneous: float
    total_per_person: float
    total_group: float
    currency: str
    price_comparisons: List[PriceComparison] = []

class TripPlanResponse(BaseModel):
    destination: str
    start_date: str
    end_date: str
    num_days: int
    num_travelers: int
    best_time_to_visit: str
    weather_summary: str
    itinerary: List[DayItinerary]
    cost_breakdown: CostBreakdown
    travel_tips: List[str]
    packing_suggestions: List[str]
    local_customs: List[str]
    emergency_contacts: Dict[str, str]

class TripPlannerService:
    def __init__(self):
        # CHANGED: Use standard OPENAI_API_KEY
        self.api_key = os.environ.get('OPENAI_API_KEY')
        self.client = AsyncOpenAI(api_key=self.api_key)
        self.weather_base_url = "https://api.open-meteo.com/v1"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
        
    async def get_coordinates(self, location: str) -> Optional[Dict[str, float]]:
        """Get latitude and longitude for a location"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.geocoding_url}/search",
                    params={"name": location, "count": 1, "language": "en"}
                )
                data = response.json()
                if data.get("results"):
                    result = data["results"][0]
                    return {
                        "latitude": result["latitude"],
                        "longitude": result["longitude"],
                        "name": result.get("name", location),
                        "country": result.get("country", "")
                    }
        except Exception as e:
            print(f"Geocoding error: {e}")
        return None

    async def get_weather_forecast(self, latitude: float, longitude: float, start_date: str, end_date: str) -> List[WeatherData]:
        """Get weather forecast from Open-Meteo API"""
        weather_data = []
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.weather_base_url}/forecast",
                    params={
                        "latitude": latitude,
                        "longitude": longitude,
                        "daily": "temperature_2m_max,temperature_2m_min,precipitation_probability_max,weathercode",
                        "start_date": start_date,
                        "end_date": end_date,
                        "timezone": "auto"
                    }
                )
                data = response.json()
                
                if "daily" in data:
                    daily = data["daily"]
                    weather_codes = {
                        0: "Clear sky", 1: "Mainly clear", 2: "Partly cloudy", 3: "Overcast",
                        45: "Foggy", 48: "Depositing rime fog",
                        51: "Light drizzle", 53: "Moderate drizzle", 55: "Dense drizzle",
                        61: "Slight rain", 63: "Moderate rain", 65: "Heavy rain",
                        71: "Slight snow", 73: "Moderate snow", 75: "Heavy snow",
                        80: "Slight rain showers", 81: "Moderate rain showers", 82: "Violent rain showers",
                        95: "Thunderstorm", 96: "Thunderstorm with slight hail", 99: "Thunderstorm with heavy hail"
                    }
                    
                    for i, date in enumerate(daily.get("time", [])):
                        weather_data.append(WeatherData(
                            date=date,
                            temperature_max=daily["temperature_2m_max"][i],
                            temperature_min=daily["temperature_2m_min"][i],
                            precipitation_probability=daily["precipitation_probability_max"][i] or 0,
                            weather_description=weather_codes.get(daily["weathercode"][i], "Unknown")
                        ))
        except Exception as e:
            print(f"Weather API error: {e}")
        
        return weather_data

    async def generate_trip_plan(self, request: TripPlanRequest, user_id: str) -> TripPlanResponse:
        """Generate a comprehensive trip plan using Standard OpenAI"""
        
        coords = await self.get_coordinates(request.destination)
        location_info = f"{coords['name']}, {coords['country']}" if coords else request.destination
        
        weather_forecast = []
        if coords:
            weather_forecast = await self.get_weather_forecast(
                coords["latitude"],
                coords["longitude"],
                request.start_date,
                request.end_date
            )
        
        start = datetime.strptime(request.start_date, "%Y-%m-%d")
        end = datetime.strptime(request.end_date, "%Y-%m-%d")
        num_days = (end - start).days + 1
        
        weather_info = ""
        if weather_forecast:
            weather_info = "Weather forecast for the trip:\n"
            for w in weather_forecast:
                weather_info += f"- {w.date}: {w.weather_description}, {w.temperature_min}°C - {w.temperature_max}°C, {w.precipitation_probability}% rain chance\n"
        
        # Kept the exact same prompt logic as original
        system_prompt = """You are an expert travel planner AI with access to current pricing data. You create detailed, practical trip itineraries with accurate cost estimates and price comparisons across platforms.
        
        Your response MUST be valid JSON matching the structure provided in the user prompt. Do not include markdown formatting like ```json."""

        user_prompt = f"""Plan a detailed trip with the following details:

**Destination:** {location_info}
**Dates:** {request.start_date} to {request.end_date} ({num_days} days)
**Number of travelers:** {request.num_travelers}
**Budget preference:** {request.budget_preference}
**Interests:** {', '.join(request.interests) if request.interests else 'General sightseeing'}
**Accommodation type:** {request.accommodation_type}
**Include flights:** {'Yes, from ' + request.departure_city if request.include_flights and request.departure_city else 'No'}
**Currency:** {request.currency}

{weather_info}

Please provide a JSON response with this exact structure:
{{
    "best_time_to_visit": "string",
    "weather_summary": "string",
    "itinerary": [
        {{
            "day": 1,
            "date": "YYYY-MM-DD",
            "activities": [
                {{"time": "09:00", "activity": "Name", "description": "Details", "duration": "2 hours", "cost": 50, "location": "Place"}}
            ],
            "estimated_cost": 150,
            "tips": "Day tips"
        }}
    ],
    "cost_breakdown": {{
        "flights": 0, "accommodation": 0, "food": 0, "activities": 0, "transportation": 0, "miscellaneous": 0,
        "total_per_person": 0, "total_group": 0, "currency": "{request.currency}",
        "price_comparisons": []
    }},
    "travel_tips": [], "packing_suggestions": [], "local_customs": [], "emergency_contacts": {{}}
}}"""

        # CHANGED: Standard OpenAI Call
        try:
            response = await self.client.chat.completions.create(
                model="gpt-4o",  # or gpt-3.5-turbo
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={"type": "json_object"}
            )
            
            content = response.choices[0].message.content
            ai_plan = json.loads(content)
            
            # ... (Rest of parsing logic remains identical to original file) ...
            
            # Build itinerary
            itinerary = []
            for day_plan in ai_plan.get("itinerary", []):
                day_num = day_plan.get("day", 1)
                day_date = day_plan.get("date", request.start_date)
                
                day_weather = None
                for w in weather_forecast:
                    if w.date == day_date:
                        day_weather = w
                        break
                
                itinerary.append(DayItinerary(
                    day=day_num,
                    date=day_date,
                    weather=day_weather,
                    activities=day_plan.get("activities", []),
                    estimated_cost=day_plan.get("estimated_cost", 0),
                    tips=day_plan.get("tips", "")
                ))
            
            cost_data = ai_plan.get("cost_breakdown", {})
            price_comparisons = []
            for pc in cost_data.get("price_comparisons", []):
                price_comparisons.append(PriceComparison(
                    category=pc.get("category", ""),
                    item_name=pc.get("item_name", ""),
                    prices=pc.get("prices", []),
                    best_deal=pc.get("best_deal", {}),
                    savings_potential=pc.get("savings_potential", 0)
                ))
            
            cost_breakdown = CostBreakdown(
                flights=cost_data.get("flights", 0),
                accommodation=cost_data.get("accommodation", 0),
                food=cost_data.get("food", 0),
                activities=cost_data.get("activities", 0),
                transportation=cost_data.get("transportation", 0),
                miscellaneous=cost_data.get("miscellaneous", 0),
                total_per_person=cost_data.get("total_per_person", 0),
                total_group=cost_data.get("total_group", 0),
                currency=cost_data.get("currency", "USD"),
                price_comparisons=price_comparisons
            )
            
            return TripPlanResponse(
                destination=location_info,
                start_date=request.start_date,
                end_date=request.end_date,
                num_days=num_days,
                num_travelers=request.num_travelers,
                best_time_to_visit=ai_plan.get("best_time_to_visit", ""),
                weather_summary=ai_plan.get("weather_summary", ""),
                itinerary=itinerary,
                cost_breakdown=cost_breakdown,
                travel_tips=ai_plan.get("travel_tips", []),
                packing_suggestions=ai_plan.get("packing_suggestions", []),
                local_customs=ai_plan.get("local_customs", []),
                emergency_contacts=ai_plan.get("emergency_contacts", {})
            )
            
        except Exception as e:
            print(f"Trip planning error: {e}")
            raise ValueError("Failed to generate trip plan. Please try again.")

trip_planner = TripPlannerService()