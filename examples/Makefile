# Prosty Makefile do uruchamiania przykładów NLP2CMD
# Użycie: make [nazwa_folderu] lub make all

# Domyślna akcja - pokaz pomoc
.PHONY: help
help:
	@echo "Dostępne komendy:"
	@echo ""
	@echo "Uruchom pojedynczy przykład:"
	@echo "  make [nazwa_folderu]           - Uruchom przykład z danego folderu"
	@echo ""
	@echo "Uruchom grupy przykładów:"
	@echo "  make all                        - Uruchom WSZYSTKIE przykłady"
	@echo "  make 01_basics                  - Podstawowe przykłady"
	@echo "  make 02_benchmarks              - Testy wydajnościowe"
	@echo "  make 03_integrations            - Integracje"
	@echo "  make 04_domain_specific         - Przykłady domenowe"
	@echo "  make 05_advanced_features       - Zaawansowane funkcje"
	@echo "  make 06_tools_and_utilities     - Narzędzia"
	@echo ""
	@echo "Inne komendy:"
	@echo "  make list                       - Pokaż wszystkie przykłady"
	@echo "  make clean                      - Wyczyść pliki tymczasowe"

# Uruchom wszystkie przykłady
.PHONY: all
all:
	@echo "Uruchamianie WSZYSTKICH przykładów..."
	@echo "To może zająć dużo czasu. Ctrl+C aby przerwać."
	@sleep 3
	@export NLP2CMD_KEYWORD_DETECTOR_CONFIG="$(CURDIR)/../data/keyword_intent_detector_config.json"; \
	export NLP2CMD_PATTERNS_FILE="$(CURDIR)/../data/patterns.json"; \
	export NLP2CMD_EXAMPLES_NONINTERACTIVE="1"; \
	export PYTHONPATH="$(CURDIR)/../src:$$PYTHONPATH"; \
	for dir in 0*; do \
		if [ -d "$$dir" ]; then \
			echo ""; \
			echo "=== $$dir ==="; \
			$(MAKE) "$$dir"; \
		fi; \
	done

# Uruchom pojedynczy przykład lub grupę
.PHONY: 01_basics 02_benchmarks 03_integrations 04_domain_specific 05_advanced_features 06_tools_and_utilities
01_basics 02_benchmarks 03_integrations 04_domain_specific 05_advanced_features 06_tools_and_utilities:
	@echo "Uruchamianie przykładów z folderu: $@"
	@if [ -d "$@" ]; then \
		cd "$@"; \
		export NLP2CMD_KEYWORD_DETECTOR_CONFIG="$(CURDIR)/../data/keyword_intent_detector_config.json"; \
		export NLP2CMD_PATTERNS_FILE="$(CURDIR)/../data/patterns.json"; \
		export NLP2CMD_EXAMPLES_NONINTERACTIVE="1"; \
		export PYTHONPATH="$(CURDIR)/../src:$$PYTHONPATH"; \
		for subdir in */; do \
			if [ -d "$$subdir" ]; then \
				echo ""; \
				echo "--- $$subdir ---"; \
				cd "$$subdir"; \
				for script in example.py demo.py benchmark.py *.py; do \
					if [ -f "$$script" ] && [ "$$script" != "*.py" ]; then \
						echo "Uruchamianie: $$script"; \
						python3 "$$script" || echo "Błąd: $$script"; \
					fi; \
				done; \
				cd ..; \
			fi; \
		done; \
		cd ..; \
	else \
		echo "Folder $@ nie istnieje!"; \
	fi

# Lista wszystkich przykładów
.PHONY: list
list:
	@echo "Dostępne przykłady:"
	@echo ""
	@for dir in 0*; do \
		if [ -d "$$dir" ]; then \
			echo "$$dir:"; \
			find $$dir -name "*.py" | grep -E "(example|demo|benchmark)" | sort | sed 's/^/  /'; \
			echo ""; \
		fi; \
	done

# Wyczyść pliki tymczasowe
.PHONY: clean
clean:
	@echo "Czyszczenie..."
	@find . -name "*.pyc" -delete
	@find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
	@find . -name "*.log" -delete 2>/dev/null || true
	@find . -name "*report*.json" -delete 2>/dev/null || true
	@echo "Gotowe."

# Domyślny cel
.DEFAULT_GOAL := help
