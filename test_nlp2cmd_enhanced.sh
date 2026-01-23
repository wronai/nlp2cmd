#!/bin/bash

# Enhanced shell script to test Docker commands through nlp2cmd
# This script will:
# 1. Check if required commands are installed
# 2. Generate schemas for missing commands (cmd2schema)
# 3. Run all test commands through nlp2cmd
# 4. Display all logs and outputs

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SCHEMA_DIR="$SCRIPT_DIR/command_schemas"
LOG_FILE="$SCRIPT_DIR/nlp2cmd_test.log"

# Ensure schema directory exists
mkdir -p "$SCHEMA_DIR"

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$LOG_FILE"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$LOG_FILE"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1" | tee -a "$LOG_FILE"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$LOG_FILE"
}

print_header() {
    echo -e "${CYAN}=== $1 ===${NC}" | tee -a "$LOG_FILE"
}

# List of commands to test
declare -A COMMANDS=(
    ["List all running containers"]="docker"
    ["Show logs for web container"]="docker"
    ["Stop all containers"]="docker"
    ["Remove unused images"]="docker"
    ["Build image from current directory tagged as myapp"]="docker"
)

# List of required system commands
REQUIRED_COMMANDS=(
    "docker"
    "nginx"
)

# Function to check if nlp2cmd is installed
check_nlp2cmd() {
    print_header "Checking nlp2cmd Installation"
    
    if ! command -v nlp2cmd &> /dev/null; then
        print_error "nlp2cmd is not installed or not in PATH"
        print_status "Installing nlp2cmd..."
        
        # Try to install nlp2cmd in development mode
        if [ -d "src/nlp2cmd" ]; then
            print_status "Found local nlp2cmd source, installing in development mode..."
            pip install -e . 2>&1 | tee -a "$LOG_FILE"
        else
            print_error "Cannot find nlp2cmd source code. Please ensure you're in the nlp2cmd directory."
            exit 1
        fi
    else
        print_success "nlp2cmd is installed"
        nlp2cmd --version 2>&1 | tee -a "$LOG_FILE" || true
    fi
}

# Function to generate schema for a command using app2schema
generate_command_schema() {
    local cmd=$1
    local schema_file="$SCHEMA_DIR/${cmd}.json"
    
    if [ ! -f "$schema_file" ]; then
        print_status "Generating schema for command: $cmd"
        
        # Use app2schema to generate schema
        if command -v python &> /dev/null; then
            if python -m app2schema "$cmd" --type shell -o "${schema_file}.tmp" 2>/dev/null; then
                # Convert appspec to our format if needed
                mv "${schema_file}.tmp" "$schema_file"
                print_success "Schema generated for $cmd"
            else
                print_warning "app2schema failed for $cmd, creating placeholder"
                create_placeholder_schema "$cmd" "$schema_file"
            fi
        else
            print_warning "Python not found, creating placeholder schema"
            create_placeholder_schema "$cmd" "$schema_file"
        fi
    else
        print_success "Schema already exists for $cmd"
    fi
}

# Function to create placeholder schema
create_placeholder_schema() {
    local cmd=$1
    local schema_file="$2"
    
    if command -v "$cmd" &> /dev/null; then
        local installed="true"
    else
        local installed="false"
    fi
    
    # Create a basic schema
    cat > "$schema_file" << EOF
{
  "format": "app2schema.appspec",
  "version": 1,
  "app": {
    "name": "$cmd",
    "kind": "shell",
    "source": "generated",
    "metadata": {}
  },
  "actions": [
    {
      "id": "shell.$cmd",
      "type": "shell",
      "description": "Command: $cmd",
      "dsl": {
        "kind": "shell",
        "output_format": "raw"
      },
      "params": {},
      "schema": {
        "command": "$cmd"
      },
      "match": {
        "patterns": ["$cmd"],
        "examples": ["$cmd --help"]
      },
      "executor": {
        "kind": "shell",
        "config": {}
      },
      "metadata": {
        "installed": $installed
      },
      "tags": []
    }
  ],
  "metadata": {}
}
EOF
}

# Function to install missing commands with schema generation
install_command_with_schema() {
    local cmd=$1
    local install_instructions=$2
    
    if ! command -v $cmd &> /dev/null; then
        print_warning "$cmd is not installed"
        
        # Generate schema first
        generate_command_schema "$cmd"
        
        # Provide installation instructions
        print_status "To install $cmd, please run:"
        echo "  $install_instructions"
        
        # Ask user if they want to continue without the command
        read -p "Continue without $cmd? (y/N): " -n 1 -r
        echo
        if [[ ! $REPLY =~ ^[Yy]$ ]]; then
            print_error "Installation aborted by user"
            exit 1
        fi
    else
        print_success "$cmd is available"
        # Generate schema for available command
        generate_command_schema "$cmd"
    fi
}

