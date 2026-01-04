# Dockerization Guide for StockSim

This guide explains how to containerize the StockSim application (Frontend, Backend, and Database) using Docker and Docker Compose.

## Prerequisites

- [Docker](https://docs.docker.com/get-docker/) installed on your machine.
- [Docker Compose](https://docs.docker.com/compose/install/) (usually included with Docker Desktop/Engine).

## 1. Backend Dockerfile

Create a file named `Dockerfile` inside the `backend/` directory (`backend/Dockerfile`).

**Note:** This Dockerfile assumes the build context is the **project root** so it can access necessary files.

```dockerfile
# backend/Dockerfile
FROM python:3.9-slim

# Set working directory
WORKDIR /app

# Install system dependencies (needed for psycopg2)
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements from the root (since build context will be root)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire project into the container
COPY . .

# Expose the port FastAPI runs on
EXPOSE 8000

# Command to run the application
# We run from /app, so module path is backend.main
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 2. Frontend Dockerfile

Create a file named `Dockerfile` inside the `frontend/` directory (`frontend/Dockerfile`).

```dockerfile
# frontend/Dockerfile
FROM node:18-alpine

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./

# Install dependencies
RUN npm ci

# Copy the rest of the frontend code
COPY . .

# Build the Next.js application
# Note: NEXT_PUBLIC_API_URL is set at build time for client-side environment variables
ARG NEXT_PUBLIC_API_URL
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL

RUN npm run build

# Expose Next.js port
EXPOSE 3000

# Start the application
CMD ["npm", "start"]
```

## 3. Docker Compose Configuration

Create a `docker-compose.yml` file in the **project root** directory. This orchestrates the database, backend, and frontend.

```yaml
version: '3.8'

services:
  # Database Service (PostgreSQL)
  db:
    image: postgres:15-alpine
    container_name: stocksim_db
    environment:
      POSTGRES_USER: ${DB_USER:-admin}
      POSTGRES_PASSWORD: ${DB_PASSWORD:-password}
      POSTGRES_DB: ${DB_NAME:-stocksim}
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      # Initialize DB with schemas automatically
      - ./stocksim_schema.sql:/docker-entrypoint-initdb.d/01_stocksim_schema.sql
      - ./backend/portfolio_schema.sql:/docker-entrypoint-initdb.d/02_portfolio_schema.sql

  # Backend Service (FastAPI)
  backend:
    build:
      context: .
      dockerfile: backend/Dockerfile
    container_name: stocksim_backend
    depends_on:
      - db
    environment:
      DB_HOST: db
      DB_USER: ${DB_USER:-admin}
      DB_PASSWORD: ${DB_PASSWORD:-password}
      DB_NAME: ${DB_NAME:-stocksim}
    ports:
      - "8000:8000"
    volumes:
      - .:/app  # Optional: Mount for hot-reloading during dev

  # Frontend Service (Next.js)
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      args:
        # URL for the browser to access the API (client-side)
        NEXT_PUBLIC_API_URL: http://localhost:8000
    container_name: stocksim_frontend
    depends_on:
      - backend
    ports:
      - "3000:3000"
    environment:
      # URL for Server-Side Rendering (if needed)
      API_INTERNAL_URL: http://backend:8000

volumes:
  postgres_data:
```

## 4. How to Run

1.  **Create/Check Environment Variables**:
    You can create a `.env` file in the root directory if you want to override the defaults (though the `docker-compose.yml` has defaults).

    ```env
    DB_USER=admin
    DB_PASSWORD=password
    DB_NAME=stocksim
    ```

2.  **Build and Start**:
    Run the following command in the project root:

    ```bash
    docker-compose up --build
    ```

3.  **Access the Application**:
    -   Frontend: [http://localhost:3000](http://localhost:3000)
    -   Backend API Docs: [http://localhost:8000/docs](http://localhost:8000/docs)

4.  **Data Initialization (Optional)**:
    The database schemas are loaded automatically on the first run. If you need to populate initial stock data from CSVs, you can execute the loader script inside the running backend container:

    ```bash
    # Open a shell in the backend container
    docker exec -it stocksim_backend bash

    # Run the loader script
    python -m backend.db_load.load_csvs
    ```

## 5. Cleaning Up

To stop the containers and remove them:

```bash
docker-compose down
```

To stop and also remove the database volume (WARNING: deletes all data):

```bash
docker-compose down -v
```
