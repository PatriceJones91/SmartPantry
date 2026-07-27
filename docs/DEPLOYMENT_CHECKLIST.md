# Deployment Checklist

## Backend

1. Copy `backend/.env.example` to `backend/.env` and enter Supabase values.
2. Set `APP_ENV=production` so internal exception details are hidden from API responses.
3. Set `ALLOWED_ORIGINS` to the exact production frontend origin(s).
4. Keep `SUPABASE_SERVICE_ROLE_KEY` server-side only.
5. Install `backend/requirements.txt` and start FastAPI from the backend folder.
6. Verify `/api/health`, `/api/recommendations/contract`, and a test recommendation request.

## Frontend

1. Copy `frontend/.env.example` to `frontend/.env`.
2. Set `VITE_API_URL` to the deployed backend `/api` URL.
3. Run `npm ci` and `npm run build`.
4. Test direct navigation, refresh behavior, login, pantry entry, recommendations, history, and admin access.

## Database

- Apply `database/schema.sql` and any migration files in date order.
- Confirm participant rows are separated by `user_id`.
- Confirm recommendation sessions, results, actions, and feedback tables accept writes.
- Review Supabase Row Level Security before participant launch.

## Final participant-study checks

- Use neutral participant-facing wording.
- Remove test accounts and sample study records from production.
- Confirm survey wording and consent materials match the approved study protocol.
- Export a backup before and after the study window.
