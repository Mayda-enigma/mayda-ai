#!/bin/bash

# Voice Chef Docker Management Script

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to check if Docker is running
check_docker() {
    if ! docker info >/dev/null 2>&1; then
        print_error "Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to check audio setup (Linux)
check_audio_linux() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        print_status "Checking audio setup..."
        
        # Check if user is in audio group
        if groups $USER | grep -q '\baudio\b'; then
            print_success "User is in audio group"
        else
            print_warning "User is not in audio group. Run: sudo usermod -a -G audio $USER"
        fi
        
        # Check PulseAudio
        if pgrep -x "pulseaudio" > /dev/null; then
            print_success "PulseAudio is running"
        else
            print_warning "PulseAudio is not running. Audio may not work."
        fi
    fi
}

# Function to build the application
build() {
    print_status "Building Voice Chef Docker image..."
    check_docker
    docker-compose build --no-cache
    print_success "Build completed successfully!"
}

# Function to run in production mode
run() {
    print_status "Starting Voice Chef application..."
    check_docker
    check_audio_linux
    docker-compose up -d
    print_success "Application started! Use 'logs' command to view output."
}

# Function to run in development mode
dev() {
    print_status "Starting Voice Chef in development mode..."
    check_docker
    check_audio_linux
    docker-compose -f docker-compose.dev.yml up
}

# Function to view logs
logs() {
    print_status "Viewing application logs..."
    docker-compose logs -f voice-chef
}

# Function to stop the application
stop() {
    print_status "Stopping Voice Chef application..."
    docker-compose down
    print_success "Application stopped successfully!"
}

# Function to restart the application
restart() {
    print_status "Restarting Voice Chef application..."
    stop
    run
}

# Function to clean up
clean() {
    print_status "Cleaning up Docker resources..."
    docker-compose down -v --remove-orphans
    docker image prune -f
    print_success "Cleanup completed!"
}

# Function to test audio in container
test_audio() {
    print_status "Testing audio in container..."
    docker-compose exec voice-chef python -c "
import sounddevice as sd
print('Available audio devices:')
print(sd.query_devices())
print('Testing microphone access...')
try:
    import numpy as np
    audio = sd.rec(int(1 * 16000), samplerate=16000, channels=1, dtype='float32')
    sd.wait()
    print('✅ Audio recording test successful!')
except Exception as e:
    print(f'❌ Audio test failed: {e}')
"
}

# Function to enter container shell
shell() {
    print_status "Opening shell in Voice Chef container..."
    docker-compose exec voice-chef /bin/bash
}

# Function to show status
status() {
    print_status "Voice Chef application status:"
    docker-compose ps
}

# Function to show help
help() {
    echo "Voice Chef Docker Management"
    echo ""
    echo "Usage: $0 [COMMAND]"
    echo ""
    echo "Commands:"
    echo "  build       Build the Docker image"
    echo "  run         Start the application in production mode"
    echo "  dev         Start the application in development mode"
    echo "  logs        View application logs"
    echo "  stop        Stop the application"
    echo "  restart     Restart the application"
    echo "  clean       Clean up Docker resources"
    echo "  test-audio  Test audio functionality in container"
    echo "  shell       Open a shell in the container"
    echo "  status      Show application status"
    echo "  help        Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0 build && $0 run    # Build and run the application"
    echo "  $0 dev                # Run in development mode"
    echo "  $0 logs               # View real-time logs"
}

# Main script logic
case "${1:-}" in
    build)
        build
        ;;
    run)
        run
        ;;
    dev)
        dev
        ;;
    logs)
        logs
        ;;
    stop)
        stop
        ;;
    restart)
        restart
        ;;
    clean)
        clean
        ;;
    test-audio)
        test_audio
        ;;
    shell)
        shell
        ;;
    status)
        status
        ;;
    help|--help|-h)
        help
        ;;
    *)
        print_error "Unknown command: ${1:-}"
        echo ""
        help
        exit 1
        ;;
esac