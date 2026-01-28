#!/usr/bin/env python3
"""
Test shell improvements - sprawdzenie czy poprawki działają
"""

import asyncio
import sys
from pathlib import Path

# Dodaj ścieżkę do importów
sys.path.append(str(Path(__file__).parent.parent.parent / "src"))
sys.path.append(str(Path(__file__).resolve().parents[1]))

from _demo_helpers import print_rule

from nlp2cmd.generation.thermodynamic import HybridThermodynamicGenerator


async def test_shell_improvements():
    """Test kilka konkretnych przypadków shell."""
    print("🔧 Testowanie poprawek shell DSL")
    print_rule(width=50, char="=")
    
    generator = HybridThermodynamicGenerator()
    
    # Test cases
    test_cases = [
        ("znajdź pliki z rozszerzeniem .py", "find . -name '*.py' -type f"),
        ("skopiuj plik config.json do backup/", "cp config.json backup/"),
        ("usuń wszystkie pliki .tmp", "find . -name '*.tmp' -delete"),
        ("pokaż zawartość pliku /var/log/syslog", "cat /var/log/syslog"),
        ("zmień nazwę pliku old.txt na new.txt", "mv old.txt new.txt"),
        ("sprawdź rozmiar pliku database.db", "du -h database.db"),
        ("utwórz katalog nowy_projekt", "mkdir nowy_projekt"),
        ("pokaż ostatnie 10 linii pliku access.log", "tail -10 access.log"),
        ("znajdź pliki większe niż 100MB", "find . -size +100M"),
        ("znajdź pliki zmodyfikowane w ostatnim tygodniu", "find . -mtime -7"),
        ("pokaż użycie CPU i pamięci", "top -n 1"),
        ("sprawdź działające procesy", "ps aux"),
        ("znajdź procesy zużywające najwięcej pamięci", "ps aux --sort=-%mem | head -10"),
        ("pokaż dysk twardy i użycie miejsca", "df -h"),
        ("sprawdź połączenie z google.com", "ping -c 4 google.com"),
        ("pokaż adres IP komputera", "ip addr show"),
        ("znajdź otwarte porty na localhost", "netstat -tuln | grep LISTEN"),
        ("zabij proces o PID 1234", "kill -9 1234"),
        ("uruchom proces w tle", "nohup python script.py &"),
        ("znajdź procesy python", "ps aux | grep python"),
        ("uruchom skrypt start.sh", "./start.sh"),
        ("zatrzymaj usługę nginx", "systemctl stop nginx"),
        ("uruchom ponownie serwer apache", "systemctl restart apache2"),
        ("pokaż drzewo procesów", "pstree"),
        ("znajdź procesy użytkownika tom", "ps aux | grep tom"),
        ("uruchom monitor systemowy", "htop"),
        ("sprawdź status usługi docker", "systemctl status docker"),
        ("uruchom testy jednostkowe", "pytest tests/"),
        ("zbuduj projekt z Maven", "mvn clean install"),
        ("zainstaluj zależności npm", "npm install"),
        ("uruchom serwer deweloperski", "python manage.py runserver"),
        ("sprawdź wersję node.js", "node --version"),
        ("uruchom linter na kodzie", "pylint src/"),
        ("pokaż logi aplikacji", "tail -f app.log"),
        ("uruchom debugger", "python -m pdb script.py"),
        ("czyszczenie cache projektu", "rm -rf __pycache__"),
        ("generuj dokumentację API", "sphinx-build -b html docs/"),
        ("sprawdź kto jest zalogowany", "who"),
        ("pokaż historię logowań", "last -n 10"),
        ("znajdź otwarte sesje SSH", "who"),
        ("sprawdź uprawnienia pliku config.conf", "ls -la config.conf"),
        ("znajdź pliki z uprawnieniami SUID", "find / -perm -4000 -type f"),
        ("pokaż firewall rules", "iptables -L"),
        ("sprawdź logi bezpieczeństwa", "tail -n 100 /var/log/auth.log"),
        ("znajdź podejrzane procesy", "ps aux | grep -v '\\['"),
        ("sprawdź zainstalowane pakiety", "dpkg -l | grep -i security"),
        ("pokaż użytkowników w systemie", "cat /etc/passwd"),
        ("utwórz backup katalogu /home/user/documents", "tar -czf backup.tar.gz /home/user/documents"),
        ("skompresuj pliki do archiwum tar.gz", "tar -czf archive.tar.gz ."),
        ("skopiuj backup na serwer zdalny", "rsync -av /src/ /dst/"),
        ("sprawdź integralność backupu", "md5sum backup.tar.gz"),
        ("usun stare backupi starsze niż 7 dni", "find /backup -mtime +7 -delete"),
        ("pokaż rozmiar backupu", "du -sh backup.tar.gz"),
        ("odtwórz plik z backupu", "tar -xzf backup.tar.gz file.txt"),
        ("zaplanuj automatyczny backup", "crontab -l"),
        ("sprawdź status backupu", "ls -la /backup/"),
        ("czyść cache systemowy", "apt update && apt upgrade -y"),
        ("sprawdź miejsce na dysku", "df -h"),
        ("znajdź duże pliki do usunięcia", "find /tmp -type f -atime +7 -delete"),
        ("uruchom aktualizację systemu", "apt update && apt upgrade -y"),
        ("sprawdź logi systemowe", "tail -n 50 /var/log/syslog"),
        ("oczyszczanie tymczasowych plików", "rm -rf /tmp/*"),
        ("sprawdź zdrowie dysku", "fsck -n /dev/sda1"),
        ("uruchom defragmentację", "defrag /dev/sda1"),
        ("sprawdź status usługi cron", "systemctl status cron"),
        ("znajdź błędy w logach", "grep -i error /var/log/syslog"),
    ]
    
    exact_matches = 0
    similar_matches = 0
    shell_matches = 0
    sql_matches = 0
    unknown_matches = 0
    
    print(f"Testowanie {len(test_cases)} przypadków...\n")
    
    for i, (query, expected) in enumerate(test_cases, 1):
        try:
            result = await generator.generate(query)
            
            # Pobierz komendę z wyniku
            if hasattr(result, 'result') and hasattr(result.result, 'command'):
                actual = result.result.command
                domain = result.result.domain
            elif hasattr(result, 'command'):
                actual = result.command
                domain = result.domain
            else:
                actual = str(result)
                domain = "unknown"
            
            # Sprawdź trafność
            is_exact = actual == expected
            is_similar = expected in actual or actual in expected
            
            if domain == 'shell':
                shell_matches += 1
            elif domain == 'sql':
                sql_matches += 1
            elif domain == 'unknown':
                unknown_matches += 1
                
            if is_exact:
                exact_matches += 1
                similar_matches += 1
            elif is_similar:
                similar_matches += 1
            
            status = "✅" if is_exact else "⚠️" if is_similar else "❌"
            domain_icon = "🐚" if domain == 'shell' else "🗄️" if domain == 'sql' else "❓" if domain == 'unknown' else "🔧"
            
            print(f"{i:2d}. {status} {domain_icon} {query[:40]:<40}")
            print(f"     Expected: {expected}")
            print(f"     Actual:   {actual}")
            print(f"     Domain:   {domain}")
            print()
            
        except Exception as e:
            print(f"❌ Error: {query} -> {str(e)}")
            print()
    
    # Podsumowanie
    print_rule(width=50, char="=")
    print("📊 PODSUMOWANIE TESTU")
    print_rule(width=50, char="=")
    print(f"Łącznie testów: {len(test_cases)}")
    print(f"Dokładne trafienia: {exact_matches} ({exact_matches/len(test_cases)*100:.1f}%)")
    print(f"Podobne trafienia: {similar_matches} ({similar_matches/len(test_cases)*100:.1f}%)")
    print(f"Shell domena: {shell_matches} ({shell_matches/len(test_cases)*100:.1f}%)")
    print(f"SQL domena: {sql_matches} ({sql_matches/len(test_cases)*100:.1f}%)")
    print(f"Unknown domena: {unknown_matches} ({unknown_matches/len(test_cases)*100:.1f}%)")
    
    if shell_matches > sql_matches:
        print("\n✅ Poprawki działają! Shell dominuje nad SQL")
    else:
        print("\n❌ Problem: SQL nadal dominuje nad Shell")


if __name__ == "__main__":
    asyncio.run(test_shell_improvements())
