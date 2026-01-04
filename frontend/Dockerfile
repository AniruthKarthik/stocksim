
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

