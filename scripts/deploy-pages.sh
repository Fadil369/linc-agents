#!/bin/bash

echo "🚀 Deploying BrainSAIT LINC to Cloudflare Pages"

# Exit on any error
set -e

# Check if wrangler is installed
if ! command -v wrangler &> /dev/null; then
    echo "❌ Wrangler CLI not found. Installing..."
    npm install -g wrangler
fi

# Check if we're authenticated
if ! wrangler whoami &> /dev/null; then
    echo "⚠️  Please authenticate with Cloudflare first:"
    echo "   wrangler login"
    exit 1
fi

# Build the project
echo "🔨 Building project..."
npm run build

# Copy Pages configuration
echo "📋 Copying Pages configuration..."
cp infra/cloudflare-pages/_redirects dist/web/
cp infra/cloudflare-pages/pages-config.json dist/web/

# Deploy to Pages
echo "🌐 Deploying to Cloudflare Pages..."
wrangler pages deploy dist/web/ --project-name brainsait-linc

echo "✅ Deployment complete!"
echo "🔗 Your site will be available at: https://brainsait-linc.pages.dev"