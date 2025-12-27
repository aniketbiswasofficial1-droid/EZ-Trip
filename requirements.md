# EZ Trip - Trip Expense Splitting App

## Original Problem Statement
Create a responsive web-application which is a alternative to Splitwise, where a trip expense is easily calculated. If one or multiple person pays for the whole group or some specific people for a specific expense, can be added. It can also take into account of refunds of a specific bill and can distribute accordingly. It should have Gmail login and people can access it by logging in from their Gmail or account. It should have modern design. If it scales, I should easily be able to integrate ads in it.

## User Requirements
- Google OAuth authentication
- Refunds option on each bill with clear indication
- Multiple currency support (13+ currencies)
- Native ad slots that blend with design
- Dark mode design
- **AI Trip Planner** with weather, costs, and itinerary generation

## Architecture

### Backend (FastAPI + MongoDB)
- **Auth Routes**: `/api/auth/session`, `/api/auth/me`, `/api/auth/logout`
- **Trip Routes**: CRUD for trips, member management, balances, settlements
- **Expense Routes**: Create/list/delete expenses with multi-payer and custom splits
- **Refund Routes**: Create/list/delete refunds linked to expenses
- **Planner Routes**: `/api/planner/generate`, `/api/planner/save`, `/api/planner/saved`
- **Currencies**: List of 13 supported currencies

### AI Trip Planner Service
- **LLM**: OpenAI GPT-4o
- **Weather API**: Open-Meteo (free, no API key needed)
- **Features**:
  - Day-by-day itinerary with time slots
  - Weather forecast integration
  - Cost breakdown (flights, hotels, food, activities)
  - Per-person and group total estimates
  - Travel tips, packing suggestions, local customs
  - Emergency contacts

### Frontend (React + Tailwind + Shadcn)
- **Landing Page**: Hero section, features, Google OAuth login
- **Dashboard**: Trip list, balance overview, AI Planner card, create trip modal
- **Trip Detail**: Expenses tab, balances tab, settlements tab
- **AI Trip Planner**: Full planning interface with preferences and results
- **Modals**: Add expense, add refund, add member

### Database Collections
- `users`: User profiles with user_id, email, name, picture
- `user_sessions`: Session tokens with expiry
- `trips`: Trip details with members array
- `expenses`: Expense records with payers and splits arrays
- `refunds`: Refund records linked to expenses
- `saved_plans`: AI-generated trip plans
- `settings`: App settings including LLM API key

## Completed Features
- [x] Google OAuth authentication
- [x] Create/delete trips with cover images
- [x] Add/remove trip members
- [x] Multi-currency support (13 currencies)
- [x] Create expenses with multiple payers
- [x] Custom split options (equal or manual)
- [x] Refund tracking with clear indication
- [x] Balance calculation per member
- [x] Settlement suggestions (who pays whom)
- [x] Dark mode UI with neon accents
- [x] Native ad slots (styled like content cards)
- [x] Responsive design
- [x] **AI Trip Planner with GPT-4o**
- [x] **Weather integration (Open-Meteo)**
- [x] **Cost estimation and breakdown**
- [x] **Day-by-day itinerary generation**
- [x] **Save and view trip plans**
- [x] **Admin LLM key management**
- [x] **Full Admin Panel**
  - Dashboard with analytics (users, trips, expenses, AI plans)
  - User management (view, make admin, enable/disable)
  - Trip management (view all, delete)
  - Feature toggles (enable/disable any button or feature)
  - Content management (edit all site text)
  - Settings (LLM provider/model, maintenance mode, registration)

## Next Action Items
1. **Real-time currency conversion**: Add exchange rate API for multi-currency trips
2. **Export trip plans**: PDF export for itineraries
3. **Share trip plans**: Shareable links for group planning
4. **Push notifications**: Notify when expenses are added

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Framer Motion
- Backend: FastAPI, Motor (async MongoDB)
- Database: MongoDB
- Auth: Google OAuth
- AI: OpenAI GPT-4o
- Weather: Open-Meteo API
- Fonts: Montserrat
