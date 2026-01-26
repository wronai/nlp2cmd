"""
Integracja Projektora z nlp2cmd.

Ten moduł konfiguruje automatyczne przechwytywanie błędów
i tworzenie ticketów w projektorze.

Użycie:
    # W głównym pliku nlp2cmd (np. __main__.py lub cli.py):
    from projektor_integration import setup_projektor
    setup_projektor()
    
    # Lub importuj z projektor bezpośrednio:
    from projektor.integration import install_global_handler
    install_global_handler(auto_fix=False)
"""

import sys
from pathlib import Path

# Dodaj projektor do ścieżki jeśli jest w tym samym workspace
PROJEKTOR_PATH = Path(__file__).parent.parent / "projektor" / "src"
if PROJEKTOR_PATH.exists():
    sys.path.insert(0, str(PROJEKTOR_PATH))


def setup_projektor(auto_fix: bool = False) -> None:
    """
    Konfiguruje integrację projektora z nlp2cmd.
    
    Args:
        auto_fix: Czy automatycznie próbować naprawiać błędy
    """
    try:
        from projektor.integration import install_global_handler
        from projektor.integration.config_loader import load_integration_config
        
        # Załaduj konfigurację z projektor.yaml lub pyproject.toml
        config = load_integration_config(Path(__file__).parent)
        
        if not config.enabled:
            print("[projektor] Integration disabled in config")
            return
        
        # Użyj ustawień z konfiguracji
        install_global_handler(auto_fix=config.auto_fix or auto_fix)
        
        print("[projektor] Error tracking enabled for nlp2cmd")
        if config.auto_fix or auto_fix:
            print("[projektor] Auto-fix is ON")
        
    except ImportError as e:
        print(f"[projektor] Not available: {e}")
        print("[projektor] Install with: pip install projektor")


def catch_nlp2cmd_errors(func):
    """
    Dekorator do przechwytywania błędów w nlp2cmd.
    
    Użycie:
        @catch_nlp2cmd_errors
        def parse_command(text):
            ...
    """
    try:
        from projektor.integration import catch_errors
        from projektor.core.ticket import Priority
        
        return catch_errors(
            func,
            auto_fix=False,
            priority=Priority.HIGH,
            labels=["nlp2cmd", "runtime-error"],
        )
    except ImportError:
        # Fallback - zwróć oryginalną funkcję
        return func


# ==================== Przykłady użycia ====================

if __name__ == "__main__":
    # Włącz integrację
    setup_projektor(auto_fix=False)
    
    # Przykład funkcji z dekoratorem
    @catch_nlp2cmd_errors
    def example_function():
        # Ta funkcja automatycznie utworzy ticket przy błędzie
        raise ValueError("Example error for testing projektor integration")
    
    print("Testing projektor integration...")
    try:
        example_function()
    except ValueError as e:
        print(f"Error caught: {e}")
        print("Check .projektor/tickets/ for the created bug ticket")
