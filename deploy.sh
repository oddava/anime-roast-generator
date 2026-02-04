#!/bin/bash

# Anime Roast Generator - Production Deployment Script
# Usage: ./deploy.sh

set -e

echo "🚀 Starting deployment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if .env.prod exists
if [ ! -f .env.prod ]; then
    echo -e "${RED}Error: .env.prod file not found!${NC}"
    echo "Please create .env.prod from .env.prod.example"
    exit 1
fi

# Load environment variables
export $(grep -v '^#' .env.prod | xargs)

# Check required variables
if [ -z "$DOMAIN" ]; then
    echo -e "${RED}Error: DOMAIN is not set in .env.prod${NC}"
    exit 1
fi

if [ -z "$ACME_EMAIL" ]; then
    echo -e "${RED}Error: ACME_EMAIL is not set in .env.prod${NC}"
    exit 1
fi

# Pull latest changes
echo -e "${YELLOW}📥 Pulling latest changes...${NC}"
git pull origin main

# Stop existing containers
echo -e "${YELLOW}🛑 Stopping existing containers...${NC}"
docker-compose -f docker-compose.prod.yml down

# Remove old images to free space
echo -e "${YELLOW}🧹 Cleaning up old images...${NC}"
docker system prune -f

# Build and start containers
echo -e "${YELLOW}🔨 Building and starting containers...${NC}"
docker-compose -f docker-compose.prod.yml up --build -d

# Wait for services to be ready
echo -e "${YELLOW}⏳ Waiting for services to be ready...${NC}"
sleep 10

# Check health
echo -e "${YELLOW}🏥 Checking service health...${NC}"
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Backend is healthy!${NC}"
else
    echo -e "${RED}❌ Backend health check failed${NC}"
    docker-compose -f docker-compose.prod.yml logs backend
    exit 1
fi

# Display status
echo -e "${GREEN}✅ Deployment completed successfully!${NC}"
echo ""
echo -e "${GREEN}🌐 Application is running at: https://${DOMAIN}${NC}"
echo ""
echo -e "${YELLOW}📊 Container status:${NC}"
docker-compose -f docker-compose.prod.yml ps

echo ""
echo -e "${YELLOW}📋 Useful commands:${NC}"
echo "  View logs:          docker-compose -f docker-compose.prod.yml logs -f"
echo "  Restart:            docker-compose -f docker-compose.prod.yml restart"
echo "  Stop:               docker-compose -f docker-compose.prod.yml down"
echo "  Update:             ./deploy.sh"
