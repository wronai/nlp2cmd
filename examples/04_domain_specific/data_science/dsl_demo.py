"""
NLP2CMD - Przykłady bezpośrednich komend DSL w shell

Demonstruje użycie NLP2CMD do generowania konkretnych komend shell
bezpośrednio z języka naturalnego.
"""

import asyncio
import time
from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator


def print_result(query, result, elapsed):
    """Helper function to print results for both DSL and Thermodynamic sources."""
    print(f"\n📝 Query: {query}")
    
    # Handle both DSL and Thermodynamic results
    if result['source'] == 'dsl':
        print(f"   Command: {result['result'].command}")
    else:
        print(f"   Solution: {result['result'].decoded_output}")
    
    print(f"   ⚡ Latency: {elapsed:.1f}ms")


async def demo_file_operations():
    """Demonstracja operacji na plikach."""
    print("=" * 70)
    print("  Shell DSL - Operacje na plikach")
    print("=" * 70)
    
    generator = HybridThermodynamicGenerator()
    
    # Operacje na plikach
    file_queries = [
        "znajdź pliki z rozszerzeniem .py w katalogu src",
        "skopiuj plik config.json do backup/",
        "usuń wszystkie pliki .tmp",
        "pokaż zawartość pliku /var/log/syslog",
        "zmień nazwę pliku old.txt na new.txt",
        "sprawdź rozmiar pliku database.db",
        "znajdź pliki większe niż 100MB",
        "utwórz katalog nowy_projekt",
        "pokaż ostatnie 10 linii pliku access.log",
        "znajdź pliki zmodyfikowane w ostatnim tygodniu",
    ]
    
    print("📁 Operacje na plikach i katalogach:")
    for query in file_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)


async def demo_system_monitoring():
    """Demonstracja monitoringu systemu."""
    print("\n" + "=" * 70)
    print("  Shell DSL - Monitorowanie systemu")
    print("=" * 70)
    
    generator = HybridThermodynamicGenerator()
    
    # Monitorowanie systemu
    monitoring_queries = [
        "pokaż użycie CPU i pamięci",
        "sprawdź działające procesy",
        "znajdź procesy zużywające najwięcej pamięci",
        "pokaż dysk twardy i użycie miejsca",
        "sprawdź temperaturę procesora",
        "pokaż otwarte porty sieciowe",
        "znajdź procesy nasłuchujące na porcie 8080",
        "sprawdź load average systemu",
        "pokaż historię poleceń użytkownika",
        "znajdź zombie procesy",
    ]
    
    print("🖥️ Monitorowanie systemu:")
    for query in monitoring_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)


async def demo_network_operations():
    """Demonstracja operacji sieciowych."""
    print("\n" + "=" * 70)
    print("  Shell DSL - Operacje sieciowe")
    print("=" * 70)
    
    generator = HybridThermodynamicGenerator()
    
    # Operacje sieciowe
    network_queries = [
        "sprawdź połączenie z google.com",
        "pokaż adres IP komputera",
        "znajdź otwarte porty na localhost",
        "sprawdź prędkość internetu",
        "pokaż tabelę routingu",
        "znajdź urządzenia w lokalnej sieci",
        "sprawdź ping do serwera 8.8.8.8",
        "pokaż aktywne połączenia sieciowe",
        "znajdź proces używający portu 22",
        "sprawdź konfigurację sieciową",
    ]
    
    print("🌐 Operacje sieciowe:")
    for query in network_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)


async def demo_process_management():
    """Demonstracja zarządzania procesami."""
    print("\n" + "=" * 70)
    print("  Shell DSL - Zarządzanie procesami")
    print("=" * 70)
    
    generator = HybridThermodynamicGenerator()
    
    # Zarządzanie procesami
    process_queries = [
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
    ]
    
    print("⚙️ Zarządzanie procesami:")
    for query in process_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)


async def demo_development_tools():
    """Demonstracja narzędzi deweloperskich."""
    print("\n" + "=" * 70)
    print("  Shell DSL - Narzędzia deweloperskie")
    print("=" * 70)
    
    generator = HybridThermodynamicGenerator()
    
    # Narzędzia deweloperskie
    dev_queries = [
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
    ]
    
    print("💻 Narzędzia deweloperskie:")
    for query in dev_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)


async def demo_security_operations():
    """Demonstracja operacji bezpieczeństwa."""
    print("\n" + "=" * 70)
    print("  Shell DSL - Operacje bezpieczeństwa")
    print("=" * 70)
    
    generator = HybridThermodynamicGenerator()
    
    # Operacje bezpieczeństwa
    security_queries = [
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
    ]
    
    print("🔒 Operacje bezpieczeństwa:")
    for query in security_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)


async def demo_backup_operations():
    """Demonstracja operacji backup."""
    print("\n" + "=" * 70)
    print("  Shell DSL - Operacje backup")
    print("=" * 70)
    
    generator = HybridThermodynamicGenerator()
    
    # Operacje backup
    backup_queries = [
        "utwórz backup katalogu /home/user/documents",
        "skompresuj pliki do archiwum tar.gz",
        "skopiuj backup na serwer zdalny",
        "sprawdź integralność backupu",
        "usun stare backupi starsze niż 7 dni",
        "pokaż rozmiar backupu",
        "odtwórz plik z backupu",
        "zaplanuj automatyczny backup",
        "sprawdź status backupu",
        "utwórz przyrostowy backup",
    ]
    
    print("💾 Operacje backup:")
    for query in backup_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)


async def demo_system_maintenance():
    """Demonstracja konserwacji systemu."""
    print("\n" + "=" * 70)
    print("  Shell DSL - Konserwacja systemu")
    print("=" * 70)
    
    generator = HybridThermodynamicGenerator()
    
    # Konserwacja systemu
    maintenance_queries = [
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
    
    print("🔧 Konserwacja systemu:")
    for query in maintenance_queries:
        start_time = time.time()
        result = await generator.generate(query)
        elapsed = (time.time() - start_time) * 1000
        
        print_result(query, result, elapsed)


async def main():
    """Uruchom wszystkie demonstracje komend DSL."""
    print("🚀 NLP2CMD - Przykłady bezpośrednich komend DSL w shell")
    print("=" * 70)
    print("Demonstracja generowania konkretnych komend shell z języka naturalnego")
    print("=" * 70)
    
    start_total = time.time()
    
    await demo_file_operations()
    await demo_system_monitoring()
    await demo_network_operations()
    await demo_process_management()
    await demo_development_tools()
    await demo_security_operations()
    await demo_backup_operations()
    await demo_system_maintenance()
    
    total_time = (time.time() - start_total) * 1000
    
    print("\n" + "=" * 70)
    print("  Podsumowanie demonstracji DSL")
    print("=" * 70)
    print(f"Całkowity czas wykonania: {total_time:.1f}ms")
    print(f"Średnia latencja na zapytanie: ~{total_time/80:.1f}ms")
    print("\n✅ Wszystkie przykłady komend DSL ukończone!")
    print("=" * 70)


if __name__ == "__main__":
    asyncio.run(main())
