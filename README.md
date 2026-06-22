# Smart Pantry 2.0

Smart Pantry 2.0 is a separate React + FastAPI rebuild of the Smart Pantry prototype.

The current Streamlit version can stay as the Milestone 6 capstone submission. This folder is the next architecture direction: a React frontend, FastAPI backend, and Supabase database.

## Stack
- React
- Vite
- FastAPI
- Supabase/PostgreSQL
- Recharts
- Python

## Setup

### 1. Supabase
Open Supabase SQL Editor and run `database/schema.sql`.

### 2. Backend
```bash
cd backend
python -m venv venv
source venv/Scripts/activate
python -m pip install -r requirements.txt
cp .env.example .env
python -m uvicorn main:app --reload
```

Update `backend/.env` with your Supabase URL and key before running.

Backend API: `http://127.0.0.1:8000`
API docs: `http://127.0.0.1:8000/docs`

### 3. Frontend
Open a second terminal:

```bash
cd frontend
npm install
cp .env.example .env
npm run dev
```

React app: `http://localhost:5173`

## Demo Admin Login
username: admin
password: Admin123!

## Current Features
- Login/register
- Participant dashboard
- Pantry category pie chart
- Expiration alerts
- Pantry item entry
- Pre-study survey
- Post-study survey
- Meal recommendations
- Recommendation actions
- Recommendation history
- Admin dashboard
- Supabase database schema

Do not commit `.env` files or Supabase keys to GitHub.
