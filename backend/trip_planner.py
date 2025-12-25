"""
AI Trip Planner Service - STANDARD OPENAI VERSION
Uses standard OpenAI API instead of Emergent wrapper.
"""
import os
import httpx
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import json
from openai import AsyncOpenAI  # Changed from emergentintegrations

# Configure logger
logger = logging.getLogger(__name__)

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
    departure_transport: str = "flight"  # Options: flight, train, bus, none
    return_transport: str = "flight"     # Options: flight, train, bus, none
    departure_city: Optional[str] = None
    compare_prices: bool = True

class WeatherData(BaseModel):
    date: str
    temperature_max: float
    temperature_min: float
    precipitation_probability: int
    weather_description: str

class TransportDetails(BaseModel):
    transport_type: str  # flight, train, bus
    cost: float
    duration: str  # e.g., "2h 30m"
    departure_time: Optional[str] = None
    arrival_time: Optional[str] = None
    provider: Optional[str] = None

class PriceComparison(BaseModel):
    category: str
    item_name: str
    prices: List[Dict[str, Any]]  # Each price dict should have: platform, price, url (optional), duration
    best_deal: Dict[str, Any]
    savings_potential: float

class ActivityCategory(BaseModel):
    category: str  # adventure, dining, cultural, relaxation, etc.
    cost: float
    activities: List[str]

class PackingCategory(BaseModel):
    category: str  # essentials, clothing, electronics, documents, etc.
    items: List[str]

class DayItinerary(BaseModel):
    day: int
    date: str
    weather: Optional[WeatherData] = None
    activities: List[Dict[str, Any]]
    estimated_cost: float
    tips: str

class CostBreakdown(BaseModel):
    departure_transport: float
    return_transport: float
    accommodation: float
    food: float
    activities: float
    local_transportation: float  # Intercity local transport (between cities)
    miscellaneous: float
    total_per_person: float
    total_group: float
    currency: str
    price_comparisons: List[PriceComparison] = []
    activities_breakdown: List[ActivityCategory] = []

