"""
Integracja Projektora z nlp2cmd.

Ten moduł konfiguruje automatyczne przechwytywanie błędów
i tworzenie ticketów w projektorze.

Użycie:
    # Automatyczna instalacja (zalecane) - w __init__.py lub main.py:
    try:
        from projektor import install
        install()
    except ImportError:
        pass  # projektor nie jest zainstalowany
    
    # Lub przez ten moduł:
    from projektor_integration import setup_projektor
    setup_projektor()
"""

import sys
from pathlib import Path

# Dodaj projektor do ścieżki jeśli jest w tym samym workspace
PROJEKTOR_PATH = Path(__file__).parent.parent / "projektor" / "src"
if PROJEKTOR_PATH.exists():
    sys.path.insert(0, str(PROJEKTOR_PATH))


def setup_projektor(auto_fix: bool = False) -> bool:
    """
    Konfiguruje integrację projektora z nlp2cmd.
    
    Args:
        auto_fix: Czy automatycznie próbować naprawiać błędy
        
    Returns:
        True jeśli instalacja się powiodła
    """
    try:
        from projektor import install
        return install(auto_fix=auto_fix)
    except ImportError as e:
        print(f"[projektor] Not available: {e}")
        print("[projektor] Install with: pip install projektor")
        return False


# ==================== Dekoratory ====================

def track_errors(func=None, **kwargs):
    """
    Dekorator do śledzenia błędów w funkcjach.
    
    Użycie:
        @track_errors
        def parse_command(text):
            ...
        
        @track_errors(context={"component": "parser"})
        def process(data):
            ...
    """
    try:
        from projektor import track_errors as _track_errors
        return _track_errors(func, **kwargs)
    except ImportError:
        # Fallback - zwróć oryginalną funkcję
        if func is None:
            return lambda f: f
        return func


def track_async_errors(func=None, **kwargs):
    """
    Dekorator do śledzenia błędów w funkcjach async.
    
    Użycie:
        @track_async_errors
        async def fetch_data(url):
            ...
        
        @track_async_errors(context={"component": "thermodynamic"})
        async def generate(text):
            ...
    """
    try:
        from projektor import track_async_errors as _track_async_errors
        return _track_async_errors(func, **kwargs)
    except ImportError:
        # Fallback - zwróć oryginalną funkcję
        if func is None:
            return lambda f: f
        return func


# ==================== Context Manager ====================

class ErrorTracker:
    """
    Context manager do śledzenia błędów.
    
    Użycie:
        with ErrorTracker(context={"input": text[:50]}) as tracker:
            result = process(text)
        
        if tracker.had_error:
            print(f"Error: {tracker.error}")
    """
    
    def __init__(self, **kwargs):
        self.kwargs = kwargs
        self.had_error = False
        self.error = None
        self.ticket = None
        self._real_tracker = None
    
    def __enter__(self):
        try:
            from projektor import ErrorTracker as _ErrorTracker
            self._real_tracker = _ErrorTracker(**self.kwargs)
            return self._real_tracker.__enter__()
        except ImportError:
            return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._real_tracker:
            return self._real_tracker.__exit__(exc_type, exc_val, exc_tb)
        if exc_val:
            self.had_error = True
            self.error = exc_val
        return False


# ==================== Test ====================

if __name__ == "__main__":
    print("=== Testing Projektor Integration for nlp2cmd ===\n")
    
    # Włącz integrację
    if setup_projektor(auto_fix=False):
        print("[OK] Projektor installed\n")
    else:
        print("[SKIP] Projektor not available\n")
    
    # Przykład 1: Dekorator
    print("1. Testing @track_errors decorator...")
    
    @track_errors
    def example_function():
        raise ValueError("Example error for testing")
    
    try:
        example_function()
    except ValueError as e:
        print(f"   Error caught: {e}")
    
    # Przykład 2: Context manager
    print("\n2. Testing ErrorTracker context manager...")
    
    with ErrorTracker(context={"test": "example"}) as tracker:
        # To nie rzuci błędu
        x = 1 + 1
    
    print(f"   Had error: {tracker.had_error}")
    
    print("\n=== Done ===")
    print("Check .projektor/tickets/ for created bug tickets")
