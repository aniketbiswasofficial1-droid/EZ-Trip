from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, UploadFile, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import io
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import bcrypt
import uuid
import re  # Required for password validation
from datetime import datetime, timezone, timedelta
import httpx
from trip_planner import trip_planner, TripPlanRequest, TripPlanResponse
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from email_service import EmailService
from PIL import Image
import shutil

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Environment configuration
ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
IS_PRODUCTION = ENVIRONMENT == 'production'
DEBUG = os.getenv('DEBUG', 'true').lower() == 'true' and not IS_PRODUCTION

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017/eztrip')
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'eztrip_db')]

# Create uploads directory
UPLOAD_DIR = ROOT_DIR / "uploads" / "profile-pictures"
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

# Allowed image types and max size
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

# Create the main app
app = FastAPI()

# Configure logging
log_level = os.getenv('LOG_LEVEL', 'INFO' if IS_PRODUCTION else 'DEBUG')
logging.basicConfig(
    level=getattr(logging, log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Log startup information
logger.info(f"Starting EZ-Trip Backend in {ENVIRONMENT} mode")
logger.info(f"Debug mode: {DEBUG}")

# GLOBAL ERROR HANDLER
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Global error: {exc}", exc_info=True if DEBUG else False)
    # Don't expose internal error details in production
    error_detail = str(exc) if DEBUG else "Internal server error"
    return JSONResponse(
        status_code=500,
        content={"detail": error_detail}
    )

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth")
trips_router = APIRouter(prefix="/trips")
expenses_router = APIRouter(prefix="/expenses")
refunds_router = APIRouter(prefix="/refunds")
settlements_router = APIRouter(prefix="/settlements")
planner_router = APIRouter(prefix="/planner")
admin_router = APIRouter(prefix="/admin")

# ========================
# CORS CONFIGURATION
# ========================
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5173",
    "http://127.0.0.1:5173"
]

if os.environ.get('CORS_ORIGINS'):
    origins.extend(os.environ.get('CORS_ORIGINS').split(','))

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Security Headers Middleware
@app.middleware("http")
async def add_security_headers(request: Request, call_next):
    response = await call_next(request)
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    if IS_PRODUCTION:
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response

# ========================
# PYDANTIC MODELS
# ========================

class UserBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    username: Optional[str] = None  # NEW: Unique username
    picture: Optional[str] = None
    custom_profile_picture: Optional[str] = None
    date_of_birth: Optional[str] = None
    default_currency: str = "INR"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserUpdate(BaseModel):
    name: Optional[str] = None
    date_of_birth: Optional[str] = None
    custom_profile_picture: Optional[str] = None
    default_currency: Optional[str] = None

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class UsernameUpdate(BaseModel):
    username: str

class TripCreate(BaseModel):
    name: str
    description: Optional[str] = None
    currency: str = "INR"
    cover_image: Optional[str] = None

class TripMember(BaseModel):
    user_id: str
    name: str
    email: str
    username: Optional[str] = None  # NEW: Username for registered users
    picture: Optional[str] = None

class TripResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    trip_id: str
    name: str
    description: Optional[str] = None
    currency: str
    cover_image: Optional[str] = None
    created_by: str
    members: List[TripMember]
    created_at: datetime
    total_expenses: float = 0
    your_balance: float = 0

class ExpensePayer(BaseModel):
    user_id: str
    amount: float

class ExpenseSplit(BaseModel):
    user_id: str
    amount: float

class ExpenseCreate(BaseModel):
    trip_id: str
    description: str
    total_amount: float
    currency: str
    payers: List[ExpensePayer]
    splits: List[ExpenseSplit]
    category: Optional[str] = "general"
    date: Optional[datetime] = None

class RefundCreate(BaseModel):
    expense_id: str
    amount: float
    reason: str
    refunded_to: List[str]  # List of user_ids receiving refund

class RefundResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    refund_id: str
    expense_id: str
    expense_description: str
    amount: float
    reason: str
    refunded_to: List[str]
    created_by: str
    created_at: datetime

class ExpenseResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    expense_id: str
    trip_id: str
    description: str
    total_amount: float
    currency: str
    payers: List[ExpensePayer]
    splits: List[ExpenseSplit]
    category: str
    date: datetime
    created_by: str
    created_at: datetime
    refunds: List[RefundResponse] = []
    net_amount: float = 0

class BalanceEntry(BaseModel):
    user_id: str
    name: str
    balance: float  # Positive = owed money, Negative = owes money

class SettlementSuggestion(BaseModel):
    from_user_id: str
    from_user_name: str
    to_user_id: str
    to_user_name: str
    amount: float
    currency: str

class TripAddMember(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None  # NEW: Can add by username
    name: str

class SettlementCreate(BaseModel):
    trip_id: str
    from_user_id: str
    to_user_id: str
    amount: float
    note: Optional[str] = None

class SettlementEntry(BaseModel):
    model_config = ConfigDict(extra="ignore")
    settlement_id: str
    trip_id: str
    from_user_id: str
    from_user_name: str
    to_user_id: str
    to_user_name: str
    amount: float
    note: Optional[str] = None
    created_by: str
    created_at: datetime

# Trip Plan Models
class TripPlan(BaseModel):
    destination: str
    start_date: str
    end_date: str
    num_days: Optional[int] = None
    num_travelers: Optional[int] = None
    itinerary: List[Dict]
    best_time_to_visit: Optional[str] = None
    weather_summary: Optional[str] = None
    cost_breakdown: Optional[Dict] = None
    departure_transport_details: Optional[Dict] = None
    return_transport_details: Optional[Dict] = None
    travel_tips: Optional[List[str]] = []
    packing_suggestions: Optional[List[str]] = []
    packing_suggestions_detailed: Optional[List[Dict]] = []
    local_customs: Optional[List[str]] = []
    emergency_contacts: Optional[Dict] = None

class SavedTripPlan(BaseModel):
    plan_id: str
    destination: str
    start_date: str
    end_date: str
    itinerary: List[Dict]
    weather_forecast: Optional[Dict] = None
    cost_estimates: Optional[Dict] = None
    created_at: str
    linked_to_trip: Optional[str] = None

class LinkPlanRequest(BaseModel):
    plan_id: str

# ========================
# AUTH HELPERS
# ========================

async def get_current_user(request: Request) -> dict:
    """Get current user from session token (cookie or header)"""
    session_token = request.cookies.get("session_token")
    
    if not session_token:
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            session_token = auth_header.split(" ")[1]
    
    if not session_token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    
    session = await db.user_sessions.find_one(
        {"session_token": session_token},
        {"_id": 0}
    )
    
    if not session:
        raise HTTPException(status_code=401, detail="Invalid session")
    
    expires_at = session.get("expires_at")
    if isinstance(expires_at, str):
        expires_at = datetime.fromisoformat(expires_at)
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=401, detail="Session expired")
    
    user = await db.users.find_one(
        {"user_id": session["user_id"]},
        {"_id": 0}
    )
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return user

# ========================
# AUTH ROUTES
# ========================

# NEW: Helper functions using bcrypt directly
def verify_password(plain_password, hashed_password):
    if not hashed_password:
        return False
    if isinstance(plain_password, str):
        plain_password = plain_password.encode('utf-8')
    if isinstance(hashed_password, str):
        hashed_password = hashed_password.encode('utf-8')
    try:
        return bcrypt.checkpw(plain_password, hashed_password)
    except ValueError:
        return False

def get_password_hash(password):
    if isinstance(password, str):
        password = password.encode('utf-8')
    return bcrypt.hashpw(password, bcrypt.gensalt()).decode('utf-8')

# NEW: Password Validation
def validate_strong_password(password: str):
    if len(password) < 8:
        raise HTTPException(status_code=400, detail="Password must be at least 8 characters long")
    if not re.search(r"[a-zA-Z]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one letter")
    if not re.search(r"\d", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one number")
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        raise HTTPException(status_code=400, detail="Password must contain at least one special character")

# Username Validation
def validate_username(username: str):
    """Validate username format"""
    if not re.match(r'^[a-zA-Z0-9_-]{3,20}$', username):
        raise HTTPException(
            status_code=400, 
            detail="Username must be 3-20 characters (letters, numbers, _, -)"
        )
    return username.lower()

async def is_username_taken(username: str, exclude_user_id: Optional[str] = None) -> bool:
    """Check if username is already taken"""
    query = {"username": username.lower()}
    if exclude_user_id:
        query["user_id"] = {"$ne": exclude_user_id}
    user = await db.users.find_one(query)
    return user is not None

async def generate_unique_username(email: str, name: str) -> str:
    """Generate a unique username from email or name"""
    # Try username from email first (john.doe@gmail.com -> john_doe)
    base_username = email.split('@')[0].lower()
    base_username = re.sub(r'[^a-z0-9_-]', '_', base_username)
    
    # If too short, add part of name
    if len(base_username) < 3:
        name_part = re.sub(r'[^a-z0-9_-]', '_', name.lower())[:10]
        base_username = f"{name_part}_{base_username}"
    
    # Truncate if too long
    base_username = base_username[:15]
    
    # Check if taken, add random suffix if needed
    username = base_username
    counter = 1
    while await is_username_taken(username):
        random_suffix = uuid.uuid4().hex[:4]
        username = f"{base_username}_{random_suffix}"
        counter += 1
        if counter > 10:  # Fallback to pure random
            username = f"user_{uuid.uuid4().hex[:12]}"
            break
    
    return username

class UserRegister(BaseModel):
    email: str
    password: str
    name: str
    username: str  # NEW: Required username

class UserLogin(BaseModel):
    email: str
    password: str

@auth_router.post("/register")
async def register(user_data: UserRegister, response: Response):
    """Register a new user manually"""
    
    # Validate password strength
    validate_strong_password(user_data.password)
    
    # Validate username
    validate_username(user_data.username)

    # Check if user exists
    try:
        existing_user = await db.users.find_one({"email": user_data.email})
        if existing_user:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Check if username is taken
        if await is_username_taken(user_data.username):
            raise HTTPException(status_code=400, detail="Username already taken")
        
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        hashed_password = get_password_hash(user_data.password)
        
        new_user = {
            "user_id": user_id,
            "email": user_data.email,
            "password_hash": hashed_password, 
            "name": user_data.name,
            "username": user_data.username.lower(),  # NEW: Save username
            "picture": f"https://api.dicebear.com/7.x/initials/svg?seed={user_data.name}", 
            "default_currency": "INR",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        
        await db.users.insert_one(new_user)
        
        # Link user to existing trips where they were added as a guest
        await link_user_to_existing_trips(user_id, user_data.email)
        
        # Create session immediately
        session_token = f"session_{uuid.uuid4().hex}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Set cookie with environment-aware security
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=IS_PRODUCTION,  # True in production, False in development
            samesite="strict" if IS_PRODUCTION else "lax",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        
        return {"user_id": user_id, "name": new_user["name"], "email": new_user["email"]}
    except Exception as e:
        logger.error(f"Registration error: {e}")
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Registration failed: {str(e)}")

@auth_router.post("/login")
async def login(login_data: UserLogin, response: Response):
    """Login with email and password"""
    user = await db.users.find_one({"email": login_data.email})
    
    if not user or not verify_password(login_data.password, user.get("password_hash", "")):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    
    # Create session
    session_token = f"session_{uuid.uuid4().hex}"
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user["user_id"],
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie with environment-aware security
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=IS_PRODUCTION,  # True in production, False in development
        samesite="strict" if IS_PRODUCTION else "lax",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    return {"user_id": user["user_id"], "name": user["name"], "email": user["email"]}

@auth_router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
    # Don't send password hash back
    user.pop("password_hash", None)
    # Return custom profile picture if available, otherwise OAuth picture
    if user.get("custom_profile_picture"):
        user["picture"] = user["custom_profile_picture"]
    return user

@auth_router.post("/logout")
async def logout(request: Request, response: Response):
    """Logout user"""
    session_token = request.cookies.get("session_token")
    
    if session_token:
        await db.user_sessions.delete_one({"session_token": session_token})
    
    response.delete_cookie(
        key="session_token",
        path="/",
        secure=IS_PRODUCTION,
        samesite="strict" if IS_PRODUCTION else "lax"
    )
    
    return {"message": "Logged out"}

async def link_user_to_existing_trips(user_id: str, email: str):
    """Link a newly registered/logged in user to trips they were added to as a guest"""
    try:
        # Get the user's current profile info
        user = await db.users.find_one({"user_id": user_id})
        if not user:
            return
            
        user_name = user.get("name", "")
        user_picture = user.get("picture", "")
        
        # Find all trips where this email exists as a guest member
        trips_cursor = db.trips.find({"members.email": email})
        trips = await trips_cursor.to_list(None)
        
        for trip in trips:
            # Find the member with this email and a guest user_id
            for i, member in enumerate(trip["members"]):
                if member["email"] == email and member["user_id"].startswith("guest_"):
                    old_user_id = member["user_id"]
                    logger.info(f"Linking user {user_id} to trip {trip['trip_id']}, replacing guest {old_user_id}")
                    
                    # Update trip member with user_id, name, and picture
                    trip["members"][i]["user_id"] = user_id
                    await db.trips.update_one(
                        {"trip_id": trip["trip_id"]},
                        {"$set": {
                            f"members.{i}.user_id": user_id,
                            f"members.{i}.name": user_name,
                            f"members.{i}.picture": user_picture
                        }}
                    )
                    
                    # Update all expenses where this user was a payer
                    await db.expenses.update_many(
                        {"trip_id": trip["trip_id"], "payers.user_id": old_user_id},
                        {"$set": {"payers.$[elem].user_id": user_id}},
                        array_filters=[{"elem.user_id": old_user_id}]
                    )
                    
                    # Update all expenses where this user was in splits
                    await db.expenses.update_many(
                        {"trip_id": trip["trip_id"], "splits.user_id": old_user_id},
                        {"$set": {"splits.$[elem].user_id": user_id}},
                        array_filters=[{"elem.user_id": old_user_id}]
                    )
                    
                    # Update all refunds
                    refunds_cursor = db.refunds.find({"trip_id": trip["trip_id"]})
                    refunds = await refunds_cursor.to_list(None)
                    for refund in refunds:
                        if old_user_id in refund.get("refunded_to", []):
                            new_refunded_to = [user_id if uid == old_user_id else uid for uid in refund["refunded_to"]]
                            await db.refunds.update_one(
                                {"refund_id": refund["refund_id"]},
                                {"$set": {"refunded_to": new_refunded_to}}
                            )
                    
                    # Update settlements if they exist
                    await db.settlements.update_many(
                        {"trip_id": trip["trip_id"], "from_user_id": old_user_id},
                        {"$set": {"from_user_id": user_id}}
                    )
                    await db.settlements.update_many(
                        {"trip_id": trip["trip_id"], "to_user_id": old_user_id},
                        {"$set": {"to_user_id": user_id}}
                    )
                    
                    logger.info(f"Successfully linked {email} to trip {trip['trip_id']}")
                    
    except Exception as e:
        logger.error(f"Error linking user to existing trips: {str(e)}")

async def update_user_in_all_trips(user_id: str, name: str, picture: str):
    """Update user's name and picture in all trips they're a member of"""
    try:
        # Find all trips where this user is a member
        trips_cursor = db.trips.find({"members.user_id": user_id})
        trips = await trips_cursor.to_list(None)
        
        for trip in trips:
            # Find the member index
            for i, member in enumerate(trip["members"]):
                if member["user_id"] == user_id:
                    # Update member's name and picture
                    await db.trips.update_one(
                        {"trip_id": trip["trip_id"]},
                        {"$set": {
                            f"members.{i}.name": name,
                            f"members.{i}.picture": picture
                        }}
                    )
                    logger.info(f"Updated user {user_id} profile in trip {trip['trip_id']}")
                    break
                    
    except Exception as e:
        logger.error(f"Error updating user in trips: {str(e)}")


# Google OAuth Login
class GoogleAuthRequest(BaseModel):
    id_token: str

@auth_router.post("/google")
async def google_auth(auth_data: GoogleAuthRequest, response: Response):
    """Authenticate with Google OAuth"""
    try:
        # Verify the Google ID token
        google_client_id = os.getenv('GOOGLE_CLIENT_ID')
        if not google_client_id:
            raise HTTPException(status_code=500, detail="Google OAuth not configured")
        
        # Verify the Google ID token with clock skew tolerance
        # This allows for small time differences between client and server
        idinfo = id_token.verify_oauth2_token(
            auth_data.id_token, 
            google_requests.Request(), 
            google_client_id,
            clock_skew_in_seconds=10  # Allow 10 seconds of clock skew
        )
        
        email = idinfo.get('email')
        name = idinfo.get('name')
        picture = idinfo.get('picture')
        google_id = idinfo.get('sub')
        
        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")
        
        # Check if user exists
        user = await db.users.find_one({"email": email})
        
        if user:
            # User exists - update their profile info from Google
            user_id = user["user_id"]
            
            # NEW: Ensure existing user has a username
            update_data = {
                "picture": picture,
                "name": name,
                "oauth_provider": "google",
                "oauth_id": google_id
            }
            
            # If user doesn't have username, generate one
            if not user.get("username"):
                new_username = await generate_unique_username(email, name)
                update_data["username"] = new_username
                logger.info(f"Auto-generated username {new_username} for existing user {user_id}")
            
            await db.users.update_one(
                {"user_id": user_id},
                {"$set": update_data}
            )
            
            # Update user's profile in all trips they're a member of
            await update_user_in_all_trips(user_id, name, picture)
        else:
            # Create new user with auto-generated username
            user_id = f"user_{uuid.uuid4().hex[:12]}"
            username = await generate_unique_username(email, name)
            
            new_user = {
                "user_id": user_id,
                "email": email,
                "name": name,
                "username": username,  # NEW: Auto-generated username
                "picture": picture,
                "oauth_provider": "google",
                "oauth_id": google_id,
                "default_currency": "INR",
                "created_at": datetime.now(timezone.utc).isoformat()
            }
            await db.users.insert_one(new_user)
            
            logger.info(f"Created new Google user with auto-generated username: {username}")
            
            # Link to existing trips
            await link_user_to_existing_trips(user_id, email)
        
        # Create session
        session_token = f"session_{uuid.uuid4().hex}"
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        
        await db.user_sessions.insert_one({
            "user_id": user_id,
            "session_token": session_token,
            "expires_at": expires_at.isoformat(),
            "created_at": datetime.now(timezone.utc).isoformat()
        })
        
        # Set cookie with environment-aware security
        response.set_cookie(
            key="session_token",
            value=session_token,
            httponly=True,
            secure=IS_PRODUCTION,  # True in production, False in development
            samesite="strict" if IS_PRODUCTION else "lax",
            path="/",
            max_age=7 * 24 * 60 * 60
        )
        
        return {"user_id": user_id, "name": name, "email": email, "picture": picture}
        
    except ValueError as e:
        logger.error(f"Google OAuth error: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid Google token")
    except Exception as e:
        logger.error(f"Google OAuth error: {str(e)}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@auth_router.put("/me")
async def update_user(
    update: UserUpdate,
    user: dict = Depends(get_current_user)
):
    """Update user profile"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if update_data:
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": update_data}
        )
        
        # If name or picture changed, update in all trips
        if "name" in update_data or "custom_profile_picture" in update_data:
            updated_user = await db.users.find_one({"user_id": user["user_id"]})
            display_picture = updated_user.get("custom_profile_picture") or updated_user.get("picture", "")
            await update_user_in_all_trips(
                user["user_id"], 
                update_data.get("name", user["name"]),
                display_picture
            )
    
    updated_user = await db.users.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )
    if updated_user:
        updated_user.pop("password_hash", None)
        # Return custom profile picture if available, otherwise OAuth picture
        if updated_user.get("custom_profile_picture"):
            updated_user["picture"] = updated_user["custom_profile_picture"]
        
    return updated_user

@auth_router.post("/upload-profile-picture")
async def upload_profile_picture(
    file: UploadFile = File(...),
    user: dict = Depends(get_current_user)
):
    """Upload a profile picture"""
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if file_ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400, 
                detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
            )
        
        # Read file content
        content = await file.read()
        
        # Validate file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=400,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / 1024 / 1024}MB"
            )
        
        # Validate it's actually an image using Pillow
        try:
            image = Image.open(io.BytesIO(content))
            image.verify()
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid image file")
        
        # Generate unique filename
        unique_filename = f"{uuid.uuid4().hex}{file_ext}"
        file_path = UPLOAD_DIR / unique_filename
        
        # Save file
        with open(file_path, "wb") as f:
            f.write(content)
        
        # Return URL
        file_url = f"/api/auth/uploads/profile-pictures/{unique_filename}"
        
        return {"url": file_url, "filename": unique_filename}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error uploading profile picture: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to upload image")

@auth_router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    user: dict = Depends(get_current_user)
):
    """Change password for non-OAuth users"""
    # Check if user has a password (not OAuth user)
    if not user.get("password_hash"):
        raise HTTPException(
            status_code=400, 
            detail="Cannot change password for OAuth users"
        )
    
    # Verify current password
    if not verify_password(password_data.current_password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Current password is incorrect")
    
    # Validate new password
    validate_strong_password(password_data.new_password)
    
    # Hash new password
    new_hash = get_password_hash(password_data.new_password)
    
    # Update password
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"password_hash": new_hash}}
    )
    
    return {"message": "Password updated successfully"}

# NEW: Username Search Endpoint
@auth_router.get("/search-user")
async def search_user(q: str):
    """Search for users by username or email"""
    query = q.strip().lower()
    
    # Search by username or email
    users = await db.users.find(
        {
            "$or": [
                {"username": {"$regex": f"^{query}", "$options": "i"}},
                {"email": {"$regex": f"^{query}", "$options": "i"}}
            ]
        },
        {"_id": 0, "user_id": 1, "username": 1, "name": 1, "email": 1, "picture": 1, "custom_profile_picture": 1}
    ).limit(10).to_list(10)
    
    # Use custom profile picture if available
    for user in users:
        if user.get("custom_profile_picture"):
            user["picture"] = user["custom_profile_picture"]
        user.pop("custom_profile_picture", None)
    
    return {"results": users}

# NEW: Username Update Endpoint
@auth_router.put("/me/username")
async def update_username(
    username_data: UsernameUpdate,
    user: dict = Depends(get_current_user)
):
    """Update user's username"""
    # Validate format
    validate_username(username_data.username)
    
    # Check if already taken (excluding current user)
    if await is_username_taken(username_data.username, exclude_user_id=user["user_id"]):
        raise HTTPException(status_code=400, detail="Username already taken")
    
    # Update username
    await db.users.update_one(
        {"user_id": user["user_id"]},
        {"$set": {"username": username_data.username.lower()}}
    )
    
    # Update username in all trips
    await update_username_in_all_trips(user["user_id"], username_data.username.lower())
    
    return {"message": "Username updated successfully", "username": username_data.username.lower()}

async def update_username_in_all_trips(user_id: str, username: str):
    """Update user's username in all trip members"""
    trips_cursor = db.trips.find({"members.user_id": user_id})
    trips = await trips_cursor.to_list(None)
    
    for trip in trips:
        for i, member in enumerate(trip["members"]):
            if member["user_id"] == user_id:
                await db.trips.update_one(
                    {"trip_id": trip["trip_id"]},
                    {"$set": {f"members.{i}.username": username}}
                )
                logger.info(f"Updated username for user {user_id} in trip {trip['trip_id']}")
                break

# Serve uploaded profile pictures
@auth_router.get("/uploads/profile-pictures/{filename}")
async def serve_profile_picture(filename: str):
    """Serve uploaded profile picture"""
    file_path = UPLOAD_DIR / filename
    
    if not file_path.exists() or not file_path.is_file():
        raise HTTPException(status_code=404, detail="Image not found")
    
    # Validate filename to prevent directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")
    
    return FileResponse(file_path)


# ========================
# TRIPS ROUTES
# ========================

@trips_router.post("", response_model=TripResponse)
async def create_trip(
    trip: TripCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new trip"""
    trip_id = f"trip_{uuid.uuid4().hex[:12]}"
    
    trip_doc = {
        "trip_id": trip_id,
        "name": trip.name,
        "description": trip.description,
        "currency": trip.currency,
        "cover_image": trip.cover_image,
        "created_by": user["user_id"],
        "members": [{
            "user_id": user["user_id"],
            "name": user["name"],
            "email": user["email"],
            "picture": user.get("picture")
        }],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.trips.insert_one(trip_doc)
    
    # Remove created_at from trip_doc before passing to TripResponse
    trip_response_data = {k: v for k, v in trip_doc.items() if k != "created_at"}
    
    return TripResponse(
        **trip_response_data,
        created_at=datetime.fromisoformat(trip_doc["created_at"]),
        total_expenses=0,
        your_balance=0
    )

@trips_router.get("", response_model=List[TripResponse])
async def get_trips(user: dict = Depends(get_current_user)):
    """Get all trips for current user"""
    trips = await db.trips.find(
        {"members.user_id": user["user_id"]},
        {"_id": 0}
    ).to_list(100)
    
    result = []
    for trip in trips:
        # Calculate total expenses and user balance
        expenses = await db.expenses.find(
            {"trip_id": trip["trip_id"]},
            {"_id": 0}
        ).to_list(1000)
        
        # Get all refunds for this trip
        all_refunds = await db.refunds.find(
            {"trip_id": trip["trip_id"]},
            {"_id": 0}
        ).to_list(1000)
        
        # Group refunds by expense_id
        refunds_by_expense = {}
        for refund in all_refunds:
            expense_id = refund["expense_id"]
            if expense_id not in refunds_by_expense:
                refunds_by_expense[expense_id] = []
            refunds_by_expense[expense_id].append(refund)
        
        # Calculate total expenses after refunds
        total_expenses = 0
        for e in expenses:
            total_refunded = sum(r["amount"] for r in refunds_by_expense.get(e["expense_id"], []))
            total_expenses += (e.get("total_amount", 0) - total_refunded)
        
        # Calculate user balance
        user_balance = 0
        for expense in expenses:
            # Calculate net expense amount after refunds
            expense_id = expense["expense_id"]
            expense_refunds = refunds_by_expense.get(expense_id, [])
            total_refunded = sum(r["amount"] for r in expense_refunds)
            net_amount = expense["total_amount"] - total_refunded
            original_amount = expense["total_amount"]
            
            # What user paid
            for payer in expense.get("payers", []):
                if payer["user_id"] == user["user_id"]:
                    user_balance += payer["amount"]
            
            # Subtract refunds from recipients (treat as negative payment)
            for refund in expense_refunds:
                if user["user_id"] in refund.get("refunded_to", []):
                    per_person_refund = refund["amount"] / len(refund["refunded_to"])
                    user_balance -= per_person_refund
            
            # What user owes (recalculated based on net amount)
            splits = expense.get("splits", [])
            if splits and original_amount > 0:
                for split in splits:
                    if split["user_id"] == user["user_id"]:
                        # Calculate proportional split of net amount
                        original_split_ratio = split["amount"] / original_amount
                        adjusted_split = net_amount * original_split_ratio
                        user_balance -= adjusted_split
        
        if isinstance(trip.get("created_at"), str):
            trip["created_at"] = datetime.fromisoformat(trip["created_at"])
        
        result.append(TripResponse(
            **trip,
            total_expenses=total_expenses,
            your_balance=round(user_balance, 2)
        ))
    
    return result

@trips_router.get("/{trip_id}", response_model=TripResponse)
async def get_trip(trip_id: str, user: dict = Depends(get_current_user)):
    """Get a specific trip"""
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    expenses = await db.expenses.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Get all refunds for this trip
    all_refunds = await db.refunds.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Group refunds by expense_id
    refunds_by_expense = {}
    for refund in all_refunds:
        expense_id = refund["expense_id"]
        if expense_id not in refunds_by_expense:
            refunds_by_expense[expense_id] = []
        refunds_by_expense[expense_id].append(refund)
    
    # Calculate total expenses after refunds
    total_expenses = 0
    for e in expenses:
        total_refunded = sum(r["amount"] for r in refunds_by_expense.get(e["expense_id"], []))
        total_expenses += (e.get("total_amount", 0) - total_refunded)
    
    user_balance = 0
    for expense in expenses:
        # Calculate net expense amount after refunds
        expense_id = expense["expense_id"]
        expense_refunds = refunds_by_expense.get(expense_id, [])
        total_refunded = sum(r["amount"] for r in expense_refunds)
        net_amount = expense["total_amount"] - total_refunded
        original_amount = expense["total_amount"]
        
        # What user paid
        for payer in expense.get("payers", []):
            if payer["user_id"] == user["user_id"]:
                user_balance += payer["amount"]
        
        # Subtract refunds from recipients (treat as negative payment)
        for refund in expense_refunds:
            if user["user_id"] in refund.get("refunded_to", []):
                per_person_refund = refund["amount"] / len(refund["refunded_to"])
                user_balance -= per_person_refund
        
        # What user owes (recalculated based on net amount)
        splits = expense.get("splits", [])
        if splits and original_amount > 0:
            for split in splits:
                if split["user_id"] == user["user_id"]:
                    # Calculate proportional split of net amount
                    original_split_ratio = split["amount"] / original_amount
                    adjusted_split = net_amount * original_split_ratio
                    user_balance -= adjusted_split
    
    if isinstance(trip.get("created_at"), str):
        trip["created_at"] = datetime.fromisoformat(trip["created_at"])
    
    return TripResponse(
        **trip,
        total_expenses=total_expenses,
        your_balance=round(user_balance, 2)
    )

@trips_router.post("/{trip_id}/members")
async def add_member(
    trip_id: str,
    member: TripAddMember,
    user: dict = Depends(get_current_user)
):
    """Add a member to trip"""
    # NEW: Support adding by username or email
    if not member.email and not member.username:
        raise HTTPException(status_code=400, detail="Provide email or username")
    
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # NEW: Build query to find user by username or email
    query = {}
    if member.username:
        query["username"] = member.username.lower()
    elif member.email:
        query["email"] = member.email
    
    # Check if member already exists in trip
    check_email = member.email if member.email else None
    check_username = member.username.lower() if member.username else None
    existing_member = next(
        (m for m in trip["members"] if 
         (check_email and m.get("email") == check_email) or
         (check_username and m.get("username") == check_username)),
        None
    )
    if existing_member:
        raise HTTPException(status_code=400, detail="Member already in trip")
    
    # Check if user exists in system
    existing_user = await db.users.find_one(query, {"_id": 0})
    
    if existing_user:
        # Use registered user's data
        new_member = {
            "user_id": existing_user["user_id"],
            "name": existing_user["name"],
            "email": existing_user["email"],
            "username": existing_user.get("username"),  # NEW: Include username
            "picture": existing_user.get("custom_profile_picture") or existing_user.get("picture")
        }
    else:
        # Create placeholder for non-registered users (guests)
        new_member = {
            "user_id": f"guest_{uuid.uuid4().hex[:8]}",
            "name": member.name,
            "email": member.email or f"guest_{uuid.uuid4().hex[:8]}@guest.local",
            "username": None,  # NEW: Guests don't have usernames
            "picture": None
        }
    
    await db.trips.update_one(
        {"trip_id": trip_id},
        {"$push": {"members": new_member}}
    )
    
    # Return response immediately - don't wait for email
    response_data = {"message": "Member added", "member": new_member}
    
    # Send email notification in background (non-blocking)
    async def send_email_background():
        try:
            trip_creator = next((m for m in trip["members"] if m["user_id"] == user["user_id"]), None)
            if trip_creator:
                await EmailService.send_member_added_notification(
                    trip_name=trip["name"],
                    new_member_name=new_member["name"],
                    new_member_email=new_member["email"],
                    added_by_name=trip_creator["name"]
                )
                logger.info(f"Sent member added notification to {new_member['email']}")
        except Exception as e:
            logger.error(f"Failed to send member added notification: {str(e)}")
    
    # Schedule email to be sent in background (fire and forget)
    import asyncio
    asyncio.create_task(send_email_background())
    
    return response_data

@trips_router.delete("/{trip_id}/members/{member_user_id}")
async def remove_member(
    trip_id: str,
    member_user_id: str,
    user: dict = Depends(get_current_user)
):
    """Remove a member from trip"""
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "created_by": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or not authorized")
    
    if member_user_id == user["user_id"]:
        raise HTTPException(status_code=400, detail="Cannot remove yourself")
    
    await db.trips.update_one(
        {"trip_id": trip_id},
        {"$pull": {"members": {"user_id": member_user_id}}}
    )
    
    return {"message": "Member removed"}

@trips_router.delete("/{trip_id}")
async def delete_trip(trip_id: str, user: dict = Depends(get_current_user)):
    """Delete a trip"""
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "created_by": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found or not authorized")
    
    await db.trips.delete_one({"trip_id": trip_id})
    await db.expenses.delete_many({"trip_id": trip_id})
    await db.refunds.delete_many({"trip_id": trip_id})
    
    return {"message": "Trip deleted"}

@trips_router.get("/{trip_id}/balances")
async def get_trip_balances(
    trip_id: str,
    user: dict = Depends(get_current_user)
) -> List[BalanceEntry]:
    """Get balances for all members in a trip"""
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Initialize balances for all members
    balances = {m["user_id"]: 0 for m in trip["members"]}
    member_names = {m["user_id"]: m["name"] for m in trip["members"]}
    
    expenses = await db.expenses.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Get all refunds for this trip
    all_refunds = await db.refunds.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).to_list(1000)
    
    # Group refunds by expense_id
    refunds_by_expense = {}
    for refund in all_refunds:
        expense_id = refund["expense_id"]
        if expense_id not in refunds_by_expense:
            refunds_by_expense[expense_id] = []
        refunds_by_expense[expense_id].append(refund)
    
    for expense in expenses:
        # Calculate net expense amount after refunds
        expense_id = expense["expense_id"]
        expense_refunds = refunds_by_expense.get(expense_id, [])
        total_refunded = sum(r["amount"] for r in expense_refunds)
        net_amount = expense["total_amount"] - total_refunded
        original_amount = expense["total_amount"]
        
        # Add what each person paid
        for payer in expense.get("payers", []):
            if payer["user_id"] in balances:
                balances[payer["user_id"]] += payer["amount"]
        
        # Subtract refunds from recipients (treat as negative payment)
        for refund in expense_refunds:
            for user_id in refund.get("refunded_to", []):
                if user_id in balances:
                    per_person_refund = refund["amount"] / len(refund["refunded_to"])
                    balances[user_id] -= per_person_refund
        
        # Recalculate splits based on net amount
        splits = expense.get("splits", [])
        if splits and original_amount > 0:
            # Calculate each person's share based on the net amount
            for split in splits:
                if split["user_id"] in balances:
                    # Calculate the proportional split of the net amount
                    original_split_ratio = split["amount"] / original_amount
                    adjusted_split = net_amount * original_split_ratio
                    balances[split["user_id"]] -= adjusted_split
    
    # Apply settlements to balances
    all_settlements = await db.settlements.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).to_list(1000)
    
    for settlement in all_settlements:
        # Reduce amount owed by from_user (increase their balance)
        if settlement["from_user_id"] in balances:
            balances[settlement["from_user_id"]] += settlement["amount"]
        # Reduce amount owed to to_user (decrease their balance)
        if settlement["to_user_id"] in balances:
            balances[settlement["to_user_id"]] -= settlement["amount"]
    
    return [
        BalanceEntry(
            user_id=uid,
            name=member_names.get(uid, "Unknown"),
            balance=round(bal, 2)
        )
        for uid, bal in balances.items()
    ]

@trips_router.get("/{trip_id}/settlements")
async def get_settlements(
    trip_id: str,
    user: dict = Depends(get_current_user)
) -> List[SettlementSuggestion]:
    """Get settlement suggestions for a trip"""
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    balances_list = await get_trip_balances(trip_id, user)
    
    # Separate creditors and debtors
    creditors = [(b.user_id, b.name, b.balance) for b in balances_list if b.balance > 0.01]
    debtors = [(b.user_id, b.name, -b.balance) for b in balances_list if b.balance < -0.01]
    
    settlements = []
    
    # Simple greedy algorithm for settlement
    creditors = sorted(creditors, key=lambda x: x[2], reverse=True)
    debtors = sorted(debtors, key=lambda x: x[2], reverse=True)
    
    i, j = 0, 0
    while i < len(creditors) and j < len(debtors):
        creditor_id, creditor_name, credit = creditors[i]
        debtor_id, debtor_name, debt = debtors[j]
        
        amount = min(credit, debt)
        
        if amount > 0.01:
            settlements.append(SettlementSuggestion(
                from_user_id=debtor_id,
                from_user_name=debtor_name,
                to_user_id=creditor_id,
                to_user_name=creditor_name,
                amount=round(amount, 2),
                currency=trip["currency"]
            ))
        
        creditors[i] = (creditor_id, creditor_name, credit - amount)
        debtors[j] = (debtor_id, debtor_name, debt - amount)
        
        if creditors[i][2] < 0.01:
            i += 1
        if debtors[j][2] < 0.01:
            j += 1
    
    return settlements

# ========================
# EXPENSES ROUTES
# ========================

@expenses_router.post("", response_model=ExpenseResponse)
async def create_expense(
    expense: ExpenseCreate,
    user: dict = Depends(get_current_user)
):
    """Create a new expense"""
    # Verify trip exists and user is member
    trip = await db.trips.find_one(
        {"trip_id": expense.trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    expense_id = f"exp_{uuid.uuid4().hex[:12]}"
    expense_date = expense.date or datetime.now(timezone.utc)
    
    expense_doc = {
        "expense_id": expense_id,
        "trip_id": expense.trip_id,
        "description": expense.description,
        "total_amount": expense.total_amount,
        "currency": expense.currency,
        "payers": [p.model_dump() for p in expense.payers],
        "splits": [s.model_dump() for s in expense.splits],
        "category": expense.category,
        "date": expense_date.isoformat(),
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.expenses.insert_one(expense_doc)
    
    # Send email notification to all trip members
    try:
        member_emails = [m["email"] for m in trip["members"] if m.get("email")]
        if member_emails:
            # Get payer names
            payer_names = []
            for payer in expense.payers:
                member = next((m for m in trip["members"] if m["user_id"] == payer.user_id), None)
                if member:
                    payer_names.append(member["name"])
            
            await EmailService.send_expense_added_notification(
                trip_name=trip["name"],
                expense_description=expense.description,
                amount=expense.total_amount,
                currency=expense.currency,
                payer_names=payer_names,
                recipient_emails=member_emails
            )
            logger.info(f"Sent expense notification to {len(member_emails)} trip members")
    except Exception as e:
        logger.warning(f"Failed to send expense notification: {str(e)}")
    
    # Remove date and created_at from expense_doc before passing to ExpenseResponse
    expense_response_data = {k: v for k, v in expense_doc.items() if k not in ["date", "created_at"]}
    
    return ExpenseResponse(
        **expense_response_data,
        date=expense_date,
        created_at=datetime.fromisoformat(expense_doc["created_at"]),
        refunds=[],
        net_amount=expense.total_amount
    )

@expenses_router.get("/trip/{trip_id}", response_model=List[ExpenseResponse])
async def get_trip_expenses(
    trip_id: str,
    user: dict = Depends(get_current_user)
):
    """Get all expenses for a trip"""
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    expenses = await db.expenses.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).sort("date", -1).to_list(1000)
    
    result = []
    for expense in expenses:
        # Get refunds for this expense
        refunds = await db.refunds.find(
            {"expense_id": expense["expense_id"]},
            {"_id": 0}
        ).to_list(100)
        
        total_refunded = sum(r["amount"] for r in refunds)
        net_amount = expense["total_amount"] - total_refunded
        
        refund_responses = []
        for r in refunds:
            if isinstance(r.get("created_at"), str):
                r["created_at"] = datetime.fromisoformat(r["created_at"])
            refund_responses.append(RefundResponse(
                **r,
                expense_description=expense["description"]
            ))
        
        if isinstance(expense.get("date"), str):
            expense["date"] = datetime.fromisoformat(expense["date"])
        if isinstance(expense.get("created_at"), str):
            expense["created_at"] = datetime.fromisoformat(expense["created_at"])
        
        result.append(ExpenseResponse(
            **expense,
            refunds=refund_responses,
            net_amount=net_amount
        ))
    
    return result

@expenses_router.get("/{expense_id}", response_model=ExpenseResponse)
async def get_expense(
    expense_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific expense"""
    expense = await db.expenses.find_one(
        {"expense_id": expense_id},
        {"_id": 0}
    )
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Verify user has access
    trip = await db.trips.find_one(
        {"trip_id": expense["trip_id"], "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    refunds = await db.refunds.find(
        {"expense_id": expense_id},
        {"_id": 0}
    ).to_list(100)
    
    total_refunded = sum(r["amount"] for r in refunds)
    
    refund_responses = []
    for r in refunds:
        if isinstance(r.get("created_at"), str):
            r["created_at"] = datetime.fromisoformat(r["created_at"])
        refund_responses.append(RefundResponse(
            **r,
            expense_description=expense["description"]
        ))
    
    if isinstance(expense.get("date"), str):
        expense["date"] = datetime.fromisoformat(expense["date"])
    if isinstance(expense.get("created_at"), str):
        expense["created_at"] = datetime.fromisoformat(expense["created_at"])
    
    return ExpenseResponse(
        **expense,
        refunds=refund_responses,
        net_amount=expense["total_amount"] - total_refunded
    )

@expenses_router.delete("/{expense_id}")
async def delete_expense(
    expense_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete an expense"""
    expense = await db.expenses.find_one(
        {"expense_id": expense_id, "created_by": user["user_id"]},
        {"_id": 0}
    )
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found or not authorized")
    
    await db.expenses.delete_one({"expense_id": expense_id})
    await db.refunds.delete_many({"expense_id": expense_id})
    
    return {"message": "Expense deleted"}

class ExpenseUpdate(BaseModel):
    description: Optional[str] = None
    total_amount: Optional[float] = None
    currency: Optional[str] = None
    payers: Optional[List[ExpensePayer]] = None
    splits: Optional[List[ExpenseSplit]] = None
    category: Optional[str] = None

@expenses_router.put("/{expense_id}", response_model=ExpenseResponse)
async def update_expense(
    expense_id: str,
    update: ExpenseUpdate,
    user: dict = Depends(get_current_user)
):
    """Update an expense"""
    expense = await db.expenses.find_one(
        {"expense_id": expense_id},
        {"_id": 0}
    )
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Verify user has access to the trip
    trip = await db.trips.find_one(
        {"trip_id": expense["trip_id"], "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Build update data
    update_data = {}
    if update.description is not None:
        update_data["description"] = update.description
    if update.total_amount is not None:
        update_data["total_amount"] = update.total_amount
    if update.currency is not None:
        update_data["currency"] = update.currency
    if update.payers is not None:
        update_data["payers"] = [p.model_dump() for p in update.payers]
    if update.splits is not None:
        update_data["splits"] = [s.model_dump() for s in update.splits]
    if update.category is not None:
        update_data["category"] = update.category
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.expenses.update_one(
            {"expense_id": expense_id},
            {"$set": update_data}
        )
    
    # Fetch updated expense
    updated_expense = await db.expenses.find_one(
        {"expense_id": expense_id},
        {"_id": 0}
    )
    
    # Get refunds
    refunds = await db.refunds.find(
        {"expense_id": expense_id},
        {"_id": 0}
    ).to_list(100)
    
    total_refunded = sum(r["amount"] for r in refunds)
    
    refund_responses = []
    for r in refunds:
        if isinstance(r.get("created_at"), str):
            r["created_at"] = datetime.fromisoformat(r["created_at"])
        refund_responses.append(RefundResponse(
            **r,
            expense_description=updated_expense["description"]
        ))
    
    if isinstance(updated_expense.get("date"), str):
        updated_expense["date"] = datetime.fromisoformat(updated_expense["date"])
    if isinstance(updated_expense.get("created_at"), str):
        updated_expense["created_at"] = datetime.fromisoformat(updated_expense["created_at"])
    
    return ExpenseResponse(
        **updated_expense,
        refunds=refund_responses,
        net_amount=updated_expense["total_amount"] - total_refunded
    )

# ========================
# REFUNDS ROUTES
# ========================

@refunds_router.post("", response_model=RefundResponse)
async def create_refund(
    refund: RefundCreate,
    user: dict = Depends(get_current_user)
):
    """Create a refund for an expense"""
    expense = await db.expenses.find_one(
        {"expense_id": refund.expense_id},
        {"_id": 0}
    )
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    # Verify user has access
    trip = await db.trips.find_one(
        {"trip_id": expense["trip_id"], "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    refund_id = f"ref_{uuid.uuid4().hex[:12]}"
    
    refund_doc = {
        "refund_id": refund_id,
        "expense_id": refund.expense_id,
        "trip_id": expense["trip_id"],
        "amount": refund.amount,
        "reason": refund.reason,
        "refunded_to": refund.refunded_to,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.refunds.insert_one(refund_doc)
    
    # Remove created_at from refund_doc before passing to RefundResponse
    refund_response_data = {k: v for k, v in refund_doc.items() if k != "created_at"}
    
    return RefundResponse(
        **refund_response_data,
        expense_description=expense["description"],
        created_at=datetime.fromisoformat(refund_doc["created_at"])
    )

@refunds_router.get("/expense/{expense_id}", response_model=List[RefundResponse])
async def get_expense_refunds(
    expense_id: str,
    user: dict = Depends(get_current_user)
):
    """Get all refunds for an expense"""
    expense = await db.expenses.find_one(
        {"expense_id": expense_id},
        {"_id": 0}
    )
    
    if not expense:
        raise HTTPException(status_code=404, detail="Expense not found")
    
    trip = await db.trips.find_one(
        {"trip_id": expense["trip_id"], "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    refunds = await db.refunds.find(
        {"expense_id": expense_id},
        {"_id": 0}
    ).to_list(100)
    
    result = []
    for r in refunds:
        if isinstance(r.get("created_at"), str):
            r["created_at"] = datetime.fromisoformat(r["created_at"])
        result.append(RefundResponse(
            **r,
            expense_description=expense["description"]
        ))
    
    return result

@refunds_router.delete("/{refund_id}")
async def delete_refund(
    refund_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a refund"""
    refund = await db.refunds.find_one(
        {"refund_id": refund_id, "created_by": user["user_id"]},
        {"_id": 0}
    )
    
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found or not authorized")
    
    await db.refunds.delete_one({"refund_id": refund_id})
    
    return {"message": "Refund deleted"}

class RefundUpdate(BaseModel):
    amount: Optional[float] = None
    reason: Optional[str] = None
    refunded_to: Optional[List[str]] = None

@refunds_router.put("/{refund_id}", response_model=RefundResponse)
async def update_refund(
    refund_id: str,
    update: RefundUpdate,
    user: dict = Depends(get_current_user)
):
    """Update a refund"""
    refund = await db.refunds.find_one(
        {"refund_id": refund_id},
        {"_id": 0}
    )
    
    if not refund:
        raise HTTPException(status_code=404, detail="Refund not found")
    
    # Verify user has access to the trip
    trip = await db.trips.find_one(
        {"trip_id": refund["trip_id"], "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Get expense for response
    expense = await db.expenses.find_one(
        {"expense_id": refund["expense_id"]},
        {"_id": 0}
    )
    
    # Build update data
    update_data = {}
    if update.amount is not None:
        update_data["amount"] = update.amount
    if update.reason is not None:
        update_data["reason"] = update.reason
    if update.refunded_to is not None:
        update_data["refunded_to"] = update.refunded_to
    
    if update_data:
        update_data["updated_at"] = datetime.now(timezone.utc).isoformat()
        await db.refunds.update_one(
            {"refund_id": refund_id},
            {"$set": update_data}
        )
    
    # Fetch updated refund
    updated_refund = await db.refunds.find_one(
        {"refund_id": refund_id},
        {"_id": 0}
    )
    
    if isinstance(updated_refund.get("created_at"), str):
        updated_refund["created_at"] = datetime.fromisoformat(updated_refund["created_at"])
    
    return RefundResponse(
        **{k: v for k, v in updated_refund.items() if k not in ["created_at", "updated_at"]},
        expense_description=expense["description"] if expense else "",
        created_at=updated_refund["created_at"]
    )

# ========================
# CURRENCIES
# ========================

SUPPORTED_CURRENCIES = [
    {"code": "INR", "symbol": "\u20b9", "name": "Indian Rupee"},
    {"code": "USD", "symbol": "$", "name": "US Dollar"},
    {"code": "EUR", "symbol": "\u20ac", "name": "Euro"},
    {"code": "GBP", "symbol": "\u00a3", "name": "British Pound"},
    {"code": "JPY", "symbol": "\u00a5", "name": "Japanese Yen"},
    {"code": "AUD", "symbol": "A$", "name": "Australian Dollar"},
    {"code": "CAD", "symbol": "C$", "name": "Canadian Dollar"},
    {"code": "CHF", "symbol": "Fr", "name": "Swiss Franc"},
    {"code": "CNY", "symbol": "\u00a5", "name": "Chinese Yuan"},
    {"code": "SGD", "symbol": "S$", "name": "Singapore Dollar"},
    {"code": "THB", "symbol": "\u0e3f", "name": "Thai Baht"},
    {"code": "MXN", "symbol": "$", "name": "Mexican Peso"},
    {"code": "BRL", "symbol": "R$", "name": "Brazilian Real"},
]

@api_router.get("/currencies")
async def get_currencies():
    """Get list of supported currencies"""
    return SUPPORTED_CURRENCIES

# ========================
# AI TRIP PLANNER ROUTES
# ========================

from trip_planner import trip_planner, TripPlanRequest, TripPlanResponse

class SavedTripPlan(BaseModel):
    model_config = ConfigDict(extra="ignore")
    plan_id: str
    user_id: str
    destination: str
    start_date: str
    end_date: str
    num_travelers: int
    plan_data: Dict[str, Any]
    created_at: datetime

@planner_router.post("/generate", response_model=TripPlanResponse)
async def generate_trip_plan(
    request: TripPlanRequest,
    user: dict = Depends(get_current_user)
):
    """Generate an AI-powered trip plan"""
    try:
        plan = await trip_planner.generate_trip_plan(request, user["user_id"])
        return plan
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Trip planning error: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate trip plan. Please try again.")

@planner_router.post("/save")
async def save_trip_plan(
    plan: Dict[str, Any],
    user: dict = Depends(get_current_user)
):
    """Save a generated trip plan"""
    plan_id = f"plan_{uuid.uuid4().hex[:12]}"
    
    plan_doc = {
        "plan_id": plan_id,
        "user_id": user["user_id"],
        "destination": plan.get("destination", ""),
        "start_date": plan.get("start_date", ""),
        "end_date": plan.get("end_date", ""),
        "num_travelers": plan.get("num_travelers", 1),
        "plan_data": plan,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.saved_plans.insert_one(plan_doc)
    
    return {"message": "Plan saved", "plan_id": plan_id}

@planner_router.get("/saved", response_model=List[SavedTripPlan])
async def get_saved_plans(user: dict = Depends(get_current_user)):
    """Get all saved trip plans for the user"""
    plans = await db.saved_plans.find(
        {"user_id": user["user_id"]},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    for plan in plans:
        if isinstance(plan.get("created_at"), str):
            plan["created_at"] = datetime.fromisoformat(plan["created_at"])
    
    return plans

@planner_router.get("/saved/{plan_id}")
async def get_saved_plan(
    plan_id: str,
    user: dict = Depends(get_current_user)
):
    """Get a specific saved plan"""
    plan = await db.saved_plans.find_one(
        {"plan_id": plan_id, "user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return plan

@planner_router.delete("/saved/{plan_id}")
async def delete_saved_plan(
    plan_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a saved plan"""
    result = await db.saved_plans.delete_one(
        {"plan_id": plan_id, "user_id": user["user_id"]}
    )
    
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Plan not found")
    
    return {"message": "Plan deleted"}

# Admin endpoint to update LLM key
class LLMKeyUpdate(BaseModel):
    key: str

@planner_router.put("/admin/llm-key")
async def update_llm_key(
    key_update: LLMKeyUpdate,
    user: dict = Depends(get_current_user)
):
    """Update the LLM API key (admin only)"""
    # Store in database for persistence
    await db.settings.update_one(
        {"setting": "llm_key"},
        {"$set": {"value": key_update.key, "updated_by": user["user_id"], "updated_at": datetime.now(timezone.utc).isoformat()}},
        upsert=True
    )
    
    # Update environment variable for current session
    os.environ['EMERGENT_LLM_KEY'] = key_update.key
    
    return {"message": "LLM key updated successfully"}

# ========================
# ADMIN ROUTES
# ========================

from admin_service import (
    DEFAULT_FEATURE_TOGGLES, 
    DEFAULT_SITE_CONTENT, 
    LLM_MODELS,
    FeatureToggle,
    SiteContent,
    AppSettings,
    AdminStats
)

# Admin authentication check
async def get_admin_user(request: Request) -> dict:
    """Get current user and verify admin status"""
    user = await get_current_user(request)
    
    # Check if user is admin
    admin_doc = await db.admins.find_one({"user_id": user["user_id"]}, {"_id": 0})
    if not admin_doc:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    return user

# Initialize default settings
async def init_admin_defaults():
    """Initialize default feature toggles and site content if not exists"""
    # Feature toggles
    existing_toggles = await db.feature_toggles.count_documents({})
    if existing_toggles == 0:
        await db.feature_toggles.insert_many(DEFAULT_FEATURE_TOGGLES)
    
    # Site content
    existing_content = await db.site_content.count_documents({})
    if existing_content == 0:
        await db.site_content.insert_many(DEFAULT_SITE_CONTENT)
    
    # App settings
    existing_settings = await db.app_settings.find_one({"setting_id": "main"})
    if not existing_settings:
        await db.app_settings.insert_one({
            "setting_id": "main",
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "default_currency": "INR",
            "maintenance_mode": False,
            "registration_enabled": True,
            "ai_planner_enabled": True,
            "max_trips_per_user": 50,
            "max_members_per_trip": 20
        })

@app.on_event("startup")
async def startup_event():
    await init_admin_defaults()

# --- Stats ---
@admin_router.get("/stats")
async def get_admin_stats(user: dict = Depends(get_admin_user)):
    """Get admin dashboard statistics"""
    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_ago = now - timedelta(days=7)
    
    total_users = await db.users.count_documents({})
    total_trips = await db.trips.count_documents({})
    total_expenses = await db.expenses.count_documents({})
    total_refunds = await db.refunds.count_documents({})
    total_saved_plans = await db.saved_plans.count_documents({})
    
    # Active users today (sessions created today)
    active_today = await db.user_sessions.count_documents({
        "created_at": {"$gte": today_start.isoformat()}
    })
    
    # New users this week
    new_this_week = await db.users.count_documents({
        "created_at": {"$gte": week_ago.isoformat()}
    })
    
    # Popular destinations from saved plans
    pipeline = [
        {"$group": {"_id": "$destination", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 5}
    ]
    destinations = await db.saved_plans.aggregate(pipeline).to_list(5)
    popular_destinations = [{"destination": d["_id"], "count": d["count"]} for d in destinations if d["_id"]]
    
    # Expenses by currency
    currency_pipeline = [
        {"$group": {"_id": "$currency", "total": {"$sum": "$total_amount"}, "count": {"$sum": 1}}},
        {"$sort": {"total": -1}}
    ]
    currencies = await db.expenses.aggregate(currency_pipeline).to_list(10)
    expense_by_currency = [{"currency": c["_id"], "total": c["total"], "count": c["count"]} for c in currencies if c["_id"]]
    
    return {
        "total_users": total_users,
        "total_trips": total_trips,
        "total_expenses": total_expenses,
        "total_refunds": total_refunds,
        "total_saved_plans": total_saved_plans,
        "active_users_today": active_today,
        "new_users_this_week": new_this_week,
        "popular_destinations": popular_destinations,
        "expense_by_currency": expense_by_currency
    }

# --- Users Management ---
@admin_router.get("/users")
async def get_all_users(
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_admin_user)
):
    """Get all users with pagination"""
    users = await db.users.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.users.count_documents({})
    
    # Add trip count for each user
    for u in users:
        u["trip_count"] = await db.trips.count_documents({"members.user_id": u["user_id"]})
        u["is_admin"] = await db.admins.find_one({"user_id": u["user_id"]}) is not None
    
    return {"users": users, "total": total, "skip": skip, "limit": limit}

@admin_router.post("/users/{user_id}/toggle-admin")
async def toggle_admin_status(
    user_id: str,
    user: dict = Depends(get_admin_user)
):
    """Toggle admin status for a user"""
    target_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    existing_admin = await db.admins.find_one({"user_id": user_id})
    
    if existing_admin:
        await db.admins.delete_one({"user_id": user_id})
        return {"message": "Admin access revoked", "is_admin": False}
    else:
        await db.admins.insert_one({
            "user_id": user_id,
            "granted_by": user["user_id"],
            "granted_at": datetime.now(timezone.utc).isoformat()
        })
        return {"message": "Admin access granted", "is_admin": True}

@admin_router.post("/users/{user_id}/toggle-status")
async def toggle_user_status(
    user_id: str,
    user: dict = Depends(get_admin_user)
):
    """Enable/disable a user account"""
    target_user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not target_user.get("disabled", False)
    await db.users.update_one(
        {"user_id": user_id},
        {"$set": {"disabled": new_status}}
    )
    
    if new_status:
        # Invalidate all sessions for disabled user
        await db.user_sessions.delete_many({"user_id": user_id})
    
    return {"message": f"User {'disabled' if new_status else 'enabled'}", "disabled": new_status}

# --- Trips Management ---
@admin_router.get("/trips")
async def get_all_trips(
    skip: int = 0,
    limit: int = 50,
    user: dict = Depends(get_admin_user)
):
    """Get all trips with pagination"""
    trips = await db.trips.find({}, {"_id": 0}).skip(skip).limit(limit).to_list(limit)
    total = await db.trips.count_documents({})
    
    for trip in trips:
        trip["expense_count"] = await db.expenses.count_documents({"trip_id": trip["trip_id"]})
        if isinstance(trip.get("created_at"), str):
            trip["created_at"] = datetime.fromisoformat(trip["created_at"])
    
    return {"trips": trips, "total": total, "skip": skip, "limit": limit}

@admin_router.delete("/trips/{trip_id}")
async def admin_delete_trip(
    trip_id: str,
    user: dict = Depends(get_admin_user)
):
    """Delete a trip (admin)"""
    trip = await db.trips.find_one({"trip_id": trip_id}, {"_id": 0})
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    await db.trips.delete_one({"trip_id": trip_id})
    await db.expenses.delete_many({"trip_id": trip_id})
    await db.refunds.delete_many({"trip_id": trip_id})
    
    return {"message": "Trip deleted"}

# --- Feature Toggles ---
@admin_router.get("/features")
async def get_feature_toggles(user: dict = Depends(get_admin_user)):
    """Get all feature toggles"""
    toggles = await db.feature_toggles.find({}, {"_id": 0}).to_list(100)
    return toggles

@admin_router.put("/features/{feature_id}")
async def update_feature_toggle(
    feature_id: str,
    enabled: bool,
    user: dict = Depends(get_admin_user)
):
    """Update a feature toggle"""
    result = await db.feature_toggles.update_one(
        {"feature_id": feature_id},
        {"$set": {"enabled": enabled, "updated_by": user["user_id"], "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Feature not found")
    
    return {"message": "Feature updated", "feature_id": feature_id, "enabled": enabled}

@admin_router.put("/features/bulk")
async def bulk_update_features(
    updates: List[Dict[str, Any]],
    user: dict = Depends(get_admin_user)
):
    """Bulk update feature toggles"""
    for update in updates:
        await db.feature_toggles.update_one(
            {"feature_id": update["feature_id"]},
            {"$set": {"enabled": update["enabled"], "updated_by": user["user_id"], "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"message": f"Updated {len(updates)} features"}

# --- Site Content ---
@admin_router.get("/content")
async def get_site_content(user: dict = Depends(get_admin_user)):
    """Get all editable site content"""
    content = await db.site_content.find({}, {"_id": 0}).to_list(100)
    return content

@admin_router.put("/content/{content_id}")
async def update_site_content(
    content_id: str,
    value: str,
    user: dict = Depends(get_admin_user)
):
    """Update site content"""
    result = await db.site_content.update_one(
        {"content_id": content_id},
        {"$set": {"value": value, "updated_by": user["user_id"], "updated_at": datetime.now(timezone.utc).isoformat()}}
    )
    
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Content not found")
    
    return {"message": "Content updated", "content_id": content_id}

@admin_router.put("/content/bulk")
async def bulk_update_content(
    updates: List[Dict[str, str]],
    user: dict = Depends(get_admin_user)
):
    """Bulk update site content"""
    for update in updates:
        await db.site_content.update_one(
            {"content_id": update["content_id"]},
            {"$set": {"value": update["value"], "updated_by": user["user_id"], "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
    
    return {"message": f"Updated {len(updates)} content items"}

# --- App Settings ---
@admin_router.get("/settings")
async def get_app_settings(user: dict = Depends(get_admin_user)):
    """Get app settings"""
    settings = await db.app_settings.find_one({"setting_id": "main"}, {"_id": 0})
    if not settings:
        settings = {
            "setting_id": "main",
            "llm_provider": "openai",
            "llm_model": "gpt-4o",
            "default_currency": "INR",
            "maintenance_mode": False,
            "registration_enabled": True,
            "ai_planner_enabled": True,
            "max_trips_per_user": 50,
            "max_members_per_trip": 20
        }
    
    # Add available models
    settings["available_models"] = LLM_MODELS
    
    return settings

@admin_router.put("/settings")
async def update_app_settings(
    settings: Dict[str, Any],
    user: dict = Depends(get_admin_user)
):
    """Update app settings"""
    # Don't allow updating certain fields
    settings.pop("setting_id", None)
    settings.pop("available_models", None)
    
    settings["updated_by"] = user["user_id"]
    settings["updated_at"] = datetime.now(timezone.utc).isoformat()
    
    await db.app_settings.update_one(
        {"setting_id": "main"},
        {"$set": settings},
        upsert=True
    )
    
    # Update LLM key in environment if provided
    if "llm_key" in settings and settings["llm_key"]:
        os.environ['EMERGENT_LLM_KEY'] = settings["llm_key"]
    
    return {"message": "Settings updated"}

# --- Public endpoints for feature flags and content ---
@api_router.get("/public/features")
async def get_public_features():
    """Get enabled features for frontend (no auth required)"""
    toggles = await db.feature_toggles.find({}, {"_id": 0, "feature_id": 1, "enabled": 1}).to_list(100)
    return {t["feature_id"]: t["enabled"] for t in toggles}

@api_router.get("/public/content")
async def get_public_content():
    """Get site content for frontend (no auth required)"""
    content = await db.site_content.find({}, {"_id": 0}).to_list(100)
    # Organize by section
    organized = {}
    for c in content:
        section = c.get("section", "other")
        if section not in organized:
            organized[section] = {}
        organized[section][c["key"]] = c["value"]
    return organized

# ========================
# SETTLEMENTS ROUTES
# ========================

@settlements_router.post("", response_model=SettlementEntry)
async def create_settlement(
    settlement: SettlementCreate,
    user: dict = Depends(get_current_user)
):
    """Record a settlement/payment between trip members"""
    trip = await db.trips.find_one(
        {"trip_id": settlement.trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Get member names
    from_member = next((m for m in trip["members"] if m["user_id"] == settlement.from_user_id), None)
    to_member = next((m for m in trip["members"] if m["user_id"] == settlement.to_user_id), None)
    
    if not from_member or not to_member:
        raise HTTPException(status_code=400, detail="Invalid user IDs")
    
    settlement_id = f"settlement_{uuid.uuid4().hex[:12]}"
    settlement_doc = {
        "settlement_id": settlement_id,
        "trip_id": settlement.trip_id,
        "from_user_id": settlement.from_user_id,
        "from_user_name": from_member["name"],
        "to_user_id": settlement.to_user_id,
        "to_user_name": to_member["name"],
        "amount": settlement.amount,
        "note": settlement.note,
        "created_by": user["user_id"],
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    
    await db.settlements.insert_one(settlement_doc)
    
    # Send email notification to all trip members
    try:
        member_emails = [m["email"] for m in trip["members"] if m.get("email")]
        if member_emails:
            await EmailService.send_settlement_notification(
                trip_name=trip["name"],
                from_user_name=from_member["name"],
                to_user_name=to_member["name"],
                amount=settlement.amount,
                currency=trip["currency"],
                recipient_emails=member_emails,
                note=settlement.note
            )
    except Exception as e:
        logger.warning(f"Failed to send settlement notification: {str(e)}")
    
    if isinstance(settlement_doc.get("created_at"), str):
        settlement_doc["created_at"] = datetime.fromisoformat(settlement_doc["created_at"])
    
    return SettlementEntry(**settlement_doc)

@settlements_router.get("/{trip_id}", response_model=List[SettlementEntry])
async def get_settlements(
    trip_id: str,
    user: dict = Depends(get_current_user)
):
    """Get all settlements for a trip"""
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    settlements = await db.settlements.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).sort("created_at", -1).to_list(100)
    
    result = []
    for s in settlements:
        if isinstance(s.get("created_at"), str):
            s["created_at"] = datetime.fromisoformat(s["created_at"])
        result.append(SettlementEntry(**s))
    
    return result

@settlements_router.delete("/{settlement_id}")
async def delete_settlement(
    settlement_id: str,
    user: dict = Depends(get_current_user)
):
    """Delete a settlement (undo)"""
    settlement = await db.settlements.find_one(
        {"settlement_id": settlement_id},
        {"_id": 0}
    )
    
    if not settlement:
        raise HTTPException(status_code=404, detail="Settlement not found")
    
    # Only the creator can delete
    if settlement["created_by"] != user["user_id"]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    await db.settlements.delete_one({"settlement_id": settlement_id})
    
    return {"message": "Settlement deleted"}

# ========================
# ADMIN MANAGEMENT ROUTES
# ========================

@api_router.get("/public/settings")
async def get_public_settings():
    """Get public app settings (no auth required)"""
    settings = await db.app_settings.find_one({"setting_id": "main"}, {"_id": 0})
    if not settings:
        return {
            "maintenance_mode": False,
            "registration_enabled": True,
            "ai_planner_enabled": True
        }
    
    # Only return public settings
    return {
        "maintenance_mode": settings.get("maintenance_mode", False),
        "registration_enabled": settings.get("registration_enabled", True),
        "ai_planner_enabled": settings.get("ai_planner_enabled", True)
    }

# --- Check Admin Status ---
@admin_router.get("/check")
async def check_admin_status(user: dict = Depends(get_current_user)):
    """Check if current user is admin"""
    admin_doc = await db.admins.find_one({"user_id": user["user_id"]}, {"_id": 0})
    return {"is_admin": admin_doc is not None}

# ========================
# TRIP PLANNER ROUTES
# ========================

@planner_router.post("/generate", response_model=TripPlanResponse)
async def generate_trip_plan(
    request: TripPlanRequest,
    user: dict = Depends(get_current_user)
):
    """Generate a trip plan using AI"""
    try:
        plan = await trip_planner.generate_trip_plan(request, user["user_id"])
        return plan
    except Exception as e:
        logger.error(f"Trip generation error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@planner_router.post("/save")
async def save_trip_plan(
    plan: TripPlanResponse,
    user: dict = Depends(get_current_user)
):
    """Save a generated trip plan"""
    try:
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        plan_doc = plan.model_dump()
        plan_doc["plan_id"] = plan_id
        plan_doc["user_id"] = user["user_id"]
        plan_doc["created_at"] = datetime.now(timezone.utc).isoformat()
        
        await db.trip_plans.insert_one(plan_doc)
        
        return {"message": "Trip plan saved successfully", "plan_id": plan_id}
    except Exception as e:
        logger.error(f"Trip save error: {e}")
        raise HTTPException(status_code=500, detail="Failed to save trip plan")

@planner_router.get("/plans")
async def get_user_plans(user: dict = Depends(get_current_user)):
    """Get all saved trip plans for the current user"""
    try:
        plans = await db.trip_plans.find(
            {"user_id": user["user_id"]},
            {"_id": 0}
        ).sort("created_at", -1).to_list(100)
        return plans
    except Exception as e:
        logger.error(f"Error fetching trip plans: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch trip plans")

# ========================
# USER TRIP PLANS ROUTES
# ========================

user_plans_router = APIRouter(prefix="/user/plans", tags=["user-plans"])

@user_plans_router.post("")
async def save_trip_plan(plan: TripPlan, user: dict = Depends(get_current_user)):
    """Save a trip plan to user's profile"""
    try:
        plan_id = f"plan_{uuid.uuid4().hex[:12]}"
        saved_plan = {
            "plan_id": plan_id,
            "destination": plan.destination,
            "start_date": plan.start_date,
            "end_date": plan.end_date,
            "num_days": plan.num_days,
            "num_travelers": plan.num_travelers,
            "itinerary": plan.itinerary,
            "best_time_to_visit": plan.best_time_to_visit,
            "weather_summary": plan.weather_summary,
            "cost_breakdown": plan.cost_breakdown,
            "departure_transport_details": plan.departure_transport_details,
            "return_transport_details": plan.return_transport_details,
            "travel_tips": plan.travel_tips,
            "packing_suggestions": plan.packing_suggestions,
            "packing_suggestions_detailed": plan.packing_suggestions_detailed,
            "local_customs": plan.local_customs,
            "emergency_contacts": plan.emergency_contacts,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "linked_to_trip": None
        }
        
        # Initialize trip_plans array if it doesn't exist
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$setOnInsert": {"trip_plans": []}},
            upsert=False
        )
        
        # Add the plan
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$push": {"trip_plans": saved_plan}}
        )
        
        logger.info(f"User {user['user_id']} saved trip plan {plan_id}")
        return {"plan_id": plan_id, "message": "Plan saved successfully"}
    except Exception as e:
        logger.error(f"Error saving trip plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to save trip plan")

@user_plans_router.get("")
async def get_user_plans(user: dict = Depends(get_current_user)):
    """Get all saved trip plans for the current user"""
    try:
        user_data = await db.users.find_one(
            {"user_id": user["user_id"]},
            {"trip_plans": 1}
        )
        return user_data.get("trip_plans", []) if user_data else []
    except Exception as e:
        logger.error(f"Error fetching user plans: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch plans")

@user_plans_router.delete("/{plan_id}")
async def delete_trip_plan(plan_id: str, user: dict = Depends(get_current_user)):
    """Delete a saved trip plan"""
    try:
        result = await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$pull": {"trip_plans": {"plan_id": plan_id}}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Plan not found")
        
        logger.info(f"User {user['user_id']} deleted trip plan {plan_id}")
        return {"message": "Plan deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting trip plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to delete plan")

@trips_router.post("/{trip_id}/link-plan")
async def link_plan_to_trip(
    trip_id: str,
    request: LinkPlanRequest,
    user: dict = Depends(get_current_user)
):
    """Link a saved trip plan to a specific trip"""
    try:
        # Verify user is a member of the trip
        trip = await db.trips.find_one({
            "trip_id": trip_id,
            "members.user_id": user["user_id"]
        })
        
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found or access denied")
        
        # Update trip with linked plan
        await db.trips.update_one(
            {"trip_id": trip_id},
            {"$set": {"linked_plan_id": request.plan_id}}
        )
        
        # Update plan's linked_to_trip field in user's plans
        await db.users.update_one(
            {
                "user_id": user["user_id"],
                "trip_plans.plan_id": request.plan_id
            },
            {"$set": {"trip_plans.$.linked_to_trip": trip_id}}
        )
        
        logger.info(f"Linked plan {request.plan_id} to trip {trip_id}")
        return {"message": "Plan linked to trip successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking plan to trip: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to link plan")

@trips_router.get("/{trip_id}/plan")
async def get_trip_plan(trip_id: str, user: dict = Depends(get_current_user)):
    """Get the trip plan linked to a specific trip"""
    try:
        trip = await db.trips.find_one({
            "trip_id": trip_id,
            "members.user_id": user["user_id"]
        })
        
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found or access denied")
        
        if not trip.get("linked_plan_id"):
            return None
        
        # Find the plan in user's saved plans
        user_data = await db.users.find_one(
            {"user_id": user["user_id"]},
            {"trip_plans": 1}
        )
        
        if not user_data:
            return None
        
        plan = next((p for p in user_data.get("trip_plans", [])
                    if p["plan_id"] == trip["linked_plan_id"]), None)
        return plan
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching trip plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to fetch trip plan")

@trips_router.delete("/{trip_id}/plan")
async def unlink_trip_plan(trip_id: str, user: dict = Depends(get_current_user)):
    """Unlink a plan from a trip (doesn't delete the plan)"""
    try:
        trip = await db.trips.find_one({
            "trip_id": trip_id,
            "members.user_id": user["user_id"]
        })
        
        if not trip:
            raise HTTPException(status_code=404, detail="Trip not found or access denied")
        
        plan_id = trip.get("linked_plan_id")
        
        # Remove linked_plan_id from trip
        await db.trips.update_one(
            {"trip_id": trip_id},
            {"$unset": {"linked_plan_id": ""}}
        )
        
        # Update plan's linked_to_trip field
        if plan_id:
            await db.users.update_one(
                {
                    "user_id": user["user_id"],
                    "trip_plans.plan_id": plan_id
                },
                {"$set": {"trip_plans.$.linked_to_trip": None}}
            )
        
        logger.info(f"Unlinked plan from trip {trip_id}")
        return {"message": "Plan unlinked from trip"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error unlinking plan: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to unlink plan")

# ========================
# LOCATION SEARCH & FAVORITES ROUTES
# ========================

locations_router = APIRouter(prefix="/locations", tags=["locations"])

class FavoriteLocation(BaseModel):
    id: str
    name: str
    display_name: str
    country: str
    state: Optional[str] = None
    lat: float
    lon: float

@locations_router.get("/search")
async def search_locations(q: str):
    """Search for locations using Photon geocoding API"""
    try:
        if not q or len(q.strip()) < 2:
            return {"locations": []}
        
        logger.info(f"Searching for location: {q}")
        
        # Use Photon API - free, open-source geocoding based on OpenStreetMap
        try:
            # Add User-Agent header to prevent 403 Forbidden errors
            headers = {
                "User-Agent": "EZ-Trip/1.0 (Travel Planning Application; contact@example.com)"
            }
            
            async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
                logger.info(f"Calling Photon API: https://photon.komoot.io/api/?q={q}")
                response = await client.get(
                    "https://photon.komoot.io/api/",
                    params={"q": q, "limit": 10}
                )
                logger.info(f"Photon API response status: {response.status_code}")
                response.raise_for_status()
                data = response.json()
                logger.info(f"Photon API returned {len(data.get('features', []))} results")
        except httpx.TimeoutException as e:
            logger.error(f"Photon API timeout for query '{q}': {e}")
            raise HTTPException(status_code=504, detail="Location search timed out. Please try again.")
        except httpx.HTTPStatusError as e:
            logger.error(f"Photon API HTTP error for query '{q}': Status {e.response.status_code}, {e}")
            raise HTTPException(status_code=502, detail=f"Location search service returned error: {e.response.status_code}")
        except httpx.ConnectError as e:
            logger.error(f"Photon API connection error for query '{q}': {e}")
            raise HTTPException(status_code=502, detail="Cannot connect to location search service. Check internet connection.")
        except httpx.RequestError as e:
            logger.error(f"Photon API request error for query '{q}': {e}")
            raise HTTPException(status_code=502, detail=f"Location search request failed: {str(e)}")
        
        # Format the results
        locations = []
        for feature in data.get("features", []):
            props = feature.get("properties", {})
            coords = feature.get("geometry", {}).get("coordinates", [])
            
            if len(coords) >= 2:
                # Build display name
                name_parts = []
                city = props.get("city") or props.get("name")
                state = props.get("state")
                country = props.get("country")
                
                if city:
                    name_parts.append(city)
                if state and state != city:
                    name_parts.append(state)
                if country:
                    name_parts.append(country)
                
                display_name = ", ".join(name_parts)
                
                # Generate a unique ID based on coordinates
                location_id = f"loc_{abs(hash(f'{coords[1]},{coords[0]}'))}".replace("-", "")[:16]
                
                locations.append({
                    "id": location_id,
                    "name": city or props.get("name", "Unknown"),
                    "display_name": display_name,
                    "country": country or "",
                    "state": state or "",
                    "lat": coords[1],  # Photon returns [lon, lat]
                    "lon": coords[0]
                })
        
        logger.info(f"Returning {len(locations)} formatted locations")
        return {"locations": locations}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in location search for query '{q}': {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Failed to search locations: {str(e)}")

# Favorite Locations Endpoints
favorite_locations_router = APIRouter(prefix="/user/favorite-locations", tags=["favorite-locations"])

@favorite_locations_router.get("")
async def get_favorite_locations(user: dict = Depends(get_current_user)):
    """Get user's favorite locations"""
    try:
        user_data = await db.users.find_one(
            {"user_id": user["user_id"]},
            {"_id": 0, "favorite_locations": 1}
        )
        
        return {"favorites": user_data.get("favorite_locations", [])}
    except Exception as e:
        logger.error(f"Error fetching favorite locations: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch favorite locations")

@favorite_locations_router.post("")
async def add_favorite_location(
    location: FavoriteLocation,
    user: dict = Depends(get_current_user)
):
    """Add a location to user's favorites"""
    try:
        # Check if location already exists in favorites
        existing = await db.users.find_one({
            "user_id": user["user_id"],
            "favorite_locations.id": location.id
        })
        
        if existing:
            return {"message": "Location already in favorites"}
        
        # Add timestamp
        location_data = location.model_dump()
        location_data["added_at"] = datetime.now(timezone.utc).isoformat()
        
        # Initialize favorite_locations array if it doesn't exist
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$setOnInsert": {"favorite_locations": []}},
            upsert=False
        )
        
        # Add to favorites
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$push": {"favorite_locations": location_data}}
        )
        
        logger.info(f"Added favorite location {location.name} for user {user['user_id']}")
        return {"message": "Location added to favorites", "location": location_data}
    
    except Exception as e:
        logger.error(f"Error adding favorite location: {e}")
        raise HTTPException(status_code=500, detail="Failed to add favorite location")

@favorite_locations_router.delete("/{location_id}")
async def remove_favorite_location(
    location_id: str,
    user: dict = Depends(get_current_user)
):
    """Remove a location from user's favorites"""
    try:
        result = await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$pull": {"favorite_locations": {"id": location_id}}}
        )
        
        if result.modified_count == 0:
            raise HTTPException(status_code=404, detail="Favorite location not found")
        
        logger.info(f"Removed favorite location {location_id} for user {user['user_id']}")
        return {"message": "Location removed from favorites"}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error removing favorite location: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove favorite location")



# ========================
# INCLUDE ROUTERS
# ========================

api_router.include_router(auth_router)
api_router.include_router(trips_router)
api_router.include_router(expenses_router)
api_router.include_router(refunds_router)
api_router.include_router(settlements_router)
api_router.include_router(planner_router)
api_router.include_router(admin_router)
api_router.include_router(user_plans_router)
api_router.include_router(locations_router)
api_router.include_router(favorite_locations_router)

@api_router.get("/")
async def root():
    return {"message": "EZ Trip API"}

app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()