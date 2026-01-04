-- Users table
CREATE TABLE IF NOT EXISTS users (
    id SERIAL PRIMARY KEY,
    username TEXT UNIQUE NOT NULL
);

-- Portfolios table
CREATE TABLE IF NOT EXISTS portfolios (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    currency_code TEXT DEFAULT 'USD',
    cash_balance NUMERIC DEFAULT 10000.00,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, name)
);

-- Transactions table
CREATE TABLE IF NOT EXISTS transactions (
    id SERIAL PRIMARY KEY,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    asset_id INTEGER REFERENCES assets(id),
    type TEXT CHECK (type IN ('BUY', 'SELL')),
    symbol TEXT NOT NULL,
    quantity NUMERIC NOT NULL,
    price_per_unit NUMERIC NOT NULL,
    date DATE NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Game Sessions table
CREATE TABLE IF NOT EXISTS game_sessions (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
    portfolio_id INTEGER REFERENCES portfolios(id) ON DELETE CASCADE,
    start_date DATE NOT NULL,
    sim_date DATE NOT NULL,
    monthly_salary NUMERIC DEFAULT 0,
    monthly_expenses NUMERIC DEFAULT 0,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(portfolio_id)
);

-- Currencies
CREATE TABLE IF NOT EXISTS currencies (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    symbol TEXT NOT NULL
);

-- Exchange Rates (Base is USD)
-- rate: How much of Currency you get for 1 USD.
CREATE TABLE IF NOT EXISTS exchange_rates (
    currency_code TEXT REFERENCES currencies(code) ON DELETE CASCADE,
    rate NUMERIC NOT NULL,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (currency_code)
);

-- Insert default currencies if not exist
INSERT INTO currencies (code, name, symbol) VALUES
('USD', 'United States Dollar', '$'),
('EUR', 'Euro', '€'),
('GBP', 'British Pound', '£'),
('JPY', 'Japanese Yen', '¥'),
('CAD', 'Canadian Dollar', 'C$'),
('AUD', 'Australian Dollar', 'A$'),
('INR', 'Indian Rupee', '₹')
ON CONFLICT DO NOTHING;

-- Insert default USD rate (always 1)
INSERT INTO exchange_rates (currency_code, rate, last_updated) VALUES
('USD', 1.0, CURRENT_TIMESTAMP)
ON CONFLICT (currency_code) DO UPDATE SET rate = 1.0;

