#!/bin/bash

# Football Analytics - Development Setup Script
# This script sets up the development environment for the Football Analytics application

set -e

echo "🚀 Setting up Football Analytics Development Environment..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Docker is not installed. Please install Docker first.${NC}"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Docker Compose is not installed. Please install Docker Compose first.${NC}"
    exit 1
fi

# Create environment files if they don't exist
echo -e "${YELLOW}Setting up environment files...${NC}"

if [ ! -f "./backend/.env" ]; then
    cp "./backend/.env.example" "./backend/.env"
    echo -e "${GREEN}Created backend/.env from example${NC}"
fi

if [ ! -f "./frontend/.env" ]; then
    cp "./frontend/.env.example" "./frontend/.env"
    echo -e "${GREEN}Created frontend/.env from example${NC}"
fi

# Create Docker network if it doesn't exist
echo -e "${YELLOW}Setting up Docker network...${NC}"
docker network create football-network 2>/dev/null || true

# Build and start services
echo -e "${YELLOW}Building and starting services...${NC}"
docker-compose up -d --build

# Wait for services to be ready
echo -e "${YELLOW}Waiting for services to be ready...${NC}"
sleep 30

# Run database migrations
echo -e "${YELLOW}Running database migrations...${NC}"
docker-compose exec backend python -m alembic upgrade head

# Check service health
echo -e "${YELLOW}Checking service health...${NC}"

# Check backend health
backend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/health || echo "000")
if [ "$backend_health" = "200" ]; then
    echo -e "${GREEN}✅ Backend service is healthy${NC}"
else
    echo -e "${RED}❌ Backend service is not responding${NC}"
fi

# Check frontend (may take longer to start)
sleep 10
frontend_health=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 || echo "000")
if [ "$frontend_health" = "200" ]; then
    echo -e "${GREEN}✅ Frontend service is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend service may still be starting...${NC}"
fi

echo ""
echo -e "${GREEN}🎉 Football Analytics setup complete!${NC}"
echo ""
echo "📋 Services:"
echo "  • Backend API: http://localhost:8000"
echo "  • API Documentation: http://localhost:8000/docs"
echo "  • Frontend: http://localhost:3000"
echo "  • PostgreSQL: localhost:5432"
echo "  • Redis: localhost:6379"
echo ""
echo "🔧 Useful commands:"
echo "  • View logs: docker-compose logs -f"
echo "  • Stop services: docker-compose down"
echo "  • Restart services: docker-compose restart"
echo "  • Access backend shell: docker-compose exec backend bash"
echo ""
echo "📚 Next steps:"
echo "  1. Configure your API keys in backend/.env"
echo "  2. Visit http://localhost:3000 to access the application"
echo "  3. Check the API documentation at http://localhost:8000/docs"
echo ""