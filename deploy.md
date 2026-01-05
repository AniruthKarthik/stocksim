# Permanent Free Full-Stack Deployment Guide

This guide details how to set up a **permanent, cost-free** deployment for your application.

- **Database:** [Supabase](https://supabase.com) (PostgreSQL). Unlike Render's free DB, this **does not expire**.
- **Backend:** [Render](https://render.com) (Python FastAPI). The free web service spins down on inactivity but remains free indefinitely.
- **Frontend:** [Vercel](https://vercel.com) (Next.js). Optimized hosting for Next.js.

---

## Part 1: Permanent Database with Supabase

1.  **Create a Project**:
    *   Sign up at [supabase.com](https://supabase.com).
    *   Click **New Project**.
    *   Enter a **Name** (e.g., `stocksim-db`) and a strong **Database Password** (save this!).
    *   Select a **Region** close to you.
    *   Click **Create new project**.

2.  **Get Connection Details**:
    *   Once the project is created, go to **Project Settings** (gear icon) -> **Database**.
    *   Under **Connection Parameters**, note your:
        *   **Host**
        *   **Database Name** (usually `postgres`)
        *   **User** (usually `postgres`)
        *   **Port** (5432)
    *   *Alternatively*, look for the **Connection String** (URI) and select **URI**. It will look like: `postgresql://postgres.[ref]:[password]@[host]:5432/postgres`.

3.  **Initialize the Database**:
    *   In the Supabase dashboard, go to the **SQL Editor** (terminal icon on the left).
    *   Click **New Query**.
    *   Copy the content of `stocksim_schema.sql` (from your project root) and paste it into the query window.
    *   Click **Run**.
    *   Clear the editor, then copy/paste the content of `backend/portfolio_schema.sql` and click **Run**.

---

## Part 2: Backend Deployment on Render

1.  **Create Web Service**:
    *   Log in to [Render](https://render.com).
    *   Click **New +** -> **Web Service**.
    *   Connect your GitHub repository.

2.  **Configure**:
    *   **Name**: `stocksim-backend`
    *   **Runtime**: **Python 3**
    *   **Build Command**: `pip install -r requirements.txt`
    *   **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port 8000`

3.  **Environment Variables**:
    *   Scroll down to **Environment Variables** and add the keys using your **Supabase** credentials:
        *   `DB_HOST`: Your Supabase Host (e.g., `db.xyz.supabase.co`)
        *   `DB_NAME`: `postgres`
        *   `DB_USER`: `postgres`
        *   `DB_PASSWORD`: The password you set in step 1.
    *   *Note:* Supabase uses port 5432 by default, which is standard.

4.  **Deploy**:
    *   Select **Free** plan.
    *   Click **Create Web Service**.
    *   Wait for the deployment to finish. Copy the **onrender.com** URL provided (e.g., `https://stocksim-backend.onrender.com`).

---

## Part 3: Frontend Deployment on Vercel

1.  **Import Project**:
    *   Log in to [Vercel](https://vercel.com).
    *   Click **Add New...** -> **Project**.
    *   Import your Git repository.

2.  **Configure**:
    *   **Framework Preset**: Next.js
    *   **Root Directory**: Click "Edit" and select `frontend`.

3.  **Environment Variables**:
    *   Add a new variable:
        *   **Name**: `NEXT_PUBLIC_API_URL`
        *   **Value**: Your Render Backend URL (from Part 2, e.g., `https://stocksim-backend.onrender.com`).
        *   *Important:* Remove any trailing slash `/` from the URL.

4.  **Deploy**:
    *   Click **Deploy**.

---

## Part 4: Final Connection

1.  **Allow Frontend Access (CORS)**:
    *   Once Vercel deploys, copy your new frontend URL (e.g., `https://stocksim-frontend.vercel.app`).
    *   In your local code, open `backend/main.py`.
    *   Update the `origins` list to include your specific Vercel URL:
        ```python
        origins = [
            "http://localhost:3000",
            "https://stocksim-frontend.vercel.app" # Your actual Vercel URL
        ]
        ```
    *   **Commit and Push** this change to GitHub. Render will automatically redeploy the backend.

2.  **Populate Data (Optional)**:
    *   To load initial stock data into your Supabase DB, you can run the scripts locally.
    *   Create a `.env` file in your `backend/` folder with your Supabase credentials.
    *   Run `python scripts/download_all_data.py` and `python scripts/load_local_csvs.py`.