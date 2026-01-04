# Frontend Overview - StockSim

## Tech Stack
- **Framework:** Next.js 16+ (App Router)
- **Styling:** Tailwind CSS v4
- **State/Data:** React Hooks + Axios + Context API
- **Icons:** Lucide React
- **Charts:** Chart.js, Recharts
- **Language:** TypeScript

## Folder Structure

```
frontend/
├── app/
│   ├── globals.css         # Global styles & Tailwind theme
│   ├── layout.tsx          # Root layout with Navbar & CurrencyProvider
│   ├── page.tsx            # Start Session / Landing Page
│   ├── dashboard/
│   │   └── page.tsx        # Main Simulation Dashboard (Holdings, Allocation, Time Travel)
│   └── market/
│       ├── page.tsx        # Market Browser (Search & Filter assets)
│       └── [symbol]/
│           └── page.tsx    # Asset Details & Trading (Price Charts)
├── components/
│   ├── Button.tsx          # Reusable Button
│   ├── Input.tsx           # Reusable Input Field
│   ├── Card.tsx            # Content Container
│   ├── Navbar.tsx          # App Header
│   ├── CurrencySelector.tsx# Global currency switcher
│   └── ResetButton.tsx     # System reset trigger
├── context/
│   └── CurrencyContext.tsx # Global currency state and formatting logic
└── lib/
    └── api.ts              # Axios instance configuration
```

## Key Features

1.  **Session Initialization:** Users choose a past start date and monthly investment amount to begin their journey.
2.  **Simulation Dashboard:**
    *   **Real-time Net Worth:** Calculated based on historical prices at the current simulation date.
    *   **Holdings Table:** Detailed breakdown of investments with P&L tracking.
    *   **Allocation Chart:** Visual representation of portfolio distribution using Chart.js.
    *   **Time Travel:** Advance time by 1 month, 6 months, 1 year, or jump to a specific date.
3.  **Market Browser:** Browse and filter hundreds of S&P 500 assets, crypto, and commodities.
4.  **Asset Details & Trading:**
    *   **Historical Charts:** Interactive price history charts (Price vs. Time).
    *   **Buying:** Purchase assets using current session date and wallet balance.
5.  **Multi-Currency Support:** View all values in USD, EUR, GBP, JPY, etc., with live exchange rates.

## API Integration
The frontend communicates with the backend (default: `http://localhost:8000`) using `axios`.

- **Simulation:** `POST /simulation/start`, `POST /simulation/forward`, `GET /simulation/status`
- **Market:** `GET /assets`, `GET /price`, `GET /price/history`
- **Portfolio:** `POST /portfolio/buy`, `GET /portfolio/{id}`
- **System:** `GET /currencies`, `POST /reset`

## How to Run

1.  **Install Dependencies:**
    ```bash
    cd frontend
    npm install
    ```

2.  **Start Dev Server:**
    ```bash
    npm run dev
    ```

3.  Access at `http://localhost:3000`.

## Future Improvements (Not in Phase 1)
- Selling assets.
- Real-time stock price lookup/charts.
- detailed portfolio breakdown.
- User authentication (current implementation uses basic user creation).
- Dark mode toggle.
