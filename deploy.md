# Deploying StockSim

This guide details how to deploy the full stack (Frontend + Backend + Database) using **Neon** and **Render**.

## 1. Database (Neon)
We use Neon for a serverless PostgreSQL database.

1.  **Create Project:** Sign up at [neon.tech](https://neon.tech) and create a project.
2.  **Get Connection String:** Copy the pooled connection string.
    *   Example: `postgresql://neondb_owner:npg_ZBc8y6MCRkqi@ep-old-dew-a163gqj8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
3.  **Initialize Schema:**
    *   Open Neon SQL Editor.
    *   Run the script from `setupneon.txt` (or `stocksim_schema.sql` + `backend/portfolio_schema.sql`).

## 2. Hosting (Render)
We use Render to host both the Python Backend and Next.js Frontend.

### Backend Service
- **Type:** Web Service
- **Runtime:** Python 3
- **Build:** `pip install -r backend/requirements.txt`
- **Start:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
- **Env Vars:**
    - `DATABASE_URL`: (Your Neon connection string)
    - `ALLOWED_ORIGINS`: `*`
    - `PYTHON_VERSION`: `3.11.0`

### Frontend Service
- **Type:** Web Service
- **Runtime:** Node
- **Build:** `npm install && npm run build`
- **Start:** `npm start`
- **Root Directory:** `frontend`
- **Env Vars:**
    - `NEXT_PUBLIC_API_URL`: `https://stocksim-log.onrender.com` (Your backend URL)

## 3. Post-Deployment
- Ensure the Frontend can talk to the Backend (CORS).
- If you see "Network Error", check `NEXT_PUBLIC_API_URL` and `ALLOWED_ORIGINS`.
