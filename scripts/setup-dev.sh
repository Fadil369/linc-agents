#!/bin/bash

echo "🧠 Setting up BrainSAIT LINC Development Environment"

# Create necessary directories
mkdir -p data/temp data/uploads data/exports logs/agents logs/system models

# Set up database
echo "📊 Setting up database..."
docker-compose -f docker-compose.dev.yml up -d postgres redis

# Wait for services
echo "⏳ Waiting for services to be ready..."
sleep 10

# Build CSS
echo "🎨 Building CSS..."
npx tailwindcss -i ./ui/web/css/main.css -o ./ui/web/css/dist.css --watch &

echo "✅ Development environment ready!"
echo "🚀 Start with: docker-compose -f docker-compose.dev.yml up"
