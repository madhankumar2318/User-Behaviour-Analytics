#!/bin/bash

# Deployment script for production

echo "🚀 Starting deployment..."

# Stop existing containers
echo "📦 Stopping existing containers..."
docker-compose down

# Pull latest changes (if using git)
# git pull origin main

# Build new images
echo "🔨 Building Docker images..."
docker-compose build --no-cache

# Start containers
echo "▶️  Starting containers..."
docker-compose up -d

# Wait for services to be healthy
echo "⏳ Waiting for services to be healthy..."
sleep 10

# Check health
echo "🏥 Checking service health..."
docker-compose ps

# Run database migrations if needed
echo "📊 Running database migrations..."
docker-compose exec backend python migrate_database.py

echo "✅ Deployment complete!"
echo "🌐 Frontend: http://localhost"
echo "🔧 Backend API: http://localhost:5000"
echo "📚 API Docs: http://localhost:5000/api/docs"
