# Frontend Overview - StockSim

## Tech Stack
- **Framework:** Next.js 15+ (App Router)
- **Styling:** Tailwind CSS v4
- **State/Data:** React Hooks + Axios
- **Language:** TypeScript

## Folder Structure

```
frontend/
├── app/
│   ├── globals.css         # Global styles & Tailwind theme
│   ├── layout.tsx          # Root layout (Navbar wrapper)
│   ├── page.tsx            # Home page (Landing)
│   └── simulation/
│       ├── page.tsx        # Main Dashboard (View Status, Time Travel, Buy)
│       └── start/
│           └── page.tsx    # Start Simulation Form
├── components/
│   ├── Button.tsx          # Reusable Button
│   ├── Input.tsx           # Reusable Input Field
│   ├── Card.tsx            # Content Container
│   └── Navbar.tsx          # App Header
└── lib/
    └── api.ts              # Axios instance configuration
```

## Key Features

1.  **Landing Page:** Welcomes users and directs them to start or continue.
2.  **Simulation Setup:** Creates a user, a portfolio, and initializes the simulation session via a multi-step API flow.
3.  **Dashboard:**
    *   **Status Bar:** Shows current simulation date, cash, and total portfolio value.
    *   **Time Travel:** Advance simulation by 1 month, 6 months, etc.
    *   **Trading:** Buy stocks (MVP) using current simulation date.

## API Integration
The frontend communicates with the backend (default: `http://localhost:8000`) using `axios` from `@/lib/api`.

- **User Creation:** `POST /users`
- **Portfolio Creation:** `POST /portfolio/create`
- **Start Session:** `POST /simulation/start`
- **Simulation Control:** `POST /simulation/forward`, `GET /simulation/status`
- **Trading:** `POST /portfolio/buy`

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
