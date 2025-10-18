#!/bin/bash

# Run the Polylytics Security Platform locally

echo "Starting Polylytics Security Platform..."

# Set environment variables
export ENVIRONMENT=development
export DATABASE_URL=postgresql://user:password@localhost:5432/polylytics
export REDIS_URL=redis://localhost:6379/0
export JWT_SECRET=your-super-secret-jwt-key-change-in-production

# Start the application
cd polylytics
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload