"""
Admin Service - Handles admin panel functionality
"""
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field
import os

# ========================
# ADMIN MODELS
# ========================

class FeatureToggle(BaseModel):
    feature_id: str
    name: str
    description: str
    enabled: bool = True
    category: str  # "navigation", "buttons", "features", "ai"

class SiteContent(BaseModel):
    content_id: str
    section: str  # "hero", "features", "footer", etc.
    key: str
    value: str
    content_type: str = "text"  # "text", "image", "html"

class AppSettings(BaseModel):
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o"
    llm_key: Optional[str] = None
    default_currency: str = "USD"
    maintenance_mode: bool = False
    registration_enabled: bool = True
    ai_planner_enabled: bool = True
    max_trips_per_user: int = 50
    max_members_per_trip: int = 20

class AdminStats(BaseModel):
    total_users: int = 0
    total_trips: int = 0
    total_expenses: int = 0
    total_refunds: int = 0
    total_saved_plans: int = 0
    active_users_today: int = 0
    new_users_this_week: int = 0
    popular_destinations: List[Dict[str, Any]] = []
    expense_by_currency: List[Dict[str, Any]] = []

# Default feature toggles
DEFAULT_FEATURE_TOGGLES = [
    # Navigation
    {"feature_id": "nav_dashboard", "name": "Dashboard Access", "description": "Allow users to access dashboard", "enabled": True, "category": "navigation"},
    {"feature_id": "nav_planner", "name": "AI Trip Planner", "description": "Show AI Trip Planner in navigation", "enabled": True, "category": "navigation"},
    
    # Buttons
    {"feature_id": "btn_create_trip", "name": "Create Trip Button", "description": "Allow users to create new trips", "enabled": True, "category": "buttons"},
    {"feature_id": "btn_add_expense", "name": "Add Expense Button", "description": "Allow users to add expenses", "enabled": True, "category": "buttons"},
    {"feature_id": "btn_add_refund", "name": "Add Refund Button", "description": "Allow users to add refunds", "enabled": True, "category": "buttons"},
    {"feature_id": "btn_add_member", "name": "Add Member Button", "description": "Allow users to add trip members", "enabled": True, "category": "buttons"},
    {"feature_id": "btn_delete_trip", "name": "Delete Trip Button", "description": "Allow users to delete trips", "enabled": True, "category": "buttons"},
    {"feature_id": "btn_generate_plan", "name": "Generate Plan Button", "description": "Allow AI plan generation", "enabled": True, "category": "buttons"},
    {"feature_id": "btn_save_plan", "name": "Save Plan Button", "description": "Allow saving AI plans", "enabled": True, "category": "buttons"},
    {"feature_id": "btn_google_login", "name": "Google Login Button", "description": "Show Google login option", "enabled": True, "category": "buttons"},
    
    # Features
    {"feature_id": "feature_settlements", "name": "Settlement Suggestions", "description": "Show settlement suggestions in trips", "enabled": True, "category": "features"},
    {"feature_id": "feature_refunds", "name": "Refunds System", "description": "Enable refund functionality", "enabled": True, "category": "features"},
    {"feature_id": "feature_multi_currency", "name": "Multi-Currency", "description": "Allow multiple currencies per trip", "enabled": True, "category": "features"},
    {"feature_id": "feature_weather", "name": "Weather Forecast", "description": "Show weather in trip planner", "enabled": True, "category": "features"},
    {"feature_id": "feature_ads", "name": "Advertisement Slots", "description": "Show native ad slots", "enabled": True, "category": "features"},
    
    # AI Features
    {"feature_id": "ai_itinerary", "name": "AI Itinerary", "description": "Generate day-by-day itinerary", "enabled": True, "category": "ai"},
    {"feature_id": "ai_cost_estimate", "name": "AI Cost Estimation", "description": "AI-powered cost breakdown", "enabled": True, "category": "ai"},
    {"feature_id": "ai_packing_list", "name": "AI Packing List", "description": "Generate packing suggestions", "enabled": True, "category": "ai"},
    {"feature_id": "ai_local_tips", "name": "AI Local Tips", "description": "Generate local customs and tips", "enabled": True, "category": "ai"},
]

