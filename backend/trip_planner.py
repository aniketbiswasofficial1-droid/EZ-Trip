"""
AI Trip Planner Service
Uses OpenAI GPT-4o for intelligent trip planning with weather, costs, and itinerary generation.
Includes price comparison across multiple platforms via web search.
"""
import os
import httpx
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import json
import asyncio
from emergentintegrations.llm.chat import LlmChat, UserMessage

# Models for Trip Planning
class TripPlanRequest(BaseModel):
    destination: str
    start_date: str  # YYYY-MM-DD
    end_date: str    # YYYY-MM-DD
    num_travelers: int = 1
    budget_preference: str = "moderate"  # budget, moderate, luxury
    currency: str = "INR"  # Default to INR for India focus
    interests: List[str] = []  # e.g., ["adventure", "culture", "food", "relaxation"]
    accommodation_type: str = "hotel"  # hotel, hostel, airbnb, resort
    include_flights: bool = True
    departure_city: Optional[str] = None
    compare_prices: bool = True  # Enable price comparison

class WeatherData(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    precipitation_probability: int
    weather_description: str

class PriceComparison(BaseModel):
    category: str  # "flights", "hotels", "activities"
    item_name: str
    prices: List[Dict[str, Any]]  # [{platform: "Booking.com", price: 120, url: "..."}]
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
        self.llm_key = os.environ.get('EMERGENT_LLM_KEY')
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
        """Generate a comprehensive trip plan using AI"""
        
        # Get coordinates for destination
        coords = await self.get_coordinates(request.destination)
        location_info = f"{coords['name']}, {coords['country']}" if coords else request.destination
        
        # Get weather forecast
        weather_forecast = []
        if coords:
            weather_forecast = await self.get_weather_forecast(
                coords["latitude"],
                coords["longitude"],
                request.start_date,
                request.end_date
            )
        
        # Calculate number of days
        start = datetime.strptime(request.start_date, "%Y-%m-%d")
        end = datetime.strptime(request.end_date, "%Y-%m-%d")
        num_days = (end - start).days + 1
        
        # Format weather info for AI
        weather_info = ""
        if weather_forecast:
            weather_info = "Weather forecast for the trip:\n"
            for w in weather_forecast:
                weather_info += f"- {w.date}: {w.weather_description}, {w.temperature_min}°C - {w.temperature_max}°C, {w.precipitation_probability}% rain chance\n"
        
        # Create AI prompt
        system_prompt = """You are an expert travel planner AI with access to current pricing data. You create detailed, practical trip itineraries with accurate cost estimates and price comparisons across platforms.
        
Your responses must be in valid JSON format matching this structure:
{
    "best_time_to_visit": "string describing best months/seasons",
    "weather_summary": "brief weather summary for the trip dates",
    "itinerary": [
        {
            "day": 1,
            "date": "YYYY-MM-DD",
            "activities": [
                {"time": "09:00", "activity": "Activity name", "description": "Details", "duration": "2 hours", "cost": 50, "location": "Place name"}
            ],
            "estimated_cost": 150,
            "tips": "Day-specific tips"
        }
    ],
    "cost_breakdown": {
        "flights": 500,
        "accommodation": 800,
        "food": 300,
        "activities": 200,
        "transportation": 100,
        "miscellaneous": 100,
        "total_per_person": 2000,
        "total_group": 4000,
        "currency": "USD",
        "price_comparisons": [
            {
                "category": "flights",
                "item_name": "Round trip flight",
                "prices": [
                    {"platform": "Google Flights", "price": 450, "url": "https://flights.google.com"},
                    {"platform": "Skyscanner", "price": 480, "url": "https://skyscanner.com"},
                    {"platform": "Kayak", "price": 465, "url": "https://kayak.com"}
                ],
                "best_deal": {"platform": "Google Flights", "price": 450},
                "savings_potential": 30
            },
            {
                "category": "hotels",
                "item_name": "Recommended hotel per night",
                "prices": [
                    {"platform": "Booking.com", "price": 120, "url": "https://booking.com"},
                    {"platform": "Hotels.com", "price": 135, "url": "https://hotels.com"},
                    {"platform": "Airbnb", "price": 95, "url": "https://airbnb.com"},
                    {"platform": "Expedia", "price": 125, "url": "https://expedia.com"}
                ],
                "best_deal": {"platform": "Airbnb", "price": 95},
                "savings_potential": 40
            },
            {
                "category": "activities",
                "item_name": "Top attraction tickets",
                "prices": [
                    {"platform": "GetYourGuide", "price": 45, "url": "https://getyourguide.com"},
                    {"platform": "Viator", "price": 50, "url": "https://viator.com"},
                    {"platform": "Official Site", "price": 40, "url": ""}
                ],
                "best_deal": {"platform": "Official Site", "price": 40},
                "savings_potential": 10
            }
        ]
    },
    "travel_tips": ["tip1", "tip2"],
    "packing_suggestions": ["item1", "item2"],
    "local_customs": ["custom1", "custom2"],
    "emergency_contacts": {"police": "number", "ambulance": "number", "embassy": "number"}
}

Consider:
- Local peak/off-peak tourist seasons
- Average time tourists spend at each attraction
- Realistic travel times between locations
- Local food costs, transportation costs
- Budget preference affects hotel stars and restaurant choices
- Include mix of popular and hidden gem attractions
- ALWAYS provide price comparisons across multiple booking platforms
- Include actual platform names like Booking.com, Airbnb, Expedia, Skyscanner, Google Flights, Kayak, GetYourGuide, Viator
- Prices should reflect realistic current market rates for the destination and dates"""

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

Please provide:
1. A day-by-day itinerary with specific times, activities, and costs
2. Detailed cost breakdown per person and for the group
3. Best time to visit analysis
4. Practical travel tips
5. Packing suggestions based on weather and activities
6. Local customs to be aware of
7. Emergency contact numbers

IMPORTANT: All costs and prices MUST be in {request.currency}. Use realistic local prices for {request.budget_preference} budget level."""

        # Call AI
        chat = LlmChat(
            api_key=self.llm_key,
            session_id=f"trip_plan_{user_id}_{datetime.now().timestamp()}",
            system_message=system_prompt
        ).with_model("openai", "gpt-4o")
        
        response = await chat.send_message(UserMessage(text=user_prompt))
        
        # Parse AI response
        try:
            # Clean up response - remove markdown code blocks if present
            cleaned_response = response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.startswith("```"):
                cleaned_response = cleaned_response[3:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            
            ai_plan = json.loads(cleaned_response)
            
            # Build itinerary with weather data
            itinerary = []
            for day_plan in ai_plan.get("itinerary", []):
                day_num = day_plan.get("day", 1)
                day_date = day_plan.get("date", request.start_date)
                
                # Find matching weather
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
            
            # Build cost breakdown with price comparisons
            cost_data = ai_plan.get("cost_breakdown", {})
            
            # Parse price comparisons
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
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            print(f"Response was: {response[:500]}")
            raise ValueError("Failed to parse AI response. Please try again.")

# Initialize service
trip_planner = TripPlannerService()
