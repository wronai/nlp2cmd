#!/bin/bash
# Setup and run the 100 commands test

echo "=== NLP2CMD LLM Schema Test Setup ==="

# Check if Ollama is installed
if ! command -v ollama &> /dev/null; then
    echo "ERROR: Ollama is not installed. Please install it first:"
    echo "curl -fsSL https://ollama.ai/install.sh | sh"
    exit 1
fi

# Check if Ollama is running
if ! ollama list &> /dev/null; then
    echo "Starting Ollama..."
    ollama serve &
    sleep 5
fi

# Pull the model if not already available
if ! ollama list | grep -q "qwen2.5-coder:7b"; then
    echo "Pulling qwen2.5-coder:7b model..."
    ollama pull qwen2.5-coder:7b
fi

# Install dependencies
echo "Installing Python dependencies..."
pip install litellm pyyaml

# Run the test
echo "Running schema generation test..."
python test_100_commands.py

echo "Test complete! Check the following files:"
echo "  - schemas_no_llm.json (schemas generated without LLM)"
echo "  - schemas_with_llm.json (schemas generated with LLM)"
echo "  - test_results_no_llm.json (test results without LLM)"
echo "  - test_results_with_llm.json (test results with LLM)"
