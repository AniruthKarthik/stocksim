# Environment Variables (.env.local)

Create a file named `.env.local` in this directory (`frontend/`).

## Required Variables

### API Connection
This connects the frontend to your backend.

**For Local Development:**
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

**For Production (Render):**
```bash
# Your actual Render Backend URL
NEXT_PUBLIC_API_URL=https://stocksim-log.onrender.com
```
*Note: Do NOT include a trailing slash `/` at the end.*