# Default site content
DEFAULT_SITE_CONTENT = [
    # Hero Section
    {"content_id": "hero_badge", "section": "hero", "key": "badge_text", "value": "Free forever for personal use", "content_type": "text"},
    {"content_id": "hero_title_1", "section": "hero", "key": "title_line_1", "value": "Split expenses,", "content_type": "text"},
    {"content_id": "hero_title_2", "section": "hero", "key": "title_line_2", "value": "not friendships", "content_type": "text"},
    {"content_id": "hero_subtitle", "section": "hero", "key": "subtitle", "value": "The modern way to track and split trip expenses. Handle complex splits, manage refunds, and settle up with friends in any currency.", "content_type": "text"},
    {"content_id": "hero_cta", "section": "hero", "key": "cta_text", "value": "Get Started Free", "content_type": "text"},
    
    # Stats
    {"content_id": "stat_currencies", "section": "stats", "key": "currencies_count", "value": "13+", "content_type": "text"},
    {"content_id": "stat_currencies_label", "section": "stats", "key": "currencies_label", "value": "Currencies", "content_type": "text"},
    {"content_id": "stat_price", "section": "stats", "key": "price", "value": "100%", "content_type": "text"},
    {"content_id": "stat_price_label", "section": "stats", "key": "price_label", "value": "Free", "content_type": "text"},
    
    # Features Section
    {"content_id": "features_title", "section": "features", "key": "title", "value": "Everything you need to split expenses", "content_type": "text"},
    {"content_id": "features_subtitle", "section": "features", "key": "subtitle", "value": "Powerful features designed to make expense splitting simple, fair, and transparent.", "content_type": "text"},
    
    # CTA Section
    {"content_id": "cta_title", "section": "cta", "key": "title", "value": "Ready to simplify your group expenses?", "content_type": "text"},
    {"content_id": "cta_subtitle", "section": "cta", "key": "subtitle", "value": "Join thousands of travelers who trust EZ Trip for fair and easy expense splitting.", "content_type": "text"},
    {"content_id": "cta_button", "section": "cta", "key": "button_text", "value": "Start Splitting Now", "content_type": "text"},
    
    # Footer
    {"content_id": "footer_tagline", "section": "footer", "key": "tagline", "value": "Split expenses, not friendships.", "content_type": "text"},
    
    # Ad Content
    {"content_id": "ad_title", "section": "ads", "key": "native_ad_title", "value": "Currency Exchange", "content_type": "text"},
    {"content_id": "ad_description", "section": "ads", "key": "native_ad_description", "value": "Get the best rates for your international trips", "content_type": "text"},
]

# Available LLM models
LLM_MODELS = {
    "openai": [
        {"id": "gpt-4o", "name": "GPT-4o (Recommended)", "description": "Best for complex planning"},
        {"id": "gpt-4o-mini", "name": "GPT-4o Mini", "description": "Faster, more economical"},
        {"id": "gpt-4.1", "name": "GPT-4.1", "description": "Latest GPT-4 version"},
        {"id": "gpt-5.1", "name": "GPT-5.1", "description": "Most advanced model"},
    ],
    "anthropic": [
        {"id": "claude-4-sonnet-20250514", "name": "Claude 4 Sonnet", "description": "Balanced performance"},
        {"id": "claude-4-opus-20250514", "name": "Claude 4 Opus", "description": "Most capable"},
    ],
    "gemini": [
        {"id": "gemini-2.5-flash", "name": "Gemini 2.5 Flash", "description": "Fast responses"},
        {"id": "gemini-2.5-pro", "name": "Gemini 2.5 Pro", "description": "Advanced reasoning"},
    ]
}
