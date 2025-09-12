FROM node:18-alpine

WORKDIR /app

# Copy package files first for better caching
COPY frontend/package*.json ./
RUN npm ci

# Copy application code
COPY frontend/ .

# Expose port
EXPOSE 3000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

# Run the application in development mode
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]