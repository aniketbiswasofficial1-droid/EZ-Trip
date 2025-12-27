"""
AI Trip Planner Service
Uses Google Gemini 1.5 Flash for AI-powered trip planning.
"""
import os
import httpx
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel
import json
import google.generativeai as genai  # Using older but stable package

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

class ConnectivityInfo(BaseModel):
    transport_mode: str  # "train" or "flight"
    from_location: str
    to_location: str
    has_direct_connectivity: bool
    journey_time_estimate: str  # e.g., "6h 30m"
    connectivity_notes: str  # e.g., "Direct service available" or "Via nearest airport"
    nearest_station_airport: Optional[str] = None  # Name of nearest station/airport if not direct
    distance_to_nearest_km: Optional[float] = None  # Distance to nearest station/airport
    suggested_options: List[str] = []  # e.g., ["Rajdhani Express", "Shatabdi Express"] or ["Multiple daily flights"]


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
    connectivity_suggestions: List[ConnectivityInfo] = []
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
        # Configure Gemini API (using older stable package)
        self.api_key = os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable is not set")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash-lite')  # Latest lite version
        self.weather_base_url = "https://api.open-meteo.com/v1"
        self.geocoding_url = "https://geocoding-api.open-meteo.com/v1"
        
    def get_primary_airport(self, location: str) -> Optional[Dict[str, str]]:
        """Map locations to their primary airport for flight searches"""
        # Common Indian airports and international hubs
        airport_mapping = {
            "kolkata": {"code": "CCU", "name": "Netaji Subhas Chandra Bose International Airport", "city": "Kolkata"},
            "karimpur": {"code": "CCU", "name": "Netaji Subhas Chandra Bose International Airport", "city": "Kolkata"},  # Near Kolkata
            "goa": {"code": "GOI", "name": "Goa International Airport (Dabolim)", "city": "Goa"},
            "south goa": {"code": "GOI", "name": "Goa International Airport (Dabolim)", "city": "Goa"},
            "north goa": {"code": "GOI", "name": "Goa International Airport (Dabolim)", "city": "Goa"},
            "delhi": {"code": "DEL", "name": "Indira Gandhi International Airport", "city": "Delhi"},
            "new delhi": {"code": "DEL", "name": "Indira Gandhi International Airport", "city": "Delhi"},
            "mumbai": {"code": "BOM", "name": "Chhatrapati Shivaji Maharaj International Airport", "city": "Mumbai"},
            "bangalore": {"code": "BLR", "name": "Kempegowda International Airport", "city": "Bangalore"},
            "bengaluru": {"code": "BLR", "name": "Kempegowda International Airport", "city": "Bangalore"},
            "chennai": {"code": "MAA", "name": "Chennai International Airport", "city": "Chennai"},
            "hyderabad": {"code": "HYD", "name": "Rajiv Gandhi International Airport", "city": "Hyderabad"},
            "pune": {"code": "PNQ", "name": "Pune Airport", "city": "Pune"},
            "ahmedabad": {"code": "AMD", "name": "Sardar Vallabhbhai Patel International Airport", "city": "Ahmedabad"},
            "jaipur": {"code": "JAI", "name": "Jaipur International Airport", "city": "Jaipur"},
            "kochi": {"code": "COK", "name": "Cochin International Airport", "city": "Kochi"},
            "cochin": {"code": "COK", "name": "Cochin International Airport", "city": "Kochi"},
        }
        
        location_lower = location.lower()
        for city, airport in airport_mapping.items():
            if city in location_lower:
                return airport
        return None
    
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
        
        # Get airport information for better flight routing
        departure_airport = None
        destination_airport = None
        if request.departure_city:
            departure_airport = self.get_primary_airport(request.departure_city)
        destination_airport = self.get_primary_airport(request.destination)
        
        # Build airport context for AI
        airport_context = ""
        airport_proximity_info = ""
        
        if departure_airport and destination_airport:
            airport_context = f"""\n✈️ FLIGHT ROUTING:
- Departure Airport: {departure_airport['city']} ({departure_airport['code']}) - {departure_airport['name']}
- Destination Airport: {destination_airport['city']} ({destination_airport['code']}) - {destination_airport['name']}
"""
            
            # Check if departure location differs from airport city
            departure_location_lower = request.departure_city.lower() if request.departure_city else ""
            destination_location_lower = request.destination.lower()
            
            uses_nearby_departure = departure_airport and departure_airport['city'].lower() not in departure_location_lower
            uses_nearby_destination = destination_airport and destination_airport['city'].lower() not in destination_location_lower
            
            if uses_nearby_departure or uses_nearby_destination:
                airport_proximity_info = "\n🏢 AIRPORT PROXIMITY NOTIFICATION (IMPORTANT):\n"
                if uses_nearby_departure:
                    airport_proximity_info += f"- User's departure location '{request.departure_city}' does NOT have a direct airport.\n"
                    airport_proximity_info += f"  NEAREST AIRPORT: {departure_airport['name']} ({departure_airport['code']}) in {departure_airport['city']}\n"
                    airport_proximity_info += f"  YOU MUST inform the user: 'Nearest airport to {request.departure_city} is {departure_airport['name']} ({departure_airport['code']}) in {departure_airport['city']}'\n"
                if uses_nearby_destination:
                    airport_proximity_info += f"- User's destination '{request.destination}' does NOT have a direct airport.\n"
                    airport_proximity_info += f"  NEAREST AIRPORT: {destination_airport['name']} ({destination_airport['code']}) in {destination_airport['city']}\n"
                    airport_proximity_info += f"  YOU MUST inform the user: 'Nearest airport to {request.destination} is {destination_airport['name']} ({destination_airport['code']}) in {destination_airport['city']}'\n"

        
        # Known direct flight routes (major Indian routes)
        known_direct_routes = {
            ("CCU", "GOI"): {"duration": "2h 30m", "note": "Multiple daily direct flights available (IndiGo, Air India, SpiceJet)"},
            ("GOI", "CCU"): {"duration": "2h 30m", "note": "Multiple daily direct flights available (IndiGo, Air India, SpiceJet)"},
            ("DEL", "GOI"): {"duration": "2h 45m", "note": "Frequent direct flights (IndiGo, Air India, SpiceJet, Vistara)"},
            ("GOI", "DEL"): {"duration": "2h 45m", "note": "Frequent direct flights (IndiGo, Air India, SpiceJet, Vistara)"},
            ("BOM", "GOI"): {"duration": "1h 15m", "note": "Multiple daily direct flights (IndiGo, Air India, SpiceJet)"},
            ("GOI", "BOM"): {"duration": "1h 15m", "note": "Multiple daily direct flights (IndiGo, Air India, SpiceJet)"},
            ("BLR", "GOI"): {"duration": "1h 30m", "note": "Direct flights available (IndiGo, Air India)"},
            ("GOI", "BLR"): {"duration": "1h 30m", "note": "Direct flights available (IndiGo, Air India)"},
        }
        
        # Check if there's a known direct route
        direct_route_info = ""
        if departure_airport and destination_airport:
            route_key = (departure_airport['code'], destination_airport['code'])
            if route_key in known_direct_routes:
                route = known_direct_routes[route_key]
                direct_route_info = f"""\n🎯 VERIFIED DIRECT ROUTE:
- Route: {departure_airport['code']} → {destination_airport['code']}
- Flight Duration: {route['duration']}
- Availability: {route['note']}
- IMPORTANT: This is a DIRECT FLIGHT route. Do NOT suggest layovers unless specifically needed.
"""
        
        # Optimized system prompt with STRONG anti-hallucination
        system_prompt = f"""Expert travel planner. Generate valid JSON (no markdown).

CRITICAL LOCATION RULES:
- The destination is: {location_info}
- Use this EXACT name in ALL outputs
- If destination contains "Goa" → It is GOA, INDIA (NOT Genoa)
- VERIFY every location reference matches: {location_info}

FLIGHT SEARCH RULES:
- For flight searches, use the NEAREST MAJOR AIRPORT to the departure/destination city
- Example: Karimpur-I is near Kolkata, so use Kolkata (CCU) airport
- STRONGLY PREFER direct flights over connecting flights
- Only suggest layovers if NO direct flights exist OR if significantly cheaper (>40% savings)
- Major Indian airports have excellent domestic connectivity{airport_context}{direct_route_info}

TRAIN CONNECTIVITY:
- ALWAYS provide train connectivity information in addition to flight options
- Include train routes even when flights are available - travelers may prefer trains for scenic routes or budget
- For each route, suggest both flight AND train options in connectivity_suggestions
- Common trains: Rajdhani (fastest), Shatabdi (day travel), Express trains (budget-friendly)

NEAREST AIRPORT COMMUNICATION:
- When user's location differs from airport city, inform them CLEARLY in connectivity_notes
- Example: "Nearest airport to Karimpur-I is Netaji Subhas Chandra Bose International Airport (CCU) in Kolkata"
- Include this information for BOTH departure and destination if applicable{airport_proximity_info}"""

        # Optimized user prompt - concise and focused
        flight_instruction = ""
        if departure_airport and destination_airport:
            if (departure_airport['code'], destination_airport['code']) in known_direct_routes:
                flight_instruction = f"""\n⚠️ CRITICAL FLIGHT INSTRUCTION:
There ARE direct flights from {departure_airport['city']} ({departure_airport['code']}) to {destination_airport['city']} ({destination_airport['code']}).
Flight duration: ~{known_direct_routes[(departure_airport['code'], destination_airport['code'])]['duration']}
DO NOT suggest layovers or connecting flights for this route - PREFER THE DIRECT FLIGHT.
Set has_direct_connectivity=true for this route.

🚂 TRAIN OPTION:
ALSO provide train connectivity information as an alternative option.
Include both flight (direct, preferred) AND train options in connectivity_suggestions array.
"""
        
        user_prompt = f"""⚠️ DESTINATION VERIFICATION:
The user's destination is: {location_info}
CONFIRM: All connectivity, flights, and journey information MUST be for {location_info}
If this is "Goa, India" → Use GOI airport code (Goa International Airport - Dabolim)
If this is "Goa, India" → NEVER mention Genoa, Italy or GOA (Genoa) airport{flight_instruction}

TRIP DETAILS:
From: {request.departure_city or 'departure city'}
To: {location_info}

Dates: {request.start_date} to {request.end_date} ({num_days} days)
Travelers: {request.num_travelers} | Budget: {request.budget_preference}
Interests: {', '.join(request.interests) if request.interests else 'General'}
Accommodation: {request.accommodation_type}
Transport: {request.departure_transport}/{request.return_transport}
Currency: {request.currency}

{weather_info}

REQUIREMENTS:
1. Transport: 
   - PREFER direct flights when available (faster, more convenient)
   - Find nearest airport/station to each city → calc journey time → suggest options
   - Provide BOTH flight AND train connectivity suggestions for each route
   - Only suggest connecting flights if no direct option exists
2. Itinerary: Day-by-day detailed plan with activities, times, costs
3. Packing: Categorize by essentials/clothing/electronics/documents
4. Tips: Local customs, safety, budgeting advice
5. Itinerary: MUST have ALL {num_days} days with breakfast/lunch/dinner, costs, timing

Please provide a JSON response with this EXACT structure:
{{
    "best_time_to_visit": "string",
    "weather_summary": "string describing expected weather during the trip dates",
    "departure_transport": {{
        "transport_type": "{request.departure_transport}",
        "cost": 0,
        "duration": "Xh XXm",
        "departure_time": null,
        "arrival_time": null,
        "provider": null
    }},
    "return_transport": {{
        "transport_type": "{request.return_transport}",
        "cost": 0,
        "duration": "Xh XXm",
        "departure_time": null,
        "arrival_time": null,
        "provider": null
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
        "connectivity_suggestions": [
            {{
                "transport_mode": "{request.departure_transport}",
                "from_location": "{request.departure_city}",
                "to_location": "{location_info}",
                "has_direct_connectivity": true,
                "journey_time_estimate": "6h 30m",
                "connectivity_notes": "Direct train service available from New Delhi Railway Station to Goa",
                "nearest_station_airport": None,
                "distance_to_nearest_km": None,
                "suggested_options": ["Rajdhani Express", "Express trains", "Typical journey: 24-30 hours"]
            }},
            {{
                "transport_mode": "{request.return_transport}",
                "from_location": "{location_info}",
                "to_location": "{request.departure_city}",
                "has_direct_connectivity": false,
                "journey_time_estimate": "3h 45m total (30min local + 2h 30m flight + 45min local)",
                "connectivity_notes": "Via nearest airport in Dabolim, Goa",
                "nearest_station_airport": "Dabolim Airport (GOI)",
                "distance_to_nearest_km": 25.0,
                "suggested_options": ["Multiple daily flights", "2-3 hour flight duration", "IndiGo, Air India, SpiceJet available"]
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


        # Gemini API Call (using older stable package)
        try:
            # Combine prompts
            full_prompt = f"{system_prompt}\n\n{user_prompt}"
            
            # Call Gemini with JSON mode
            response = await self.model.generate_content_async(
                full_prompt,
                generation_config=genai.GenerationConfig(
                    response_mime_type="application/json"
                )
            )
            
            content = response.text
            ai_plan = json.loads(content)
            
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
            connectivity_suggestions = []
            for cs in cost_data.get("connectivity_suggestions", []):
                connectivity_suggestions.append(ConnectivityInfo(
                    transport_mode=cs.get("transport_mode", ""),
                    from_location=cs.get("from_location", ""),
                    to_location=cs.get("to_location", ""),
                    has_direct_connectivity=cs.get("has_direct_connectivity", False),
                    journey_time_estimate=cs.get("journey_time_estimate", ""),
                    connectivity_notes=cs.get("connectivity_notes", ""),
                    nearest_station_airport=cs.get("nearest_station_airport"),
                    distance_to_nearest_km=cs.get("distance_to_nearest_km"),
                    suggested_options=cs.get("suggested_options", [])
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
                connectivity_suggestions=connectivity_suggestions,
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
            logger.error(f"Trip planning error: {str(e)}", exc_info=True)
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error details: {repr(e)}")
            raise ValueError(f"Failed to generate trip plan: {str(e)}")


# Lazy initialization - will be created when first accessed (after .env is loaded)
trip_planner = None

def get_trip_planner():
    global trip_planner
    if trip_planner is None:
        trip_planner = TripPlannerService()
    return trip_planner