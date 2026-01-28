"""
Practical Usage Examples for TOON Format
Real-world examples showing how to use the unified TOON system
"""

import sys
from pathlib import Path

# Add src to path for imports
_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

# Simple demo without full dependencies
class ToonDemo:
    """Demo class showing TOON usage patterns"""
    
    def __init__(self):
        self.toon_file = _repo_root / "project.unified.toon"
        self.data = self._load_toon_data()
    
    def _load_toon_data(self):
        """Load and parse TOON data for demo"""
        if not self.toon_file.exists():
            print(f"TOON file not found: {self.toon_file}")
            return {}
        
        with open(self.toon_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Simple parsing for demo
        return {"content": content, "loaded": True}
    
    def show_basic_usage(self):
        """Show basic TOON usage"""
        print("=== PODSTAWOWE UŻYCIE TOON ===\n")
        
        print("1. Inicjalizacja systemu:")
        print("""
from nlp2cmd.core.toon_integration import get_data_manager

# Załaduj menedżer danych
manager = get_data_manager()

# Lub z konkretnym plikiem
manager = get_data_manager("project.unified.toon")
""")
        
        print("2. Pobieranie wszystkich komend:")
        print("""
# Wszystkie komendy z wszystkich kategorii
all_commands = manager.get_all_commands()

# Komendy shell
shell_commands = manager.get_shell_commands()

# Komendy przeglądarki
browser_commands = manager.get_browser_commands()
""")
        
        print("3. Pobieranie konfiguracji:")
        print("""
# Cała konfiguracja
config = manager.get_config()

# Konkretna wartość konfiguracji
batch_size = manager.get_config('schema_generation.batch_size')
llm_model = manager.get_config('schema_generation.llm.model')
""")
        
        print("4. Wyszukiwanie komend:")
        print("""
# Wyszukaj we wszystkich kategoriach
results = manager.search_commands("git")

# Wyszukaj w konkretnej kategorii
shell_results = manager.search_commands("docker", category="shell")
""")
    
    def show_advanced_usage(self):
        """Show advanced TOON usage"""
        print("\n=== ZAAWANSOWANE UŻYCIE TOON ===\n")
        
        print("1. Praca z konkretnymi komendami:")
        print("""
# Pobierz konkretną komendę
git_cmd = manager.get_command_by_name('git')

# Pobierz przykłady dla komendy
examples = manager.get_command_examples('git')
print(f"Przykłady dla git: {examples}")

# Pobierz wzorce dla komendy
patterns = manager.get_command_patterns('git')
print(f"Wzorce dla git: {patterns}")

# Pobierz szablon komendy
template = manager.get_command_template('git')
print(f"Szablon dla git: {template}")
""")
        
        print("2. Praca z szablonami:")
        print("""
# Szablony generowania komend
cmd_templates = manager.get_command_templates()
print(f"Dostępne szablony: {list(cmd_templates.keys())}")

# Szablony akcji przeglądarki
browser_templates = manager.get_browser_templates()
print(f"Szablony przeglądarki: {list(browser_templates.keys())}")

# Szablony obsługi błędów
error_templates = manager.get_error_templates()
print(f"Szablony błędów: {list(error_templates.keys())}")
""")
        
        print("3. Praca z mapowaniami:")
        print("""
# Mapowania kategorii
category_mappings = manager.get_category_mappings()
print(f"Mapowania kategorii: {category_mappings}")

# Wzorce językowe
english_patterns = manager.get_language_patterns('english')
polish_patterns = manager.get_language_patterns('polish')

# Aliasy komend
command_aliases = manager.get_command_aliases()
print(f"Aliasy komend: {command_aliases}")
""")
        
        print("4. Metadane projektu:")
        print("""
# Metadane projektu
metadata = manager.get_project_metadata()
print(f"Projekt: {metadata.get('project')}")
print(f"Wersja: {metadata.get('version')}")
print(f"Wygenerowano: {metadata.get('generated')}")

# Statystyki
stats = manager.get_statistics()
print(f"Statystyki: {stats}")
""")
    
    def show_real_world_examples(self):
        """Show real-world usage examples"""
        print("\n=== PRAKTYCZNE PRZYKŁADY ===\n")
        
        print("Przykład 1: Generator Komend")
        print("""
class CommandGenerator:
    def __init__(self):
        self.manager = get_data_manager()
    
    def generate_command(self, command_name, user_input):
        # Pobierz komendę
        cmd = self.manager.get_command_by_name(command_name)
        if not cmd:
            return f"Komenda '{command_name}' nie znaleziona"
        
        # Pobierz szablon
        template = cmd.get('template')
        if template:
            return template.format(**self._extract_params(user_input))
        
        return cmd.get('description', '')
    
    def _extract_params(self, user_input):
        # Ekstrakcja parametrów z inputu użytkownika
        return {"input": user_input}

# Użycie
generator = CommandGenerator()
result = generator.generate_command('git', 'show branch')
print(result)
""")
        
        print("Przykład 2: System Wyszukiwania")
        print("""
class CommandSearchSystem:
    def __init__(self):
        self.manager = get_data_manager()
    
    def find_command(self, query, category=None):
        # Wyszukaj komendy
        results = self.manager.search_commands(query, category)
        
        if not results:
            return f"Nie znaleziono komend dla: {query}"
        
        # Zwróć najlepszy wynik
        best_match = results[0]
        return f"Znaleziono: {best_match['name']} - {best_match.get('description', '')}"
    
    def suggest_commands(self, partial_query):
        # Sugestie na podstawie częściowego zapytania
        all_commands = self.manager.get_all_commands()
        suggestions = []
        
        for category, commands in all_commands.items():
            for cmd_name, cmd_data in commands.items():
                if partial_query.lower() in cmd_name.lower():
                    suggestions.append(f"{cmd_name}: {cmd_data.get('description', '')}")
        
        return suggestions[:5]  # Limit do 5 sugestii

# Użycie
search = CommandSearchSystem()
print(search.find_command('git'))
print(search.suggest_commands('do'))
""")
        
        print("Przykład 3: System Konfiguracyjny")
        print("""
class ConfigManager:
    def __init__(self):
        self.manager = get_data_manager()
    
    def get_llm_settings(self):
        '''Pobierz ustawienia LLM'''
        return self.manager.get_llm_config()
    
    def update_llm_setting(self, key, value):
        '''Aktualizuj ustawienie LLM (demo)'''
        current_config = self.manager.get_llm_config()
        current_config[key] = value
        print(f"Zaktualizowano {key}: {value}")
        return current_config
    
    def get_test_commands(self):
        '''Pobierz listę komend testowych'''
        return self.manager.get_test_commands()
    
    def validate_config(self):
        '''Walidacja konfiguracji'''
        config = self.manager.get_config()
        required_keys = ['schema_generation', 'test_commands']
        
        missing = [key for key in required_keys if key not in config]
        if missing:
            return f"Brakujące klucze: {missing}"
        
        return "Konfiguracja poprawna"

# Użycie
config_mgr = ConfigManager()
llm_settings = config_mgr.get_llm_settings()
print(f"Ustawienia LLM: {llm_settings}")
print(config_mgr.validate_config())
""")
        
        print("Przykład 4: System Eksportu Danych")
        print("""
class DataExporter:
    def __init__(self):
        self.manager = get_data_manager()
    
    def export_all_data(self, format='json'):
        '''Eksportuj wszystkie dane'''
        data = {
            'commands': self.manager.export_category('commands', format),
            'config': self.manager.export_category('config', format),
            'metadata': self.manager.export_category('metadata', format),
            'templates': self.manager.export_category('templates', format),
            'mappings': self.manager.export_category('mappings', format)
        }
        return data
    
    def export_category(self, category, format='json'):
        '''Eksportuj konkretną kategorię'''
        return self.manager.export_category(category, format)
    
    def backup_data(self, backup_dir="backups"):
        '''Stwórz kopię zapasową'''
        from datetime import datetime
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = Path(backup_dir) / f"backup_{timestamp}"
        backup_path.mkdir(exist_ok=True)
        
        # Eksportuj każdą kategorię
        for category in ['commands', 'config', 'metadata', 'templates', 'mappings']:
            data = self.export_category(category, 'json')
            with open(backup_path / f"{category}.json", 'w') as f:
                f.write(data)
        
        print(f"Kopia zapasowa zapisana w: {backup_path}")
        return backup_path

# Użycie
exporter = DataExporter()
all_data = exporter.export_all_data()
backup_path = exporter.backup_data()
""")
    
    def show_integration_examples(self):
        """Show integration with existing systems"""
        print("\n=== INTEGRACJA Z ISTNIEJĄCYMI SYSTEMAMI ===\n")
        
        print("Przykład 1: Migracja z istniejącego kodu")
        print("""
# STARY KOD:
def load_command_schemas_old():
    import json
    from pathlib import Path
    
    commands = {}
    schemas_dir = Path("command_schemas")
    
    # Ładowanie shell commands
    shell_dir = schemas_dir / "commands"
    for json_file in shell_dir.glob("*.json"):
        with open(json_file, 'r') as f:
            data = json.load(f)
            commands[data['command']] = data
    
    return commands

# NOWY KOD (TOON):
def load_command_schemas_new():
    from nlp2cmd.core.toon_integration import get_data_manager
    
    manager = get_data_manager()
    return manager.get_all_commands()

# Użycie (bez zmian w reszcie kodu)
commands = load_command_schemas_new()
""")
        
        print("Przykład 2: Kompatybilność wsteczna")
        print("""
# Funkcja kompatybilności dla istniejącego kodu
def get_command_schemas():
    '''Funkcja kompatybilna ze starym systemem'''
    manager = get_data_manager()
    return manager.get_all_commands()

def get_project_config():
    '''Funkcja kompatybilna dla konfiguracji'''
    manager = get_data_manager()
    return manager.get_config()

def search_in_commands(query):
    '''Funkcja kompatybilna dla wyszukiwania'''
    manager = get_data_manager()
    return manager.search_commands(query)

# Istniejący kod działa bez zmian
commands = get_command_schemas()
config = get_project_config()
results = search_in_commands("git")
""")
        
        print("Przykład 3: Aktualizacja istniejących klas")
        print("""
# STARA KLASA:
class OldCommandProcessor:
    def __init__(self):
        self.commands = self._load_commands()
        self.config = self._load_config()
    
    def _load_commands(self):
        # Skomplikowane ładowanie JSON
        pass
    
    def _load_config(self):
        # Ładowanie YAML
        pass

# NOWA KLASA (TOON):
class NewCommandProcessor:
    def __init__(self):
        self.manager = get_data_manager()
    
    def get_commands(self):
        return self.manager.get_all_commands()
    
    def get_config(self):
        return self.manager.get_config()
    
    def process_command(self, command_name):
        cmd = self.manager.get_command_by_name(command_name)
        if cmd:
            return self._generate_response(cmd)
        return "Komenda nie znaleziona"
    
    def _generate_response(self, cmd):
        examples = cmd.get('examples', [])
        return examples[0] if examples else cmd.get('description', '')
""")
    
    def show_performance_tips(self):
        """Show performance optimization tips"""
        print("\n=== WSKAZÓWKI WYDAJNOŚCIOWE ===\n")
        
        print("1. Cache'owanie menedżera:")
        print("""
# Używaj globalnej instancji menedżera
from nlp2cmd.core.toon_integration import get_data_manager

# Inicjalizuj raz na początku aplikacji
_manager = get_data_manager()

def get_commands():
    global _manager
    return _manager.get_all_commands()
""")
        
        print("2. Ładowanie opóźnione:")
        print("""
# Ładuj tylko potrzebne kategorie
def get_shell_commands_only():
    manager = get_data_manager()
    return manager.get_shell_commands()

def get_config_only():
    manager = get_data_manager()
    return manager.get_config()
""")
        
        print("3. Praca z podzbiorem danych:")
        print("""
# Pracuj z konkretnymi kategoriami zamiast wszystkiego
def search_efficiently(query, category='shell'):
    manager = get_data_manager()
    return manager.search_commands(query, category)
""")
        
        print("4. Eksport tylko potrzebnych danych:")
        print("""
# Eksportuj tylko potrzebne kategorie
def export_minimal_data():
    manager = get_data_manager()
    
    # Tylko komendy i konfiguracja
    return {
        'commands': manager.export_category('commands', 'json'),
        'config': manager.export_category('config', 'json')
    }
""")


def main():
    """Main demo function"""
    print("=== PRAKTYCZNE PRZYKŁADY UŻYCIA TOON ===\n")
    
    demo = ToonDemo()
    
    if not demo.data.get('loaded'):
        print("Nie można załadować danych TOON. Upewnij się, że plik project.unified.toon istnieje.")
        return
    
    demo.show_basic_usage()
    demo.show_advanced_usage()
    demo.show_real_world_examples()
    demo.show_integration_examples()
    demo.show_performance_tips()
    
    print("\n=== PODSUMOWANIE ===\n")
    print("✅ Prosta inicjalizacja: get_data_manager()")
    print("✅ Jednolity dostęp do wszystkich danych")
    print("✅ Wbudowane funkcje wyszukiwania")
    print("✅ Elastyczny eksport danych")
    print("✅ Kompatybilność wsteczna")
    print("✅ Wysoka wydajność")
    print("✅ Łatwa integracja")
    print("\nSystem TOON jest gotowy do użycia w projektach!")


if __name__ == "__main__":
    main()
