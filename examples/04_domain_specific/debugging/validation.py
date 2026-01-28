"""
NLP2CMD - Walidacja i porównanie komend shell

System do walidacji jakości generowanych komend shell
przez porównanie z oczekiwanymi wynikami.
"""

import asyncio
import sys
import time
from pathlib import Path
from typing import Dict, List, Tuple
from dataclasses import dataclass
from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator

sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_rule, rule_line


@dataclass
class CommandTest:
    """Test case dla komendy shell."""
    query: str
    expected_command: str
    description: str
    category: str


class ShellCommandValidator:
    """Walidator komend shell."""
    
    def __init__(self):
        self.generator = HybridThermodynamicGenerator()
        self.results = []
    
    def get_test_cases(self) -> List[CommandTest]:
        """Zwróć listę przypadków testowych."""
        return [
            # Operacje na plikach
            CommandTest(
                "znajdź pliki z rozszerzeniem .py w katalogu src",
                "find src -name '*.py' -type f",
                "Wyszukiwanie plików Python",
                "pliki"
            ),
            CommandTest(
                "skopiuj plik config.json do backup/",
                "cp config.json backup/",
                "Kopiowanie pliku",
                "pliki"
            ),
            CommandTest(
                "usuń wszystkie pliki .tmp",
                "find . -name '*.tmp' -delete",
                "Usuwanie plików tymczasowych",
                "pliki"
            ),
            CommandTest(
                "pokaż zawartość pliku /var/log/syslog",
                "cat /var/log/syslog",
                "Wyświetlanie zawartości pliku",
                "pliki"
            ),
            CommandTest(
                "zmień nazwę pliku old.txt na new.txt",
                "mv old.txt new.txt",
                "Zmiana nazwy pliku",
                "pliki"
            ),
            CommandTest(
                "sprawdź rozmiar pliku database.db",
                "du -h database.db",
                "Sprawdzanie rozmiaru pliku",
                "pliki"
            ),
            CommandTest(
                "znajdź pliki większe niż 100MB",
                "find . -size +100M",
                "Wyszukiwanie dużych plików",
                "pliki"
            ),
            CommandTest(
                "utwórz katalog nowy_projekt",
                "mkdir nowy_projekt",
                "Tworzenie katalogu",
                "pliki"
            ),
            CommandTest(
                "pokaż ostatnie 10 linii pliku access.log",
                "tail -10 access.log",
                "Wyświetlanie końca pliku",
                "pliki"
            ),
            CommandTest(
                "znajdź pliki zmodyfikowane w ostatnim tygodniu",
                "find . -mtime -7",
                "Wyszukiwanie ostatnio zmodyfikowanych",
                "pliki"
            ),
            
            # Monitorowanie systemu
            CommandTest(
                "pokaż użycie CPU i pamięci",
                "top -n 1",
                "Monitorowanie zasobów systemowych",
                "system"
            ),
            CommandTest(
                "sprawdź działające procesy",
                "ps aux",
                "Lista procesów",
                "system"
            ),
            CommandTest(
                "znajdź procesy zużywające najwięcej pamięci",
                "ps aux --sort=-%mem | head -10",
                "Procesy z najwyższym użyciem pamięci",
                "system"
            ),
            CommandTest(
                "pokaż dysk twardy i użycie miejsca",
                "df -h",
                "Informacje o dysku",
                "system"
            ),
            CommandTest(
                "sprawdź temperaturę procesora",
                "sensors",
                "Temperatura sprzętu",
                "system"
            ),
            CommandTest(
                "pokaż otwarte porty sieciowe",
                "netstat -tuln",
                "Otwarte porty",
                "sieć"
            ),
            CommandTest(
                "znajdź procesy nasłuchujące na porcie 8080",
                "lsof -i :8080",
                "Procesy na porcie 8080",
                "sieć"
            ),
            CommandTest(
                "sprawdź load average systemu",
                "uptime",
                "Obciążenie systemu",
                "system"
            ),
            CommandTest(
                "pokaż historię poleceń użytkownika",
                "history | tail -10",
                "Historia poleceń",
                "system"
            ),
            CommandTest(
                "znajdź zombie procesy",
                "ps aux | awk '{print $8}' | grep -v '^\\[' | sort | uniq -c",
                "Procesy zombie",
                "system"
            ),
            
            # Operacje sieciowe
            CommandTest(
                "sprawdź połączenie z google.com",
                "ping -c 4 google.com",
                "Test łączności",
                "sieć"
            ),
            CommandTest(
                "pokaż adres IP komputera",
                "ip addr show",
                "Adres IP",
                "sieć"
            ),
            CommandTest(
                "znajdź otwarte porty na localhost",
                "netstat -tuln | grep LISTEN",
                "Porty nasłuchujące",
                "sieć"
            ),
            CommandTest(
                "sprawdź prędkość internetu",
                "curl -o /dev/null -s -w '%{time_total}' http://speedtest.net",
                "Prędkość internetu",
                "sieć"
            ),
            CommandTest(
                "pokaż tabelę routingu",
                "ip route",
                "Tabela routingu",
                "sieć"
            ),
            CommandTest(
                "znajdź urządzenia w lokalnej sieci",
                "nmap -sn 192.168.1.0/24",
                "Skanowanie sieci",
                "sieć"
            ),
            CommandTest(
                "sprawdź ping do serwera 8.8.8.8",
                "ping -c 1 8.8.8.8",
                "Ping do serwera DNS",
                "sieć"
            ),
            CommandTest(
                "pokaż aktywne połączenia sieciowe",
                "ss -tulpn",
                "Aktywne połączenia",
                "sieć"
            ),
            CommandTest(
                "znajdź proces używający portu 22",
                "lsof -i :22",
                "Procesy na porcie SSH",
                "sieć"
            ),
            CommandTest(
                "sprawdź konfigurację sieciową",
                "ifconfig -a",
                "Konfiguracja interfejsów sieciowych",
                "sieć"
            ),
            
            # Zarządzanie procesami
            CommandTest(
                "zabij proces o PID 1234",
                "kill -9 1234",
                "Zabicie procesu",
                "procesy"
            ),
            CommandTest(
                "uruchom proces w tle",
                "nohup python script.py &",
                "Uruchomienie w tle",
                "procesy"
            ),
            CommandTest(
                "znajdź procesy python",
                "ps aux | grep python",
                "Procesy Python",
                "procesy"
            ),
            CommandTest(
                "uruchom skrypt start.sh",
                "./start.sh",
                "Uruchomienie skryptu",
                "procesy"
            ),
            CommandTest(
                "zatrzymaj usługę nginx",
                "systemctl stop nginx",
                "Zatrzymanie usługi",
                "procesy"
            ),
            CommandTest(
                "uruchom ponownie serwer apache",
                "systemctl restart apache2",
                "Restart usługi",
                "procesy"
            ),
            CommandTest(
                "pokaż drzewo procesów",
                "pstree",
                "Drzewo procesów",
                "procesy"
            ),
            CommandTest(
                "znajdź procesy użytkownika tom",
                "ps aux | grep tom",
                "Procesy użytkownika",
                "procesy"
            ),
            CommandTest(
                "uruchom monitor systemowy",
                "htop",
                "Monitor systemowy",
                "procesy"
            ),
            CommandTest(
                "sprawdź status usługi docker",
                "systemctl status docker",
                "Status usługi Docker",
                "procesy"
            ),
            
            # Narzędzia deweloperskie
            CommandTest(
                "uruchom testy jednostkowe",
                "pytest tests/",
                "Uruchomienie testów",
                "dev"
            ),
            CommandTest(
                "zbuduj projekt z Maven",
                "mvn clean install",
                "Budowanie Maven",
                "dev"
            ),
            CommandTest(
                "zainstaluj zależności npm",
                "npm install",
                "Instalacja zależności",
                "dev"
            ),
            CommandTest(
                "uruchom serwer deweloperski",
                "python manage.py runserver",
                "Serwer deweloperski",
                "dev"
            ),
            CommandTest(
                "sprawdź wersję node.js",
                "node --version",
                "Wersja Node.js",
                "dev"
            ),
            CommandTest(
                "uruchom linter na kodzie",
                "pylint src/",
                "Analiza kodu",
                "dev"
            ),
            CommandTest(
                "pokaż logi aplikacji",
                "tail -f app.log",
                "Logi aplikacji",
                "dev"
            ),
            CommandTest(
                "uruchom debugger",
                "python -m pdb script.py",
                "Debugger",
                "dev"
            ),
            CommandTest(
                "czyszczenie cache projektu",
                "rm -rf __pycache__",
                "Czyszczenie cache",
                "dev"
            ),
            CommandTest(
                "generuj dokumentację API",
                "sphinx-build -b html docs/",
                "Generowanie dokumentacji",
                "dev"
            ),
            
            # Bezpieczeństwo
            CommandTest(
                "sprawdź kto jest zalogowany",
                "who",
                "Zalogowani użytkownicy",
                "bezpieczeństwo"
            ),
            CommandTest(
                "pokaż historię logowań",
                "last -n 10",
                "Historia logowań",
                "bezpieczeństwo"
            ),
            CommandTest(
                "znajdź otwarte sesje SSH",
                "who",
                "Sesje SSH",
                "bezpieczeństwo"
            ),
            CommandTest(
                "sprawdź uprawnienia pliku config.conf",
                "ls -la config.conf",
                "Uprawnienia pliku",
                "bezpieczeństwo"
            ),
            CommandTest(
                "znajdź pliki z uprawnieniami SUID",
                "find / -perm -4000 -type f",
                "Pliki SUID",
                "bezpieczeństwo"
            ),
            CommandTest(
                "pokaż firewall rules",
                "iptables -L",
                "Reguły firewall",
                "bezpieczeństwo"
            ),
            CommandTest(
                "sprawdź logi bezpieczeństwa",
                "tail -n 100 /var/log/auth.log",
                "Logi bezpieczeństwa",
                "bezpieczeństwo"
            ),
            CommandTest(
                "znajdź podejrzane procesy",
                "ps aux | grep -v '\\['",
                "Podejrzane procesy",
                "bezpieczeństwo"
            ),
            CommandTest(
                "sprawdź zainstalowane pakiety",
                "dpkg -l | grep -i security",
                "Zainstalowane pakiety",
                "bezpieczeństwo"
            ),
            CommandTest(
                "pokaż użytkowników w systemie",
                "cat /etc/passwd",
                "Użytkownicy systemu",
                "bezpieczeństwo"
            ),
            
            # Backup i archiwizacja
            CommandTest(
                "utwórz backup katalogu /home/user/documents",
                "tar -czf backup.tar.gz /home/user/documents",
                "Tworzenie backupu",
                "backup"
            ),
            CommandTest(
                "skompresuj pliki do archiwum tar.gz",
                "tar -czf archive.tar.gz .",
                "Kompresja do archiwum",
                "backup"
            ),
            CommandTest(
                "skopiuj backup na serwer zdalny",
                "rsync -av /src/ /dst/",
                "Kopiowanie zdalne",
                "backup"
            ),
            CommandTest(
                "sprawdź integralność backupu",
                "md5sum backup.tar.gz",
                "Weryfikacja integralności",
                "backup"
            ),
            CommandTest(
                "usun stare backupi starsze niż 7 dni",
                "find /backup -mtime +7 -delete",
                "Usuwanie starych backupów",
                "backup"
            ),
            CommandTest(
                "pokaż rozmiar backupu",
                "du -sh backup.tar.gz",
                "Rozmiar backupu",
                "backup"
            ),
            CommandTest(
                "odtwórz plik z backupu",
                "tar -xzf backup.tar.gz file.txt",
                "Odtworzenie z backupu",
                "backup"
            ),
            CommandTest(
                "zaplanuj automatyczny backup",
                "crontab -l",
                "Harmonogram backup",
                "backup"
            ),
            CommandTest(
                "sprawdź status backupu",
                "ls -la /backup/",
                "Status backupu",
                "backup"
            ),
            
            # Konserwacja systemu
            CommandTest(
                "czyść cache systemowy",
                "apt update && apt upgrade -y",
                "Aktualizacja systemu",
                "konserwacja"
            ),
            CommandTest(
                "sprawdź miejsce na dysku",
                "df -h",
                "Miejsce na dysku",
                "konserwacja"
            ),
            CommandTest(
                "znajdź duże pliki do usunięcia",
                "find /tmp -type f -atime +7 -delete",
                "Usuwanie starych plików",
                "konserwacja"
            ),
            CommandTest(
                "uruchom aktualizację systemu",
                "apt update && apt upgrade -y",
                "Aktualizacja systemu",
                "konserwacja"
            ),
            CommandTest(
                "sprawdź logi systemowe",
                "tail -n 50 /var/log/syslog",
                "Logi systemowe",
                "konserwacja"
            ),
            CommandTest(
                "oczyszczanie tymczasowych plików",
                "rm -rf /tmp/*",
                "Czyszczenie /tmp",
                "konserwacja"
            ),
            CommandTest(
                "sprawdź zdrowie dysku",
                "fsck -n /dev/sda1",
                "Sprawdzanie dysku",
                "konserwacja"
            ),
            CommandTest(
                "uruchom defragmentację",
                "defrag /dev/sda1",
                "Defragmentacja dysku",
                "konserwacja"
            ),
            CommandTest(
                "sprawdź status usługi cron",
                "systemctl status cron",
                "Status cron",
                "konserwacja"
            ),
            CommandTest(
                "znajdź błędy w logach",
                "grep -i error /var/log/syslog",
                "Błędy w logach",
                "konserwacja"
            ),
        ]
    
    async def validate_command(self, test: CommandTest) -> Dict[str, any]:
        """Waliduje pojedynczą komendę."""
        start_time = time.time()
        
        try:
            result = await self.generator.generate(test.query)
            elapsed = (time.time() - start_time) * 1000
            
            # Pobierz komendę z wyniku
            if hasattr(result, 'result') and hasattr(result.result, 'command'):
                actual_command = result.result.command
            elif hasattr(result, 'command'):
                actual_command = result.command
            else:
                actual_command = str(result)
            
            # Porównaj z oczekiwaną komendą
            is_exact_match = actual_command == test.expected_command
            is_similar = self._calculate_similarity(actual_command, test.expected_command)
            
            return {
                'query': test.query,
                'expected': test.expected_command,
                'actual': actual_command,
                'is_exact_match': is_exact_match,
                'similarity': is_similar,
                'latency_ms': elapsed,
                'category': test.category,
                'description': test.description,
                'success': is_exact_match or is_similar > 0.8,
            }
        except Exception as e:
            return {
                'query': test.query,
                'expected': test.expected_command,
                'actual': f"ERROR: {str(e)}",
                'is_exact_match': False,
                'similarity': 0.0,
                'latency_ms': 0,
                'category': test.category,
                'description': test.description,
                'success': False,
                'error': str(e),
            }
    
    def _calculate_similarity(self, actual: str, expected: str) -> float:
        """Oblicz podobieństwo między komendami."""
        if not actual or not expected:
            return 0.0
        
        # Podziel komendy na słowa
        actual_words = set(actual.split())
        expected_words = set(expected.split())
        
        if not expected_words:
            return 0.0
        
        # Oblicz wspólne słowa
        common_words = actual_words & expected_words
        
        # Jaccard similarity
        return len(common_words) / len(expected_words)
    
    async def validate_all(self) -> List[Dict[str, any]]:
        """Waliduje wszystkie komendy."""
        test_cases = self.get_test_cases()
        results = []
        
        print("🔍 Walidacja komend shell...")
        print(f"Liczba testów: {len(test_cases)}")
        print_rule(width=70, char="=")
        
        for i, test in enumerate(test_cases, 1):
            print(f"\n[{i:2d}/{len(test_cases)}] {test.category}: {test.description}")
            print(f"Query: {test.query}")
            print(f"Expected: {test.expected_command}")
            
            result = await self.validate_command(test)
            results.append(result)
            
            status = "✅" if result['success'] else "❌"
            similarity_pct = result['similarity'] * 100
            
            print(f"Actual: {result['actual']}")
            print(f"{status} Similarity: {similarity_pct:.1f}% | Latency: {result['latency_ms']:.1f}ms")
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
        
        return results
    
    def generate_report(self, results: List[Dict[str, any]]) -> str:
        """Generuj raport walidacji."""
        total_tests = len(results)
        exact_matches = sum(1 for r in results if r['is_exact_match'])
        similar_matches = sum(1 for r in results if r['similarity'] > 0.8)
        successful_tests = sum(1 for r in results if r['success'])
        
        avg_latency = sum(r['latency_ms'] for r in results) / total_tests
        
        # Statystyki per kategorii
        categories = {}
        for result in results:
            cat = result['category']
            if cat not in categories:
                categories[cat] = {'total': 0, 'success': 0, 'exact': 0, 'avg_latency': 0}
            categories[cat]['total'] += 1
            categories[cat]['success'] += 1 if result['success'] else 0
            categories[cat]['exact'] += 1 if result['is_exact_match'] else 0
            categories[cat]['avg_latency'] += result['latency_ms']
        
        # Oblicz średnie dla kategorii
        for cat in categories:
            categories[cat]['avg_latency'] /= categories[cat]['total']
        
        report = f"""
📊 RAPORT WALIDACJI KOMEND SHELL
{rule_line(width=70, char="=")}
Podsumowanie:
- Łącznie testów: {total_tests}
- Dokładne trafienia: {exact_matches} ({exact_matches/total_tests*100:.1f}%)
- Podobne trafienia: {similar_matches} ({similar_matches/total_tests*100:.1f}%)
- Sukcesy ogólnie: {successful_tests} ({successful_tests/total_tests*100:.1f}%)
- Średnia latencja: {avg_latency:.1f}ms

Statystyki per kategorii:
"""
        
        for cat, stats in sorted(categories.items()):
            success_rate = stats['success'] / stats['total'] * 100
            exact_rate = stats['exact'] / stats['total'] * 100
            report += f"- {cat}: {stats['success']}/{stats['total']} ({success_rate:.1f}%) | "
            report += f"Dokładne: {stats['exact']}/{stats['total']} ({exact_rate:.1f}%) | "
            report += f"Śr. latencja: {stats['avg_latency']:.1f}ms\n"
        
        # Najgorsze wyniki
        worst_results = sorted(results, key=lambda x: x['similarity'])[:5]
        report += f"\nNajgorsze wyniki (najmniej podobne):\n"
        for i, result in enumerate(worst_results, 1):
            report += f"{i}. {result['query']}\n"
            report += f"   Expected: {result['expected']}\n"
            report += f"   Actual: {result['actual']}\n"
            report += f"   Similarity: {result['similarity']*100:.1f}%\n"
        
        # Najlepsze wyniki
        best_results = sorted(results, key=lambda x: x['similarity'], reverse=True)[:5]
        report += f"\nNajlepsze wyniki (najbardziej podobne):\n"
        for i, result in enumerate(best_results, 1):
            report += f"{i}. {result['query']}\n"
            report += f"   Expected: {result['expected']}\n"
            report += f"   Actual: {result['actual']}\n"
            report += f"   Similarity: {result['similarity']*100:.1f}%\n"
        
        return report


async def main():
    """Uruchom walidację komend shell."""
    print("🔍 NLP2CMD - Walidacja komend shell")
    print("Porównanie generowanych komend z oczekiwanymi wynikami")
    print_rule(width=70, char="=")
    
    validator = ShellCommandValidator()
    results = await validator.validate_all()
    
    print_rule(width=70, char="=", leading_newline=True)
    print(validator.generate_report(results))
    print_rule(width=70, char="=")
    
    # Zapisz wyniki do pliku
    with open('shell_validation_report.txt', 'w') as f:
        f.write(validator.generate_report(results))
    
    print(f"\n📄 Raport zapisany do: shell_validation_report.txt")


if __name__ == "__main__":
    asyncio.run(main())
