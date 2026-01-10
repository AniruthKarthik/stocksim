# Deploying StockSim with Neon (Database) and Render (App)

This guide walks you through deploying your application completely for free using **Neon** for the database and **Render** for hosting both the backend and frontend.

## 1. Set up Neon Database

1.  **Create Account:** Go to [neon.tech](https://neon.tech) and sign up.
2.  **Create Project:** Click **New Project**. Name it `stocksim-db`.
3.  **Get Connection String:**
    *   Once created, you will see a **Connection String** panel.
    *   Ensure "Pooled connection" is checked (optional but recommended).
    *   Your string: `postgresql://neondb_owner:npg_ZBc8y6MCRkqi@ep-old-dew-a163gqj8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require`
4.  **Initialize Database:**
    *   Go to the **SQL Editor** in the Neon dashboard.
    *   Copy the contents of `backend/portfolio_schema.sql` (from your local project).
    *   Paste it into the SQL Editor and run it to create your tables.

## 2. Deploy Backend (Render)

1.  **Create Web Service:**
    *   Log in to [Render](https://dashboard.render.com).
    *   Click **New +** -> **Web Service**.
    *   Connect your GitHub repository.
2.  **Configuration:**
    *   **Name:** `stocksim-backend`
    *   **Runtime:** Python 3
    *   **Root Directory:** `.` (default)
    *   **Build Command:** `pip install -r backend/requirements.txt`
    *   **Start Command:** `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
3.  **Environment Variables:**
    *   Add a single key:
        *   **Key:** `DATABASE_URL`
        *   **Value:** Paste your Neon connection string from Step 1.
    *   Add:
        *   **Key:** `ALLOWED_ORIGINS`
        *   **Value:** `*`
    *   Add:
        *   **Key:** `PYTHON_VERSION`
        *   **Value:** `3.11.0`
4.  **Deploy:** Click **Create Web Service**. Copy the URL when finished.

## 3. Deploy Frontend (Render)

1.  **Create Web Service:**
    *   Click **New +** -> **Web Service** again.
    *   Connect the **same** GitHub repository.
2.  **Configuration:**
    *   **Name:** `stocksim-frontend`
    *   **Runtime:** Node
    *   **Root Directory:** `frontend`
    *   **Build Command:** `npm install && npm run build`
    *   **Start Command:** `npm start`
3.  **Environment Variables:**
    *   Add:
        *   **Key:** `NEXT_PUBLIC_API_URL`
        *   **Value:** `https://stocksim-log.onrender.com`
        *   *Note:* No trailing slash `/` at the end.
4.  **Deploy:** Click **Create Web Service**.

## 4. Verification

1.  Open your Frontend URL.
2.  The app should work perfectly, connecting to your Python backend on Render and your PostgreSQL database on Neon.
