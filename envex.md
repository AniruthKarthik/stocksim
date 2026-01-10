# Environment Variables (.env)

Create a file named `.env` in this directory (Project Root).

## Required Variables

### Database Connection
**Option 1 (Recommended for Neon/Render):**
```bash
# Your actual Neon DB connection string
DATABASE_URL=postgresql://neondb_owner:npg_ZBc8y6MCRkqi@ep-old-dew-a163gqj8-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require
```

**Option 2 (Manual Credentials - Local Postgres):**
```bash
DB_HOST=localhost
DB_NAME=postgres
DB_USER=postgres
DB_PASSWORD=your_password
DB_PORT=5432
```

### Backend Configuration
```bash
# Comma-separated list of allowed frontend origins (CORS)
ALLOWED_ORIGINS=http://localhost:3000,https://stocksim-frontend.vercel.app
```