class TripPlanResponse(BaseModel):
    destination: str
    start_date: str
    end_date: str
    num_days: int
    num_travelers: int
    best_time_to_visit: str
    weather_summary: str
    departure_transport_details: Optional[TransportDetails] = None
    return_transport_details: Optional[TransportDetails] = None
    itinerary: List[DayItinerary]
    cost_breakdown: CostBreakdown
    travel_tips: List[str]
    packing_suggestions: List[str]  # Simple list for backward compatibility
    packing_suggestions_detailed: List[PackingCategory] = []  # Categorized packing list
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
            logger.warning(f"Geocoding error for location '{location}': {e}")
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
            logger.warning(f"Weather API error: {e}")
        
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
        
        # Enhanced prompt with detailed requirements
        system_prompt = """You are an expert travel planner AI with access to current pricing data from multiple booking platforms. You create detailed, practical trip itineraries with accurate cost estimates, price comparisons across platforms with travel durations, categorized packing lists, location-specific tips, and activity breakdowns.
        
        Your response MUST be valid JSON matching the structure provided in the user prompt. Do not include markdown formatting like ```json."""

        user_prompt = f"""Plan a detailed trip with the following details:

**Destination:** {location_info}
**Dates:** {request.start_date} to {request.end_date} ({num_days} days)
**Number of travelers:** {request.num_travelers}
**Budget preference:** {request.budget_preference}
**Interests:** {', '.join(request.interests) if request.interests else 'General sightseeing'}
**Accommodation type:** {request.accommodation_type}
**Departure transport:** {request.departure_transport.capitalize() if request.departure_transport != 'none' else 'None'} from {request.departure_city if request.departure_city else 'departure city'}
**Return transport:** {request.return_transport.capitalize() if request.return_transport != 'none' else 'None'} to {request.departure_city if request.departure_city else 'departure city'}
**Currency:** {request.currency}

{weather_info}

CRITICAL REQUIREMENTS:

1. **Transport with Price Comparison & Duration:**
   - For departure and return transport, provide price comparisons from multiple platforms (e.g., MakeMyTrip, Goibibo, Booking.com, Cleartrip, IRCTC for trains)
   - EACH price entry MUST include travel duration/time (e.g., "2h 30m", "5h 15m")
   - Include at least 3-4 platform options for each transport type
   - Mark the best deal clearly

2. **Intercity Local Transportation:**
   - Include costs for local transport BETWEEN cities during the trip (not within a city)
   - This is for traveling between different destinations during the itinerary
   - Include this in the local_transportation cost breakdown

3. **Activities Breakdown by Category:**
   - Categorize all activities into: adventure, dining, cultural, relaxation, nature, shopping, nightlife, photography
   - Provide total cost estimate for each category
   - List specific activities planned under each category

4. **Categorized Packing Suggestions:**
   - Organize packing items into clear categories:
     * essentials (sunscreen, first aid, medications, toiletries)
     * clothing (weather-appropriate, activity-specific)
     * electronics (camera, chargers, adapters, power bank)
     * documents (passport, tickets, hotel bookings, ID)
     * accessories (sunglasses, hat, backpack, water bottle)
   - Provide 5-8 items per category, specific to destination and weather

5. **Location-Specific Travel Tips:**
   - Provide tips SPECIFIC to {location_info}
   - Include local customs and etiquette specific to this destination
   - Add safety tips relevant to this location
   - Include best practices for this specific region

6. **Daily Itinerary - CRITICAL:**
   - YOU MUST CREATE ITINERARY FOR ALL {num_days} DAYS
   - DO NOT skip any days - plan activities from Day 1 through Day {num_days}
   - For EACH day, include breakfast, lunch, and dinner with realistic timing and costs
   - Include appropriate rest/downtime periods
   - Ensure all activities have proper time allocations
   - **Include dress code or special requirements** for activities when applicable (e.g., "Dress code: Shoes and formal attire required" for casinos, "Modest dress required" for religious sites)
   - Add these requirements in the activity description field

7. **Booking Platform URLs - CRITICAL FOR USER EXPERIENCE:**
   - **ALL URLs MUST BE PRE-FILLED** with trip details (dates, origin, destination, travelers)
   - Users should only need to CLICK THE LINK and then confirm/book
   - DO NOT provide generic homepage URLs - they must have query parameters
   
   **Flight URL Formats** (use appropriate format for each platform):
   - Skyscanner: Use format like "https://www.skyscanner.co.in/transport/flights/{{origin_airport_code}}/{{destination_airport_code}}/{{departure_date_YYMMDD}}/{{return_date_YYMMDD}}/?adults={{num_travelers}}"
   - MakeMyTrip: Include origin, destination, dates, travelers in URL parameters
   - Goibibo: Include flight search parameters with dates and travelers
   - Cleartrip: Pre-fill from, to, dates, adults parameters
   - Google Flights: Use search URL with origin, destination, dates
   - Expedia: Include search criteria in URL
   
   **Train URL Formats** (for India):
   - Cleartrip Trains: "https://www.cleartrip.com/trains/{{origin_station}}/{{destination_station}}/{{date}}" with travelers
   - MakeMyTrip Railways: Include origin station, destination station, date, passenger count
   - IRCTC: "https://www.irctc.co.in/" (requires login, so just provide main URL with note)
   
   **IMPORTANT**: 
   - Use airport codes (DEL for Delhi, GOI for Goa, BOM for Mumbai, etc.)
   - Use station codes for trains (NDLS for New Delhi, VSG for Vasco Da Gama, etc.)
   - Format dates as required by each platform (usually YYMMDD or YYYY-MM-DD)
   - Include number of travelers/adults parameter
   - For return journeys, include both departure and return dates

Please provide a JSON response with this EXACT structure:
{{
    "best_time_to_visit": "string",
    "weather_summary": "string describing expected weather during the trip dates",
    "departure_transport": {{
        "transport_type": "{request.departure_transport}",
        "cost": 0,
        "duration": "Xh XXm",
        "departure_time": "HH:MM",
        "arrival_time": "HH:MM",
        "provider": "Best provider name"
    }},
    "return_transport": {{
        "transport_type": "{request.return_transport}",
        "cost": 0,
        "duration": "Xh XXm",
        "departure_time": "HH:MM",
        "arrival_time": "HH:MM",
        "provider": "Best provider name"
    }},
    "itinerary": [
        {{
            "day": 1,
            "date": "YYYY-MM-DD",
            "activities": [
                {{"time": "09:00", "activity": "Activity name", "description": "Details", "duration": "2 hours", "cost": 50, "location": "Specific place"}}
            ],
            "estimated_cost": 150,
            "tips": "Specific tips for this day"
        }}
    ],
    "cost_breakdown": {{
        "departure_transport": 0,
        "return_transport": 0,
        "accommodation": 0,
        "food": 0,
        "activities": 0,
        "local_transportation": 0,
        "miscellaneous": 0,
        "total_per_person": 0,
        "total_group": 0,
        "currency": "{request.currency}",
        "price_comparisons": [
            {{
                "category": "departure_transport",
                "item_name": "{request.departure_transport.capitalize()} from {{departure_city}} to {{destination}}",
                "prices": [
                    {{"platform": "Skyscanner", "price": 5200, "duration": "2h 30m", "url": "https://www.skyscanner.co.in/transport/flights/del/goi/250101/250108/?adults=2"}},
                    {{"platform": "MakeMyTrip", "price": 5000, "duration": "2h 30m", "url": "https://www.makemytrip.com/flight/search?tripType=O&itinerary=DEL-GOI-01/01/2025&paxType=A-2"}},
                    {{"platform": "Goibibo", "price": 4800, "duration": "2h 30m", "url": "https://www.goibibo.com/flights/air-DEL-GOI-20250101-2-0-0-E/"}},
                    {{"platform": "Cleartrip", "price": 4900, "duration": "2h 30m", "url": "https://www.cleartrip.com/flight-booking/search?from=DEL&to=GOI&depart_date=01-01-2025&adults=2"}},
                    {{"platform": "Google Flights", "price": 4850, "duration": "2h 30m", "url": "https://www.google.com/travel/flights?q=Flights%20from%20DEL%20to%20GOI%20on%202025-01-01%20for%202%20adults"}},
                    {{"platform": "Expedia", "price": 5100, "duration": "2h 30m", "url": "https://www.expedia.co.in/Flights-Search?leg1=from:DEL,to:GOI,departure:01/01/2025&passengers=adults:2"}}
                ],
                "best_deal": {{"platform": "Goibibo", "price": 4800}},
                "savings_potential": 400
            }},
            {{
                "category": "return_transport",
                "item_name": "{request.return_transport.capitalize()} from {{destination}} to {{departure_city}}",
                "prices": [
                    {{"platform": "Skyscanner", "price": 5400, "duration": "2h 30m", "url": "https://www.skyscanner.co.in/transport/flights/goi/del/250108/?adults=2"}},
                    {{"platform": "MakeMyTrip", "price": 5200, "duration": "2h 30m", "url": "https://www.makemytrip.com/flight/search?tripType=O&itinerary=GOI-DEL-08/01/2025&paxType=A-2"}},
                    {{"platform": "Goibibo", "price": 4900, "duration": "2h 30m", "url": "https://www.goibibo.com/flights/air-GOI-DEL-20250108-2-0-0-E/"}},
                    {{"platform": "Cleartrip", "price": 5000, "duration": "2h 30m", "url": "https://www.cleartrip.com/flight-booking/search?from=GOI&to=DEL&depart_date=08-01-2025&adults=2"}}
                ],
                "best_deal": {{"platform": "Goibibo", "price": 4900}},
                "savings_potential": 500
            }}
        ],
        "activities_breakdown": [
            {{"category": "adventure", "cost": 3000, "activities": ["Scuba diving", "Parasailing"]}},
            {{"category": "dining", "cost": 2500, "activities": ["Beach restaurants", "Fine dining"]}},
            {{"category": "cultural", "cost": 500, "activities": ["Museum visits", "Historical sites"]}}
        ]
    }},
    "travel_tips": [
        "Tip 1 specific to {location_info}",
        "Tip 2 about local transportation in {location_info}",
        "Safety tip relevant to {location_info}",
        "Best practice for {location_info}"
    ],
    "packing_suggestions": [
        "Item 1", "Item 2", "Item 3"
    ],
    "packing_suggestions_detailed": [
        {{"category": "essentials", "items": ["Sunscreen SPF 50+", "First aid kit", "Prescription medications", "Hand sanitizer", "Insect repellent"]}},
        {{"category": "clothing", "items": ["Light cotton shirts", "Shorts/skirts", "Swimwear", "Light jacket", "Comfortable walking shoes"]}},
        {{"category": "electronics", "items": ["Camera", "Phone charger", "Power bank", "Universal adapter", "Headphones"]}},
        {{"category": "documents", "items": ["Passport/ID", "Flight tickets", "Hotel bookings", "Travel insurance", "Emergency contacts"]}},
        {{"category": "accessories", "items": ["Sunglasses", "Hat/cap", "Daypack", "Reusable water bottle", "Beach towel"]}}
    ],
    "local_customs": [
        "Custom 1 specific to {location_info}",
        "Etiquette rule for {location_info}",
        "Cultural practice in {location_info}"
    ],
    "emergency_contacts": {{
        "police": "100",
        "ambulance": "102",
        "fire": "101",
        "tourist_helpline": "1363"
    }}
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
            
            # Parse transport details
            departure_transport_data = ai_plan.get("departure_transport", {})
            return_transport_data = ai_plan.get("return_transport", {})
            
            departure_transport_details = None
            if departure_transport_data and request.departure_transport != "none":
                departure_transport_details = TransportDetails(
                    transport_type=departure_transport_data.get("transport_type", request.departure_transport),
                    cost=departure_transport_data.get("cost", 0),
                    duration=departure_transport_data.get("duration", ""),
                    departure_time=departure_transport_data.get("departure_time"),
                    arrival_time=departure_transport_data.get("arrival_time"),
                    provider=departure_transport_data.get("provider")
                )
            
            return_transport_details = None
            if return_transport_data and request.return_transport != "none":
                return_transport_details = TransportDetails(
                    transport_type=return_transport_data.get("transport_type", request.return_transport),
                    cost=return_transport_data.get("cost", 0),
                    duration=return_transport_data.get("duration", ""),
                    departure_time=return_transport_data.get("departure_time"),
                    arrival_time=return_transport_data.get("arrival_time"),
                    provider=return_transport_data.get("provider")
                )
            
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
            
            # Parse activities breakdown
            activities_breakdown = []
            for ab in cost_data.get("activities_breakdown", []):
                activities_breakdown.append(ActivityCategory(
                    category=ab.get("category", ""),
                    cost=ab.get("cost", 0),
                    activities=ab.get("activities", [])
                ))
            
            cost_breakdown = CostBreakdown(
                departure_transport=cost_data.get("departure_transport", 0),
                return_transport=cost_data.get("return_transport", 0),
                accommodation=cost_data.get("accommodation", 0),
                food=cost_data.get("food", 0),
                activities=cost_data.get("activities", 0),
                local_transportation=cost_data.get("local_transportation", 0),
                miscellaneous=cost_data.get("miscellaneous", 0),
                total_per_person=cost_data.get("total_per_person", 0),
                total_group=cost_data.get("total_group", 0),
                currency=cost_data.get("currency", "USD"),
                price_comparisons=price_comparisons,
                activities_breakdown=activities_breakdown
            )
            
            # Parse packing suggestions detailed
            packing_detailed = []
            for pc in ai_plan.get("packing_suggestions_detailed", []):
                packing_detailed.append(PackingCategory(
                    category=pc.get("category", ""),
                    items=pc.get("items", [])
                ))
            
            return TripPlanResponse(
                destination=location_info,
                start_date=request.start_date,
                end_date=request.end_date,
                num_days=num_days,
                num_travelers=request.num_travelers,
                best_time_to_visit=ai_plan.get("best_time_to_visit", ""),
                weather_summary=ai_plan.get("weather_summary", ""),
                departure_transport_details=departure_transport_details,
                return_transport_details=return_transport_details,
                itinerary=itinerary,
                cost_breakdown=cost_breakdown,
                travel_tips=ai_plan.get("travel_tips", []),
                packing_suggestions=ai_plan.get("packing_suggestions", []),
                packing_suggestions_detailed=packing_detailed,
                local_customs=ai_plan.get("local_customs", []),
                emergency_contacts=ai_plan.get("emergency_contacts", {})
            )
            
        except Exception as e:
            logger.error(f"Trip planning error: {e}", exc_info=True)
            raise ValueError("Failed to generate trip plan. Please try again.")

trip_planner = TripPlannerService()