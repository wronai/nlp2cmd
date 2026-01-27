# NLP2CMD Examples Makefile
# Usage: make [target] [CATEGORY=category] [EXAMPLE=example]

# Default target
.PHONY: help
help:
	@echo "NLP2CMD Examples - Available targets:"
	@echo ""
	@echo "General commands:"
	@echo "  help           - Show this help message"
	@echo "  list           - List all available examples"
	@echo "  all            - Run all examples (will take time)"
	@echo "  clean          - Clean generated files"
	@echo ""
	@echo "Category commands:"
	@echo "  basics         - Run all basic examples"
	@echo "  benchmarks     - Run all benchmark examples"
	@echo "  integrations   - Run all integration examples"
	@echo "  domains        - Run all domain-specific examples"
	@echo "  advanced       - Run all advanced feature examples"
	@echo "  tools          - Run all tool examples"
	@echo ""
	@echo "Specific category:"
	@echo "  make CATEGORY=[category]  - Run all examples in a category"
	@echo "  Categories: 01_basics, 02_benchmarks, 03_integrations, 04_domain_specific, 05_advanced_features, 06_tools_and_utilities"
	@echo ""
	@echo "Specific example:"
	@echo "  make CATEGORY=[category] EXAMPLE=[example]  - Run a specific example"
	@echo ""
	@echo "Examples:"
	@echo "  make basics                                    # Run all basic examples"
	@echo "  make CATEGORY=01_basics                         # Run all basic examples"
	@echo "  make CATEGORY=01_basics EXAMPLE=app2schema      # Run app2schema example"
	@echo "  make CATEGORY=04_domain_specific EXAMPLE=bioinformatics  # Run bioinformatics examples"

# List all examples
.PHONY: list
list:
	@echo "Available examples by category:"
	@echo ""
	@for dir in 0*; do \
		if [ -d "$$dir" ]; then \
			echo "$$dir:"; \
			find $$dir -name "example.py" -o -name "*.py" | grep -E "(example|demo|benchmark)" | sort | sed 's/^/  /'; \
			echo ""; \
		fi; \
	done

# Run all examples (WARNING: This will take a long time!)
.PHONY: all
all:
	@echo "Running all examples..."
	@echo "This will take a significant amount of time. Press Ctrl+C to cancel."
	@sleep 5
	@for category in 01_basics 02_benchmarks 03_integrations 04_domain_specific 05_advanced_features 06_tools_and_utilities; do \
		echo "=== Running $$category ==="; \
		$(MAKE) CATEGORY=$$category; \
	done

# Category shortcuts
.PHONY: basics
basics:
	@$(MAKE) CATEGORY=01_basics

.PHONY: benchmarks
benchmarks:
	@$(MAKE) CATEGORY=02_benchmarks

.PHONY: integrations
integrations:
	@$(MAKE) CATEGORY=03_integrations

.PHONY: domains
domains:
	@$(MAKE) CATEGORY=04_domain_specific

.PHONY: advanced
advanced:
	@$(MAKE) CATEGORY=05_advanced_features

.PHONY: tools
tools:
	@$(MAKE) CATEGORY=06_tools_and_utilities

# Run all examples in a category
.PHONY: run-category
run-category:
	@if [ -z "$(CATEGORY)" ]; then \
		echo "Error: CATEGORY must be specified"; \
		echo "Usage: make CATEGORY=[category]"; \
		exit 1; \
	fi
	@if [ ! -d "$(CATEGORY)" ]; then \
		echo "Error: Category $(CATEGORY) does not exist"; \
		exit 1; \
	fi
	@echo "Running examples in $(CATEGORY)..."
	@if [ -z "$(EXAMPLE)" ]; then \
		for subdir in $(CATEGORY)/*; do \
			if [ -d "$$subdir" ]; then \
				echo ""; \
				echo "=== $$subdir ==="; \
				cd "$$subdir"; \
				for script in example.py demo.py benchmark.py *.py; do \
					if [ -f "$$script" ] && [ "$$script" != "*.py" ]; then \
						echo "Running $$script..."; \
						python3 "$$script" || echo "Failed to run $$script"; \
						echo ""; \
					fi; \
				done; \
				cd ../..; \
			fi; \
		done; \
	else \
		if [ -d "$(CATEGORY)/$(EXAMPLE)" ]; then \
			echo "Running examples in $(CATEGORY)/$(EXAMPLE)..."; \
			cd "$(CATEGORY)/$(EXAMPLE)"; \
			for script in example.py demo.py benchmark.py *.py; do \
				if [ -f "$$script" ] && [ "$$script" != "*.py" ]; then \
					echo "Running $$script..."; \
					python3 "$$script" || echo "Failed to run $$script"; \
					echo ""; \
				fi; \
			done; \
			cd ../..; \
		else \
			echo "Error: Example $(EXAMPLE) does not exist in $(CATEGORY)"; \
		fi; \
	fi

# Run a specific example
.PHONY: run-example
run-example:
	@if [ -z "$(CATEGORY)" ] || [ -z "$(EXAMPLE)" ]; then \
		echo "Error: Both CATEGORY and EXAMPLE must be specified"; \
		echo "Usage: make CATEGORY=[category] EXAMPLE=[example]"; \
		exit 1; \
	fi
	@$(MAKE) run-category

# Clean generated files
.PHONY: clean
clean:
	@echo "Cleaning generated files..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.json" -name "*report*" -delete 2>/dev/null || true
	@find . -name "*.log" -delete 2>/dev/null || true
	@find . -name "benchmark_report.*" -delete 2>/dev/null || true
	@find . -name "generated_appspec.json" -delete 2>/dev/null || true
	@echo "Clean complete."

# Quick test - run one example from each category
.PHONY: quick-test
quick-test:
	@echo "Running quick test (one example from each category)..."
	@echo "=== Basics: app2schema ==="
	@cd 01_basics/app2schema && python3 example.py
	@echo ""
	@echo "=== Benchmarks: performance ==="
	@cd 02_benchmarks/performance_testing && python3 benchmark.py || echo "Benchmark may require specific setup"
	@echo ""
	@echo "=== Integrations: TOON ==="
	@cd 03_integrations/toon_format && python3 simple_demo.py
	@echo ""
	@echo "=== Domains: bioinformatics ==="
	@cd 04_domain_specific/bioinformatics && python3 example.py
	@echo ""
	@echo "=== Advanced: thermodynamic ==="
	@cd 05_advanced_features/thermodynamic_computing && python3 example.py || echo "Thermodynamic example may require additional dependencies"
	@echo ""
	@echo "Quick test complete!"

# Check dependencies
.PHONY: check-deps
check-deps:
	@echo "Checking dependencies..."
	@python3 -c "import nlp2cmd" || echo "Warning: nlp2cmd not installed"
	@python3 -c "import numpy" || echo "Warning: numpy not installed (required for some examples)"
	@python3 -c "import asyncio" || echo "Warning: asyncio not available"
	@echo "Dependency check complete."

# Set default target
.DEFAULT_GOAL := help

# Handle CATEGORY parameter
ifneq ($(CATEGORY),)
.PHONY: $(CATEGORY)
$(CATEGORY):
	@$(MAKE) run-category
endif
