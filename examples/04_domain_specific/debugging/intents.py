#!/usr/bin/env python3
"""
Debug intent detection - sprawdzenie jakie intenty są wykrywane
"""

import asyncio
import sys
from pathlib import Path

# Dodaj ścieżkę do importów
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_rule

from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator


async def debug_intents():
    """Debug intent detection."""
    print("🔍 Debugowanie intent detection")
    print_rule(width=50, char="=")
    
    generator = HybridThermodynamicGenerator()
    
    # Test cases
    test_cases = [
        "znajdź pliki z rozszerzeniem .py",
        "skopiuj plik config.json do backup/",
        "usuń wszystkie pliki .tmp",
        "pokaż zawartość pliku /var/log/syslog",
        "zmień nazwę pliku old.txt na new.txt",
        "sprawdź rozmiar pliku database.db",
        "utwórz katalog nowy_projekt",
        "pokaż ostatnie 10 linii pliku access.log",
        "znajdź pliki większe niż 100MB",
        "pokaż użycie CPU i pamięci",
        "sprawdź działające procesy",
        "pokaż dysk twardy i użycie miejsca",
        "sprawdź połączenie z google.com",
        "pokaż adres IP komputera",
        "znajdź otwarte porty na localhost",
        "zabij proces o PID 1234",
        "uruchom proces w tle",
        "znajdź procesy python",
        "uruchom skrypt start.sh",
        "zatrzymaj usługę nginx",
        "uruchom ponownie serwer apache",
        "pokaż drzewo procesów",
        "znajdź procesy użytkownika tom",
        "uruchom monitor systemowy",
        "sprawdź status usługi docker",
        "uruchom testy jednostkowe",
        "zbuduj projekt z Maven",
        "zainstaluj zależności npm",
        "uruchom serwer deweloperski",
        "sprawdź wersję node.js",
        "uruchom linter na kodzie",
        "pokaż logi aplikacji",
        "uruchom debugger",
        "czyszczenie cache projektu",
        "generuj dokumentację API",
        "sprawdź kto jest zalogowany",
        "pokaż historię logowań",
        "znajdź otwarte sesje SSH",
        "sprawdź uprawnienia pliku config.conf",
        "znajdź pliki z uprawnieniami SUID",
        "pokaż firewall rules",
        "sprawdź logi bezpieczeństwa",
        "znajdź podejrzane procesy",
        "sprawdź zainstalowane pakiety",
        "pokaż użytkowników w systemie",
        "utwórz backup katalogu /home/user/documents",
        "skompresuj pliki do archiwum tar.gz",
        "skopiuj backup na serwer zdalny",
        "sprawdź integralność backupu",
        "usun stare backupi starsze niż 7 dni",
        "pokaż rozmiar backupu",
        "odtwórz plik z backupu",
        "zaplanuj automatyczny backup",
        "sprawdź status backupu",
        "czyść cache systemowy",
        "sprawdź miejsce na dysku",
        "znajdź duże pliki do usunięcia",
        "uruchom aktualizację systemu",
        "sprawdź logi systemowe",
        "oczyszczanie tymczasowych plików",
        "sprawdź zdrowie dysku",
        "uruchom defragmentację",
        "sprawdź status usługi cron",
        "znajdź błędy w logach",
    ]
    
    intent_counts = {}
    domain_counts = {}
    
    for query in test_cases:
        try:
            result = await generator.generate(query)
            
            # Pobierz domain i intent
            if hasattr(result, 'result') and hasattr(result.result, 'domain'):
                domain = result.result.domain
                intent = result.result.intent
            elif hasattr(result, 'domain'):
                domain = result.domain
                intent = result.intent
            else:
                domain = "unknown"
                intent = "unknown"
            
            # Zliczaj
            intent_counts[intent] = intent_counts.get(intent, 0) + 1
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
            
            print(f"Query: {query}")
            print(f"  Domain: {domain}")
            print(f"  Intent: {intent}")
            print()
            
        except Exception as e:
            print(f"❌ Error: {query} -> {str(e)}")
            print()
    
    # Podsumowanie
    print_rule(width=50, char="=")
    print("📊 PODSUMOWANIE INTENTÓW")
    print_rule(width=50, char="=")
    print("Domain counts:")
    for domain, count in sorted(domain_counts.items()):
        print(f"  {domain}: {count}")
    
    print("\nIntent counts:")
    for intent, count in sorted(intent_counts.items()):
        print(f"  {intent}: {count}")


if __name__ == "__main__":
    asyncio.run(debug_intents())
