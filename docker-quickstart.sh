#!/bin/bash
# Docker Quick Start Script for Powerhouse Platform
# This script provides a simple way to start the Powerhouse Platform with Docker

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[⚠]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

# Check if Docker is installed
check_docker() {
    print_info "Checking Docker installation..."
    
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed!"
        echo "Please install Docker Desktop from: https://www.docker.com/products/docker-desktop/"
        exit 1
    fi
    
    if ! docker ps &> /dev/null; then
        print_error "Docker is not running!"
        echo "Please start Docker Desktop and try again."
        exit 1
    fi
    
    print_success "Docker is installed and running"
    docker --version
}

# Check if docker-compose is available
check_docker_compose() {
    print_info "Checking Docker Compose..."
    
    if command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    elif docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        print_error "Docker Compose is not available!"
        exit 1
    fi
    
    print_success "Docker Compose is available"
}

# Build images if needed
build_images() {
    print_info "Checking if images need to be built..."
    
    if [ "$1" == "--build" ] || [ "$1" == "-b" ]; then
        print_info "Building Docker images (this may take 5-10 minutes)..."
        $COMPOSE_CMD build
        print_success "Images built successfully"
    fi
}

# Start services
start_services() {
    print_info "Starting Powerhouse Platform services..."
    
    $COMPOSE_CMD up -d
    
    if [ $? -eq 0 ]; then
        print_success "Services started successfully"
    else
        print_error "Failed to start services"
        exit 1
    fi
}

# Wait for services to be ready
wait_for_services() {
    print_info "Waiting for services to initialize..."
    print_info "This may take 2-3 minutes (services have a lot to load)..."
    
    local max_attempts=90
    local attempt=0
    
    # Wait for PostgreSQL
    while [ $attempt -lt $max_attempts ]; do
        if $COMPOSE_CMD exec -T postgres pg_isready -U powerhouse_user -d powerhouse &> /dev/null; then
            print_success "PostgreSQL is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_warning "PostgreSQL is taking longer than expected to start"
    fi
    
    # Wait for Backend
    attempt=0
    while [ $attempt -lt $max_attempts ]; do
        if curl -s http://localhost:8001/health &> /dev/null; then
            print_success "Backend is ready"
            break
        fi
        attempt=$((attempt + 1))
        echo -n "."
        sleep 2
    done
    
    if [ $attempt -eq $max_attempts ]; then
        print_warning "Backend is taking longer than expected to start"
    fi
    
    echo ""
}

# Show service status
show_status() {
    echo ""
    print_info "Service Status:"
    $COMPOSE_CMD ps
    
    echo ""
    print_info "Service URLs:"
    echo "  🌐 Frontend:  http://localhost:3000"
    echo "  🔧 Backend:   http://localhost:8001"
    echo "  ❤️  Health:    http://localhost:8001/health"
    echo ""
}

# Show logs
show_logs() {
    if [ "$1" == "--logs" ] || [ "$1" == "-l" ]; then
        print_info "Showing logs (Ctrl+C to exit)..."
        $COMPOSE_CMD logs -f
    fi
}

# Main function
main() {
    echo "╔════════════════════════════════════════════════════════════╗"
    echo "║                                                            ║"
    echo "║         Powerhouse Platform - Docker Quick Start          ║"
    echo "║                                                            ║"
    echo "╚════════════════════════════════════════════════════════════╝"
    echo ""
    
    # Parse arguments
    BUILD=false
    LOGS=false
    
    for arg in "$@"; do
        case $arg in
            --build|-b)
                BUILD=true
                ;;
            --logs|-l)
                LOGS=true
                ;;
            --help|-h)
                echo "Usage: $0 [OPTIONS]"
                echo ""
                echo "Options:"
                echo "  -b, --build    Build Docker images before starting"
                echo "  -l, --logs     Show logs after starting"
                echo "  -h, --help     Show this help message"
                echo ""
                exit 0
                ;;
        esac
    done
    
    # Run checks and start
    check_docker
    check_docker_compose
    
    if [ "$BUILD" = true ]; then
        build_images --build
    fi
    
    start_services
    wait_for_services
    show_status
    
    if [ "$LOGS" = true ]; then
        show_logs --logs
    else
        echo "To view logs: docker-compose logs -f"
        echo "To stop:      docker-compose down"
        echo ""
    fi
}

# Run main function
main "$@"


