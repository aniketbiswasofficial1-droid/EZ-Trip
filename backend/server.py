from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, ConfigDict
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, timedelta
import httpx

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app
app = FastAPI()

# Create routers
api_router = APIRouter(prefix="/api")
auth_router = APIRouter(prefix="/auth")
trips_router = APIRouter(prefix="/trips")
expenses_router = APIRouter(prefix="/expenses")
refunds_router = APIRouter(prefix="/refunds")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ========================
# PYDANTIC MODELS
# ========================

class UserBase(BaseModel):
    model_config = ConfigDict(extra="ignore")
    user_id: str
    email: str
    name: str
    picture: Optional[str] = None
    default_currency: str = "USD"
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserUpdate(BaseModel):
    default_currency: Optional[str] = None

class TripCreate(BaseModel):
    name: str
    description: Optional[str] = None
    currency: str = "USD"
    cover_image: Optional[str] = None

class TripMember(BaseModel):
    user_id: str
    name: str
    email: str
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
    email: str
    name: str

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

@auth_router.post("/session")
async def create_session(request: Request, response: Response):
    """Exchange session_id for session_token"""
    body = await request.json()
    session_id = body.get("session_id")
    
    if not session_id:
        raise HTTPException(status_code=400, detail="session_id required")
    
    # Call Emergent auth to get user data
    async with httpx.AsyncClient() as client_http:
        auth_response = await client_http.get(
            "https://demobackend.emergentagent.com/auth/v1/env/oauth/session-data",
            headers={"X-Session-ID": session_id}
        )
        
        if auth_response.status_code != 200:
            raise HTTPException(status_code=401, detail="Invalid session_id")
        
        user_data = auth_response.json()
    
    # Check if user exists
    existing_user = await db.users.find_one(
        {"email": user_data["email"]},
        {"_id": 0}
    )
    
    if existing_user:
        user_id = existing_user["user_id"]
        # Update user info
        await db.users.update_one(
            {"user_id": user_id},
            {"$set": {
                "name": user_data["name"],
                "picture": user_data.get("picture")
            }}
        )
    else:
        # Create new user
        user_id = f"user_{uuid.uuid4().hex[:12]}"
        new_user = {
            "user_id": user_id,
            "email": user_data["email"],
            "name": user_data["name"],
            "picture": user_data.get("picture"),
            "default_currency": "USD",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
        await db.users.insert_one(new_user)
    
    # Create session
    session_token = user_data.get("session_token", f"session_{uuid.uuid4().hex}")
    expires_at = datetime.now(timezone.utc) + timedelta(days=7)
    
    await db.user_sessions.insert_one({
        "user_id": user_id,
        "session_token": session_token,
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now(timezone.utc).isoformat()
    })
    
    # Set cookie
    response.set_cookie(
        key="session_token",
        value=session_token,
        httponly=True,
        secure=True,
        samesite="none",
        path="/",
        max_age=7 * 24 * 60 * 60
    )
    
    user = await db.users.find_one({"user_id": user_id}, {"_id": 0})
    return user

@auth_router.get("/me")
async def get_me(user: dict = Depends(get_current_user)):
    """Get current authenticated user"""
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
        secure=True,
        samesite="none"
    )
    
    return {"message": "Logged out"}

@auth_router.put("/me")
async def update_user(
    update: UserUpdate,
    user: dict = Depends(get_current_user)
):
    """Update user preferences"""
    update_data = {k: v for k, v in update.model_dump().items() if v is not None}
    
    if update_data:
        await db.users.update_one(
            {"user_id": user["user_id"]},
            {"$set": update_data}
        )
    
    updated_user = await db.users.find_one(
        {"user_id": user["user_id"]},
        {"_id": 0}
    )
    return updated_user

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
        
        total_expenses = sum(e.get("total_amount", 0) for e in expenses)
        
        # Calculate user balance
        user_balance = 0
        for expense in expenses:
            # What user paid
            for payer in expense.get("payers", []):
                if payer["user_id"] == user["user_id"]:
                    user_balance += payer["amount"]
            
            # What user owes
            for split in expense.get("splits", []):
                if split["user_id"] == user["user_id"]:
                    user_balance -= split["amount"]
        
        # Account for refunds
        refunds = await db.refunds.find(
            {"trip_id": trip["trip_id"]},
            {"_id": 0}
        ).to_list(1000)
        
        for refund in refunds:
            if user["user_id"] in refund.get("refunded_to", []):
                per_person = refund["amount"] / len(refund["refunded_to"])
                user_balance += per_person
        
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
    
    total_expenses = sum(e.get("total_amount", 0) for e in expenses)
    
    user_balance = 0
    for expense in expenses:
        for payer in expense.get("payers", []):
            if payer["user_id"] == user["user_id"]:
                user_balance += payer["amount"]
        for split in expense.get("splits", []):
            if split["user_id"] == user["user_id"]:
                user_balance -= split["amount"]
    
    refunds = await db.refunds.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).to_list(1000)
    
    for refund in refunds:
        if user["user_id"] in refund.get("refunded_to", []):
            per_person = refund["amount"] / len(refund["refunded_to"])
            user_balance += per_person
    
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
    trip = await db.trips.find_one(
        {"trip_id": trip_id, "members.user_id": user["user_id"]},
        {"_id": 0}
    )
    
    if not trip:
        raise HTTPException(status_code=404, detail="Trip not found")
    
    # Check if member already exists
    existing_member = next(
        (m for m in trip["members"] if m["email"] == member.email),
        None
    )
    if existing_member:
        raise HTTPException(status_code=400, detail="Member already in trip")
    
    # Check if user exists in system
    existing_user = await db.users.find_one(
        {"email": member.email},
        {"_id": 0}
    )
    
    if existing_user:
        new_member = {
            "user_id": existing_user["user_id"],
            "name": existing_user["name"],
            "email": existing_user["email"],
            "picture": existing_user.get("picture")
        }
    else:
        # Create placeholder user_id for non-registered users
        new_member = {
            "user_id": f"guest_{uuid.uuid4().hex[:8]}",
            "name": member.name,
            "email": member.email,
            "picture": None
        }
    
    await db.trips.update_one(
        {"trip_id": trip_id},
        {"$push": {"members": new_member}}
    )
    
    return {"message": "Member added", "member": new_member}

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
    
    for expense in expenses:
        for payer in expense.get("payers", []):
            if payer["user_id"] in balances:
                balances[payer["user_id"]] += payer["amount"]
        
        for split in expense.get("splits", []):
            if split["user_id"] in balances:
                balances[split["user_id"]] -= split["amount"]
    
    # Account for refunds
    refunds = await db.refunds.find(
        {"trip_id": trip_id},
        {"_id": 0}
    ).to_list(1000)
    
    for refund in refunds:
        per_person = refund["amount"] / len(refund["refunded_to"])
        for uid in refund["refunded_to"]:
            if uid in balances:
                balances[uid] += per_person
    
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

# ========================
# CURRENCIES
# ========================

SUPPORTED_CURRENCIES = [
    {"code": "USD", "symbol": "$", "name": "US Dollar"},
    {"code": "EUR", "symbol": "\u20ac", "name": "Euro"},
    {"code": "GBP", "symbol": "\u00a3", "name": "British Pound"},
    {"code": "INR", "symbol": "\u20b9", "name": "Indian Rupee"},
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
# INCLUDE ROUTERS
# ========================

api_router.include_router(auth_router)
api_router.include_router(trips_router)
api_router.include_router(expenses_router)
api_router.include_router(refunds_router)

@api_router.get("/")
async def root():
    return {"message": "SplitEase API"}

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
