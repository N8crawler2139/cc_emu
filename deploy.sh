#!/bin/bash

# FF6 AI Player - Docker Deployment Script
# This script builds and deploys the FF6 AI Player in Docker

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}========================================${NC}"
echo -e "${GREEN}  FF6 AI Player - Docker Deployment${NC}"
echo -e "${GREEN}========================================${NC}\n"

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}Error: Docker is not installed${NC}"
    echo "Please install Docker first: https://docs.docker.com/get-docker/"
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}Error: Docker Compose is not installed${NC}"
    echo "Please install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Check for API key
if [ -z "$OPENAI_API_KEY" ]; then
    echo -e "${YELLOW}Warning: OPENAI_API_KEY environment variable not set${NC}"
    echo "The AI features will not work without it."
    read -p "Enter your OpenAI API key (or press Enter to skip): " api_key
    if [ ! -z "$api_key" ]; then
        export OPENAI_API_KEY="$api_key"
    fi
fi

# Parse command line arguments
COMMAND="${1:-up}"
PROFILE="${2:-default}"

case $COMMAND in
    build)
        echo -e "${YELLOW}Building Docker image...${NC}"
        docker-compose build
        echo -e "${GREEN}Build complete!${NC}"
        ;;
    
    up)
        echo -e "${YELLOW}Starting FF6 AI Player...${NC}"
        docker-compose up -d
        echo -e "${GREEN}FF6 AI Player is running!${NC}"
        echo -e "Web interface: ${GREEN}http://localhost:5000${NC}"
        echo -e "VNC server: ${GREEN}localhost:5900${NC} (no password)"
        ;;
    
    down)
        echo -e "${YELLOW}Stopping FF6 AI Player...${NC}"
        docker-compose down
        echo -e "${GREEN}FF6 AI Player stopped${NC}"
        ;;
    
    restart)
        echo -e "${YELLOW}Restarting FF6 AI Player...${NC}"
        docker-compose restart
        echo -e "${GREEN}FF6 AI Player restarted${NC}"
        ;;
    
    logs)
        echo -e "${YELLOW}Showing logs...${NC}"
        docker-compose logs -f ff6-ai-player
        ;;
    
    status)
        echo -e "${YELLOW}Checking status...${NC}"
        docker-compose ps
        ;;
    
    clean)
        echo -e "${YELLOW}Cleaning up...${NC}"
        docker-compose down -v
        docker system prune -f
        echo -e "${GREEN}Cleanup complete${NC}"
        ;;
    
    production)
        echo -e "${YELLOW}Starting in production mode with nginx...${NC}"
        docker-compose --profile production up -d
        echo -e "${GREEN}Production deployment complete!${NC}"
        echo -e "Web interface: ${GREEN}http://localhost${NC} (through nginx)"
        ;;
    
    test)
        echo -e "${YELLOW}Running integration tests...${NC}"
        docker-compose run --rm ff6-ai-player python test_full_integration.py
        ;;
    
    shell)
        echo -e "${YELLOW}Opening shell in container...${NC}"
        docker-compose exec ff6-ai-player /bin/bash
        ;;
    
    *)
        echo "Usage: $0 {build|up|down|restart|logs|status|clean|production|test|shell}"
        echo ""
        echo "Commands:"
        echo "  build      - Build Docker image"
        echo "  up         - Start the application (default)"
        echo "  down       - Stop the application"
        echo "  restart    - Restart the application"
        echo "  logs       - Show application logs"
        echo "  status     - Show container status"
        echo "  clean      - Clean up containers and images"
        echo "  production - Start with nginx reverse proxy"
        echo "  test       - Run integration tests"
        echo "  shell      - Open shell in container"
        exit 1
        ;;
esac