# Function to run a command through nlp2cmd with full logging
run_nlp2cmd_command() {
    local query="$1"
    local dsl="${2:-docker}"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    print_header "Processing: $query"
    echo "Timestamp: $timestamp" | tee -a "$LOG_FILE"
    echo "DSL: $dsl" | tee -a "$LOG_FILE"
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    
    # Run the command with full output
    local output
    local exit_code
    
    print_status "Executing: nlp2cmd --query \"$query\" --dsl \"$dsl\" --explain"
    
    if output=$(nlp2cmd --query "$query" --dsl "$dsl" --explain 2>&1); then
        exit_code=0
        print_success "Command processed successfully"
    else
        exit_code=$?
        print_warning "Command processing encountered issues (exit code: $exit_code)"
    fi
    
    # Print the output
    echo "$output" | tee -a "$LOG_FILE"
    
    # Try to extract and execute the generated command if it looks safe
    local generated_cmd
    generated_cmd=$(echo "$output" | grep -E "^(docker|kubectl|nginx)" | head -1 || echo "")
    
    if [ -n "$generated_cmd" ]; then
        print_status "Generated command detected: $generated_cmd"
        
        # Ask before executing
        read -p "Execute this command? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            print_status "Executing: $generated_cmd"
            if eval "$generated_cmd" 2>&1 | tee -a "$LOG_FILE"; then
                print_success "Command executed successfully"
            else
                print_warning "Command execution failed"
            fi
        else
            print_status "Skipping execution"
        fi
    fi
    
    echo "----------------------------------------" | tee -a "$LOG_FILE"
    echo "" | tee -a "$LOG_FILE"
    
    return $exit_code
}

# Function to test all commands
test_all_commands() {
    print_header "Testing All Commands"
    
    local success_count=0
    local total_count=${#COMMANDS[@]}
    
    for query in "${!COMMANDS[@]}"; do
        local dsl=${COMMANDS[$query]}
        
        if run_nlp2cmd_command "$query" "$dsl"; then
            ((success_count++))
        fi
        
        echo "" | tee -a "$LOG_FILE"
    done
    
    print_header "Test Results"
    echo "Successful: $success_count/$total_count" | tee -a "$LOG_FILE"
    echo "Success rate: $(( success_count * 100 / total_count ))%" | tee -a "$LOG_FILE"
}

# Function to show generated schemas
show_schemas() {
    print_header "Generated Command Schemas"
    
    if [ -d "$SCHEMA_DIR" ] && [ "$(ls -A $SCHEMA_DIR)" ]; then
        for schema in "$SCHEMA_DIR"/*.json; do
            if [ -f "$schema" ]; then
                local cmd=$(basename "$schema" .json)
                echo -e "${CYAN}Schema for $cmd:${NC}" | tee -a "$LOG_FILE"
                
                # Check if it's an appspec format
                if grep -q '"format": "app2schema.appspec"' "$schema" 2>/dev/null; then
                    # Extract description from appspec
                    local desc
                    desc=$(grep - '"description"' "$schema" | head -1 | cut -d'"' -f4 || echo "No description")
                    echo "Format: app2schema.appspec"
                    echo "Description: $desc"
                    echo "File: $schema"
                else
                    # Show raw JSON for other formats
                    cat "$schema" | tee -a "$LOG_FILE"
                fi
                echo "" | tee -a "$LOG_FILE"
            fi
        done
    else
        print_warning "No schemas found in $SCHEMA_DIR"
    fi
}

# Function to cleanup
cleanup() {
    print_status "Cleaning up..."
    # Add any cleanup tasks here
}

# Main execution
main() {
    # Initialize log file
    echo "nlp2cmd Test Log - $(date)" > "$LOG_FILE"
    echo "=========================" >> "$LOG_FILE"
    
    print_header "nlp2cmd Command Testing Script"
    echo "Log file: $LOG_FILE"
    echo "Schema directory: $SCHEMA_DIR"
    echo ""
    
    # Check dependencies
    check_nlp2cmd
    echo ""
    
    # Check and install required commands
    print_header "Checking Required Commands"
    install_command_with_schema "docker" "Visit https://docs.docker.com/get-docker/"
    install_command_with_schema "nginx" "sudo apt-get install nginx (Ubuntu/Debian) or sudo yum install nginx (RHEL/CentOS)"
    echo ""
    
    # Show generated schemas
    show_schemas
    echo ""
    
    # Test commands
    test_all_commands
    
    print_success "Testing completed!"
    print_status "Full log available at: $LOG_FILE"
}

# Handle script arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [options]"
        echo ""
        echo "Options:"
        echo "  --help, -h     Show this help message"
        echo "  --verbose      Enable verbose output"
        echo "  --dry-run      Only check commands without executing"
        echo "  --schemas      Show only generated schemas"
        echo ""
        echo "This script tests Docker commands through nlp2cmd."
        echo "It automatically generates schemas using app2schema for missing commands."
        exit 0
        ;;
    --verbose)
        set -x  # Enable command tracing
        main
        ;;
    --dry-run)
        print_header "Dry Run Mode - Only Checking Commands"
        check_nlp2cmd
        for cmd in "${REQUIRED_COMMANDS[@]}"; do
            install_command_with_schema "$cmd" "Manual installation required"
        done
        print_success "Dry run completed"
        exit 0
        ;;
    --schemas)
        show_schemas
        exit 0
        ;;
    *)
        # Set up cleanup trap
        trap cleanup EXIT
        
        main
        ;;
esac
