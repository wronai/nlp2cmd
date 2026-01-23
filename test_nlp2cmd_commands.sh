#!/bin/bash

# Shell script to test Docker commands through nlp2cmd
# This script will:
# 1. Check if required commands are installed
# 2. Install cmd2schema if needed
# 3. Run all test commands through nlp2cmd
# 4. Display all logs and outputs

set -e  # Exit on any error

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

# List of commands to test
COMMANDS=(
    "Run nginx on port 8080"
    "List all running containers"
    "Show logs for web container"
    "Stop all containers"
    "Remove unused images"
    "Build image from current directory tagged as myapp"
)

# Check if nlp2cmd is installed
if ! command -v nlp2cmd &> /dev/null; then
    print_error "nlp2cmd is not installed or not in PATH"
    print_status "Installing nlp2cmd..."
    
    # Try to install nlp2cmd in development mode
    if [ -d "src/nlp2cmd" ]; then
        print_status "Found local nlp2cmd source, installing in development mode..."
        pip install -e .
    else
        print_error "Cannot find nlp2cmd source code. Please ensure you're in the nlp2cmd directory."
        exit 1
    fi
else
    print_success "nlp2cmd is installed"
fi

# Function to check if a command exists and install if needed
check_and_install_command() {
    local cmd=$1
    local install_instructions=$2
    
    if ! command -v $cmd &> /dev/null; then
        print_warning "$cmd is not installed"
        
        # Check if we have cmd2schema functionality
        print_status "Attempting to generate schema for $cmd..."
        
        # Try to use nlp2cmd to generate command schema
        if command -v nlp2cmd &> /dev/null; then
            print_status "Using nlp2cmd to analyze $cmd..."
            
            # Create schema if possible
            if nlp2cmd --query "help $cmd" --dsl shell 2>/dev/null; then
                print_success "Successfully analyzed $cmd"
            else
                print_error "Could not analyze $cmd with nlp2cmd"
                print_status "Please install $cmd manually: $install_instructions"
                return 1
            fi
        else
            print_error "Cannot install $cmd automatically. Please install manually: $install_instructions"
            return 1
        fi
    else
        print_success "$cmd is available"
    fi
}

# Check for Docker
print_status "Checking for Docker..."
check_and_install_command "docker" "Visit https://docs.docker.com/get-docker/"

# Check for nginx (might be needed for some commands)
print_status "Checking for nginx..."
check_and_install_command "nginx" "sudo apt-get install nginx (Ubuntu/Debian) or sudo yum install nginx (RHEL/CentOS)"

# Function to run a command through nlp2cmd
run_nlp2cmd_command() {
    local query="$1"
    local dsl="${2:-docker}"  # Default to docker DSL
    
    print_status "Processing query: '$query'"
    echo "----------------------------------------"
    
    # Run the command and capture output
    if nlp2cmd --query "$query" --dsl "$dsl" --explain 2>&1; then
        print_success "Command processed successfully"
    else
        print_warning "Command processing encountered issues"
    fi
    
    echo "----------------------------------------"
    echo ""
}

# Main execution
main() {
    print_status "Starting nlp2cmd command testing..."
    echo ""
    
    # Test each command
    for cmd in "${COMMANDS[@]}"; do
        run_nlp2cmd_command "$cmd" "docker"
    done
    
    # Also test with auto DSL to see differences
    print_status "Testing with auto DSL mode..."
    echo ""
    
    for cmd in "${COMMANDS[@]}"; do
        run_nlp2cmd_command "$cmd" "auto"
    done
    
    print_success "All commands have been processed!"
}

# Check for help flag
if [ "$1" = "--help" ] || [ "$1" = "-h" ]; then
    echo "Usage: $0 [options]"
    echo ""
    echo "Options:"
    echo "  --help, -h     Show this help message"
    echo "  --verbose      Enable verbose output"
    echo ""
    echo "This script will test Docker commands through nlp2cmd."
    echo "It will automatically install missing dependencies if possible."
    exit 0
fi

# Check for verbose flag
if [ "$1" = "--verbose" ]; then
    set -x  # Enable command tracing
fi

# Run main function
main
