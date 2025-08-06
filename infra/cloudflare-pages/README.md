# Cloudflare Pages Integration

This directory contains configuration for Cloudflare Pages deployment only.

## Important Note

**Cloudflare Workers integration has been intentionally excluded** from this project. 
Only Cloudflare Pages is supported for static site hosting and serverless functions.

## Configuration

### Environment Variables
- `CLOUDFLARE_PAGES_TOKEN`: API token for Cloudflare Pages deployment
- Configure in `.env` for development and production environments

### Deployment Strategy
- Static web interfaces built with Vite
- Deployed to Cloudflare Pages for global CDN distribution
- Serverless functions via Pages Functions (not Workers)

### Files Structure
- `pages-config.json` - Pages-specific configuration
- `_redirects` - URL redirects and rewrites
- `functions/` - Pages Functions (serverless endpoints)

## Why Pages Only?

This project uses Cloudflare Pages instead of Workers for:
1. Simplified deployment pipeline
2. Integrated static site hosting
3. Built-in CI/CD with Git integration
4. Cost-effective for healthcare application hosting
5. Better integration with existing web frameworks

## Deployment Commands

```bash
# Install Wrangler CLI for Pages
npm install -g wrangler

# Deploy to Pages
wrangler pages deploy dist/

# Configure environment variables
wrangler pages secret put CLOUDFLARE_PAGES_TOKEN
```