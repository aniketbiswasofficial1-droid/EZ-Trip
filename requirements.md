# SplitEase - Trip Expense Splitting App

## Original Problem Statement
Create a responsive web-application which is a alternative to Splitwise, where a trip expense is easily calculated. If one or multiple person pays for the whole group or some specific people for a specific expense, can be added. It can also take into account of refunds of a specific bill and can distribute accordingly. It should have Gmail login and people can access it by logging in from their Gmail or account. It should have modern design. If it scales, I should easily be able to integrate ads in it.

## User Requirements
- Emergent-managed Google Auth (privacy-focused)
- Refunds option on each bill with clear indication
- Multiple currency support (13+ currencies)
- Native ad slots that blend with design
- Dark mode design

## Architecture

### Backend (FastAPI + MongoDB)
- **Auth Routes**: `/api/auth/session`, `/api/auth/me`, `/api/auth/logout`
- **Trip Routes**: CRUD for trips, member management, balances, settlements
- **Expense Routes**: Create/list/delete expenses with multi-payer and custom splits
- **Refund Routes**: Create/list/delete refunds linked to expenses
- **Currencies**: List of 13 supported currencies

### Frontend (React + Tailwind + Shadcn)
- **Landing Page**: Hero section, features, Google OAuth login
- **Dashboard**: Trip list, balance overview, create trip modal
- **Trip Detail**: Expenses tab, balances tab, settlements tab
- **Modals**: Add expense, add refund, add member

### Database Collections
- `users`: User profiles with user_id, email, name, picture
- `user_sessions`: Session tokens with expiry
- `trips`: Trip details with members array
- `expenses`: Expense records with payers and splits arrays
- `refunds`: Refund records linked to expenses

## Completed Features
- [x] Google OAuth authentication (Emergent-managed)
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

## Next Action Items
1. **Currency Conversion**: Add real-time exchange rates for multi-currency trips
2. **Expense Categories**: Add icons and filtering by category
3. **Export/Share**: Export trip summary as PDF or share link
4. **Notifications**: Email notifications for new expenses
5. **Mobile App**: React Native version for mobile

## Tech Stack
- Frontend: React 19, Tailwind CSS, Shadcn/UI, Framer Motion
- Backend: FastAPI, Motor (async MongoDB)
- Database: MongoDB
- Auth: Emergent-managed Google OAuth
- Fonts: Syne (headings), Manrope (body)
