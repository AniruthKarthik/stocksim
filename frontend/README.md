# StockSim Frontend

This is the Next.js frontend for the StockSim application.

## Setup

1.  **Install Dependencies:**
    ```bash
    npm install
    ```

2.  **Environment Variables:**
    Create a `.env.local` file. See `envex.md` (in this folder) for details.
    ```bash
    NEXT_PUBLIC_API_URL=http://localhost:8000
    ```

3.  **Run Development Server:**
    ```bash
    npm run dev
    ```

## Features
- **Dashboard:** View portfolio performance, net worth, and holdings.
- **Market:** Browse assets and view historical price charts.
- **Time Travel:** Advance simulation time to see how investments perform.
- **Currency Support:** View portfolio in USD, INR, EUR, etc.