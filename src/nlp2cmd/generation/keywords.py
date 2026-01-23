"""
Iteration 1: Rule-Based Intent Detection.

Keyword matching for intent and domain detection without LLM.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional
import json
import os
from pathlib import Path
import re


@dataclass
class DetectionResult:
    """Result of intent detection."""
    
    domain: str
    intent: str
    confidence: float
    matched_keyword: Optional[str] = None


class KeywordIntentDetector:
    """
    Rule-based intent detection using keyword matching.
    
    No LLM needed - uses predefined keyword patterns to detect
    domain (sql, shell, docker, kubernetes) and intent.
    
    Example:
        detector = KeywordIntentDetector()
        result = detector.detect("Pokaż wszystkich użytkowników z tabeli users")
        # result.domain == 'sql', result.intent == 'select'
    """
    
    PATTERNS: dict[str, dict[str, list[str]]] = {
        'sql': {
            'select': [
                'pokaż', 'wyświetl', 'znajdź', 'pobierz', 'select', 'get', 
                'show', 'list', 'fetch', 'query', 'retrieve',
                'z tabeli', 'from table', 'wszystkich', 'all records',
                'dane z', 'data from', 'wszystkie rekordy', 'all records', 'wiersze', 'rows',
            ],
            'select_distinct': [
                'unikalne', 'distinct', 'różne', 'unique values', 'bez duplikatów',
                'without duplicates', 'deduplikuj',
            ],
            'insert': [
                'dodaj', 'wstaw', 'insert', 'create record', 'add record',
                'nowy rekord', 'new record', 'wprowadź', 'enter',
            ],
            'update': [
                'zmień', 'zaktualizuj', 'update', 'modify', 'ustaw',
                'set', 'edit', 'zmiana', 'aktualizacja',
            ],
            'delete': [
                'usuń', 'skasuj', 'delete', 'remove', 'wymaż',
                'kasuj', 'drop record', 'usuń rekord', 'skasuj rekord',
            ],
            'truncate': [
                'truncate', 'wyczyść tabelę', 'clear table', 'usuń wszystko z tabeli',
                'opróżnij tabelę', 'empty table',
            ],
            'aggregate': [
                'policz', 'zsumuj', 'średnia', 'count', 'sum', 'avg',
                'ile jest', 'how many', 'total', 'suma', 'średnio',
                'grupuj', 'group by', 'pogrupuj', 'min', 'max', 'minimum', 'maksimum',
            ],
            # Joins
            'inner_join': [
                'inner join', 'join', 'połącz tabele', 'złącz tabele',
                'join tables', 'łączenie tabel', 'relacja między',
            ],
            'left_join': [
                'left join', 'left outer join', 'lewe złączenie',
                'wszystkie z lewej', 'all from left',
            ],
            'right_join': [
                'right join', 'right outer join', 'prawe złączenie',
                'wszystkie z prawej', 'all from right',
            ],
            'full_join': [
                'full join', 'full outer join', 'pełne złączenie',
                'wszystkie z obu', 'all from both',
            ],
            # DDL
            'create_table': [
                'utwórz tabelę', 'create table', 'nowa tabela', 'new table',
                'stwórz tabelę', 'zdefiniuj tabelę', 'tabela sql', 'sql table',
            ],
            'drop_table': [
                'drop table', 'usuń tabelę', 'skasuj tabelę', 'delete table',
                'zniszcz tabelę',
            ],
            'alter_add_column': [
                'alter table add', 'dodaj kolumnę', 'add column', 'nowa kolumna',
                'rozszerz tabelę',
            ],
            'alter_drop_column': [
                'alter table drop', 'usuń kolumnę', 'drop column', 'skasuj kolumnę',
            ],
            'alter_rename_column': [
                'rename column', 'zmień nazwę kolumny', 'przemianuj kolumnę',
            ],
            # Indexes
            'create_index': [
                'create index', 'utwórz indeks', 'dodaj indeks', 'new index',
                'zindeksuj', 'index on',
            ],
            'drop_index': [
                'drop index', 'usuń indeks', 'skasuj indeks', 'delete index',
            ],
            # Views
            'create_view': [
                'create view', 'utwórz widok', 'nowy widok', 'zdefiniuj widok',
            ],
            'drop_view': [
                'drop view', 'usuń widok', 'skasuj widok',
            ],
            # Window functions
            'window_row_number': [
                'row_number', 'numer wiersza', 'row number', 'numeruj wiersze',
                'ponumeruj',
            ],
            'window_rank': [
                'rank', 'ranking', 'pozycja', 'uszereguj', 'dense_rank',
            ],
            'window_lag': [
                'lag', 'poprzednia wartość', 'previous value', 'wartość wcześniejsza',
            ],
            'window_lead': [
                'lead', 'następna wartość', 'next value', 'wartość późniejsza',
            ],
            # Transactions
            'begin': [
                'begin', 'start transaction', 'rozpocznij transakcję',
            ],
            'commit': [
                'commit', 'zatwierdź', 'zatwierdź transakcję',
            ],
            'rollback': [
                'rollback', 'cofnij', 'wycofaj transakcję', 'anuluj transakcję',
            ],
            # Utility
            'describe': [
                'describe', 'opisz tabelę', 'struktura tabeli', 'table structure',
                'schema tabeli', 'kolumny tabeli',
            ],
            'show_tables': [
                'show tables', 'pokaż tabele', 'lista tabel', 'list tables',
                'jakie tabele', 'what tables',
            ],
            'show_databases': [
                'show databases', 'pokaż bazy', 'lista baz', 'list databases',
                'jakie bazy', 'what databases',
            ],
            'explain': [
                'explain', 'plan zapytania', 'query plan', 'analiza zapytania',
                'optymalizacja', 'performance',
            ],
        },
        'shell': {
            'find': [
                'znajdź plik', 'szukaj plik', 'find files', 'search files',
                'locate', 'wyszukaj', 'gdzie jest', 'where is',
                'find python', 'find log', 'znajdź pliki z rozszerzeniem',
                'znajdź pliki większe niż', 'znajdź pliki zmodyfikowane',
                'pokaż zawartość pliku', 'wyświetl plik', 'cat plik', 'odczytaj plik',
                'pokaż ostatnie linii pliku', 'tail plik', 'koniec pliku'
            ],
            'count_files': [
                'ile plików',
                'ile jest plików',
                'ile plikow',
                'ile jest plikow',
                'policz pliki',
                'zlicz pliki',
                'count files',
                'how many files',
                'number of files',
            ],
            'count_dirs': [
                'ile folderów',
                'ile jest folderów',
                'ile folderow',
                'ile jest folderow',
                'ile katalogów',
                'ile jest katalogów',
                'ile katalogow',
                'ile jest katalogow',
                'policz foldery',
                'zlicz foldery',
                'policz katalogi',
                'zlicz katalogi',
                'count directories',
                'how many directories',
                'number of directories',
                'count folders',
                'how many folders',
                'number of folders',
            ],
            'list': [
                'lista plików', 'pokaż katalog', 'ls', 'dir', 'wylistuj',
                'zawartość katalogu', 'directory contents', 'folder contents',
                'pokaż pliki', 'listuj pliki', 'wypisz pliki'
            ],
            'process': [
                'procesy', 'ps', 'uruchomione procesy', 'running processes',
                'działające procesy', 'top procesy', 'cpu', 'memory usage', 
                'użycie pamięci', 'show processes', 'pokaż procesy',
                'sprawdź procesy', 'procesy zużywające pamięć', 'procesy zużywające cpu',
                'znajdź procesy', 'procesy użytkownika', 'zombie procesy', 'drzewo procesów',
                'pokaż użycie cpu i pamięci', 'monitor systemowy', 'htop'
            ],
            'file_operation': [
                'kopiuj', 'przenieś', 'usuń plik', 'copy', 'move', 'rm',
                'skopiuj', 'mv', 'rename', 'zmień nazwę',
                'skopiuj plik', 'przenieś plik', 'usuń plik', 'usuń wszystkie pliki',
                'utwórz katalog', 'zmień nazwę pliku', 'zmień nazwę pliku na',
                'sprawdź rozmiar pliku', 'rozmiar pliku', 'du plik', 'wielkość pliku'
            ],
            'disk': [
                'miejsce na dysku', 'disk space', 'df', 'du', 'rozmiar',
                'ile miejsca', 'how much space', 'wolne miejsce', 'free space',
                'pokaż dysk', 'użycie dysku', 'miejsce na dysku', 'sprawdź miejsce na dysku',
                'sprawdź dysk twardy', 'dysk twardy', 'zdrowie dysku', 'defragmentacja'
            ],
            'network': [
                'ping', 'curl', 'wget', 'sieć', 'network', 'port',
                'połączenie', 'connection', 'netstat',
                'sprawdź połączenie', 'testuj łączność', 'pinguj', 'sprawdź ping',
                'pokaż adres ip', 'adres ip', 'ip address', 'konfiguracja sieciowa',
                'znajdź porty', 'otwarte porty', 'porty nasłuchujące', 'aktywne połączenia',
                'znajdź urządzenia', 'skanuj sieć', 'nmap', 'prędkość internetu'
            ],
            'archive': [
                'spakuj', 'rozpakuj', 'zip', 'tar', 'compress', 'extract',
                'archiwum', 'archive', 'unzip', 'untar',
                'utwórz backup', 'skompresuj', 'backup', 'kopia zapasowa',
                'skopiuj backup', 'odtwórz z backupu', 'integralność backupu', 'status backupu',
                'usuń stare backupi', 'rozmiar backupu', 'harmonogram backup'
            ],
            'grep': [
                'grep', 'wyszukaj tekst', 'find text', 'szukaj w pliku',
                'pattern', 'wzorzec', 'filtruj', 'filter',
                'znajdź błędy', 'wyszukaj błędy', 'grep error', 'filtruj logi', 'przeglądaj logi'
                , 'wyszukaj linie', 'linie z error', 'linie z ERROR', 'szukaj error'
            ],
            'git_status': [
                'git status',
                'status gita',
                'status git',
                'pokaż status gita',
                'sprawdź status gita',
            ],
            'git_branch': [
                'git branch',
                'aktualna gałąź',
                'aktualna galaz',
                'gałąź gita',
                'galaz gita',
                'current branch',
            ],
            'system_maintenance': [
                'aktualizacja', 'upgrade', 'czyszczenie', 'maintenance', 'update', 'clean',
                'czyść cache', 'aktualizuj system', 'uruchom aktualizację', 'czyszczenie systemowe',
                'sprawdź logi', 'logi systemowe', 'oczyszczanie plików tymczasowych', 'usuń stare pliki',
                'sprawdź cron', 'status cron', 'uruchom defragmentację'
            ],
            'development': [
                'test', 'build', 'compile', 'run', 'debug', 'lint', 'version', 'install',
                'uruchom testy', 'testy jednostkowe', 'zbuduj projekt', 'maven', 'npm install',
                'serwer deweloperski', 'uruchom serwer', 'debugger', 'linter', 'analiza kodu',
                'logi aplikacji', 'czyszczenie cache', 'generuj dokumentację', 'wersja node'
            ],
            'security': [
                'bezpieczeństwo', 'security', 'who', 'last', 'ssh', 'permissions', 'firewall',
                'kto jest zalogowany', 'historia logowań', 'sesje ssh', 'uprawnienia pliku',
                'pliki suid', 'firewall rules', 'logi bezpieczeństwa', 'podejrzane procesy',
                'zainstalowane pakiety', 'użytkownicy systemu'
            ],
            'process_management': [
                'zabij proces', 'uruchom proces', 'zatrzymaj proces', 'restartuj proces', 'uruchom ponownie',
                'uruchom w tle', 'uruchom skrypt', 'zatrzymaj usługę', 'uruchom usługę', 'status usługi',
                'sprawdź status', 'monitor systemowy', 'htop', 'top'
            ],
            'open_url': [
                'otwórz przeglądarkę', 'open browser', 'otwórz stronę', 'open url', 'open website',
                'otwórz link', 'browse to', 'navigate to', 'go to url', 'idź do strony',
                'wejdź na stronę', 'przeglądarka', 'browser', 'xdg-open', 'open link',
                'otwórz google', 'otwórz youtube', 'otwórz github', 'open google', 'open youtube',
                'go to youtube', 'go to github', 'go to google', 'go to facebook',
                'youtube.com', 'github.com', 'google.com', 'facebook.com',
            ],
            'search_web': [
                'wyszukaj w google', 'google search', 'szukaj w internecie', 'search web',
                'wyszukaj online', 'znajdź w internecie', 'look up online',
                'wyszukaj w', 'szukaj w google', 'google python', 'google tutorial',
            ],
            # Text processing
            'text_head': [
                'head', 'pokaż początek', 'pierwsze linie', 'first lines', 'top lines',
                'początek pliku', 'head file', 'pokaż pierwsze',
            ],
            'text_tail': [
                'tail', 'pokaż koniec', 'ostatnie linie', 'last lines', 'bottom lines',
                'koniec pliku', 'tail file', 'pokaż ostatnie', 'follow log',
            ],
            'text_wc': [
                'wc', 'policz linie', 'policz słowa', 'count lines', 'count words',
                'ile linii', 'ile słów', 'word count', 'line count', 'zlicz linie',
            ],
            'text_sort': [
                'sort', 'posortuj', 'sortuj', 'sort file', 'sort lines',
                'posortuj plik', 'sortowanie', 'uporządkuj',
            ],
            'text_uniq': [
                'uniq', 'unikalne', 'unique', 'usuń duplikaty', 'remove duplicates',
                'deduplikacja', 'dedupe', 'distinct lines',
            ],
            'text_cut': [
                'cut', 'wytnij kolumnę', 'cut column', 'extract column', 'field',
                'wytnij pole', 'delimiter', 'kolumna z pliku',
            ],
            'text_awk': [
                'awk', 'przetwórz tekst', 'process text', 'text processing',
                'wyciągnij pole', 'extract field', 'awk print',
            ],
            'text_sed': [
                'sed', 'zamień tekst', 'replace text', 'substitute', 'find replace',
                'podmień', 'search replace', 'edytuj w miejscu',
            ],
            'text_tr': [
                'tr', 'transliteruj', 'translate chars', 'zamień znaki',
                'uppercase', 'lowercase', 'małe litery', 'wielkie litery',
            ],
            'text_diff': [
                'diff', 'porównaj pliki', 'compare files', 'różnice', 'differences',
                'różnica między', 'porównanie plików',
            ],
            'text_cat': [
                'cat', 'pokaż plik', 'wyświetl plik', 'show file', 'display file',
                'zawartość pliku', 'file content', 'odczytaj plik',
            ],
            'text_less': [
                'less', 'more', 'przeglądaj plik', 'browse file', 'page through',
                'pager', 'scroll file',
            ],
            # Permissions
            'perm_chmod': [
                'chmod', 'uprawnienia', 'permissions', 'zmień uprawnienia',
                'change permissions', 'executable', 'wykonywalny', 'read write',
            ],
            'perm_chown': [
                'chown', 'właściciel', 'owner', 'zmień właściciela', 'change owner',
                'ownership', 'grupa', 'group',
            ],
            # Users and groups
            'user_whoami': [
                'whoami', 'kto jestem', 'current user', 'aktualny użytkownik',
                'moja nazwa', 'my username',
            ],
            'user_id': [
                'id', 'user id', 'uid', 'gid', 'groups', 'grupy użytkownika',
            ],
            'user_list': [
                'użytkownicy', 'users', 'lista użytkowników', 'list users',
                'konta', 'accounts', 'passwd',
            ],
            # SSH/SCP
            'ssh_connect': [
                'ssh', 'połącz ssh', 'ssh connect', 'remote shell',
                'zaloguj ssh', 'ssh login', 'połącz z serwerem',
            ],
            'ssh_copy': [
                'scp', 'kopiuj ssh', 'ssh copy', 'remote copy', 'scp file',
                'prześlij plik', 'transfer file', 'kopiuj na serwer',
            ],
            'ssh_keygen': [
                'ssh-keygen', 'generuj klucz', 'generate key', 'ssh key',
                'klucz ssh', 'para kluczy', 'key pair',
            ],
            # Environment
            'env_show': [
                'env', 'printenv', 'zmienne środowiskowe', 'environment variables',
                'pokaż zmienne', 'show env', 'echo $',
            ],
            'env_export': [
                'export', 'ustaw zmienną', 'set variable', 'set env',
                'zmienna środowiskowa', 'environment variable',
            ],
            # Cron
            'cron_list': [
                'crontab -l', 'pokaż cron', 'list cron', 'scheduled tasks',
                'zaplanowane zadania', 'cron jobs', 'harmonogram',
            ],
            'cron_edit': [
                'crontab -e', 'edytuj cron', 'edit cron', 'add cron',
                'dodaj zadanie', 'schedule task', 'zaplanuj',
            ],
            # System info
            'sys_uname': [
                'uname', 'wersja systemu', 'system version', 'kernel version',
                'wersja kernela', 'os version', 'linux version',
            ],
            'sys_uptime': [
                'uptime', 'czas działania', 'system uptime', 'jak długo działa',
                'server uptime', 'czas od restartu',
            ],
            'sys_hostname': [
                'hostname', 'nazwa hosta', 'host name', 'nazwa serwera',
                'server name', 'machine name',
            ],
            'sys_date': [
                'date', 'data', 'czas', 'time', 'current date', 'aktualna data',
                'jaki jest czas', 'what time',
            ],
            'sys_cal': [
                'cal', 'kalendarz', 'calendar', 'pokaż kalendarz', 'show calendar',
                'miesiąc', 'month',
            ],
            'sys_free': [
                'free', 'pamięć', 'memory', 'ram', 'użycie pamięci', 'memory usage',
                'wolna pamięć', 'free memory', 'available memory',
            ],
            'sys_lscpu': [
                'lscpu', 'cpu info', 'informacje o cpu', 'procesor',
                'processor info', 'cpu details', 'ile rdzeni', 'cores',
            ],
            'sys_lsblk': [
                'lsblk', 'block devices', 'dyski', 'partitions', 'partycje',
                'urządzenia blokowe', 'storage devices',
            ],
            'sys_mount': [
                'mount', 'zamontowane', 'mounted', 'punkty montowania',
                'mount points', 'filesystems',
            ],
            # History
            'history': [
                'history', 'historia', 'poprzednie komendy', 'previous commands',
                'command history', 'historia poleceń',
            ],
            # Aliases
            'alias_list': [
                'alias', 'aliasy', 'aliases', 'pokaż aliasy', 'list aliases',
            ],
            # Watch/repeat
            'watch': [
                'watch', 'obserwuj', 'monitor', 'powtarzaj', 'repeat command',
                'co sekundę', 'every second',
            ],
            # Download
            'download_wget': [
                'wget', 'pobierz plik', 'download file', 'pobierz z url',
                'download from url', 'fetch file',
            ],
            'download_curl': [
                'curl', 'pobierz curl', 'curl download', 'api request',
                'http request', 'rest api', 'pobierz dane',
            ],
            # JSON processing
            'json_jq': [
                'jq', 'parsuj json', 'parse json', 'json query', 'extract json',
                'filtruj json', 'json filter', 'pretty print json',
            ],
            # Xargs/parallel
            'xargs': [
                'xargs', 'parallel', 'równolegle', 'for each', 'dla każdego',
                'batch process', 'przetwarzaj wsadowo',
            ],
        },
        'docker': {
            'list': [
                'kontenery', 'containers', 'docker ps', 'pokaż kontenery',
                'lista kontenerów', 'running containers', 'obrazy', 'images',
            ],
            'run': [
                'uruchom kontener', 'docker run', 'start container',
                'odpal kontener', 'wystartuj',
            ],
            'start': [
                'uruchom kontener', 'docker start', 'start container',
                'odpal kontener', 'wystartuj', 'zatrzymany kontener',
            ],
            'stop': [
                'zatrzymaj kontener', 'docker stop', 'stop container',
                'zatrzymaj', 'kill container',
            ],
            'remove': [
                'usuń kontener', 'docker remove', 'remove container',
                'usuń', 'docker rm',
            ],
            'logs': [
                'logi kontenera', 'docker logs', 'container logs',
                'pokaż logi', 'show logs', 'dziennik',
                'logów kontenera', 'logow kontenera',
            ],
            'build': [
                'zbuduj obraz', 'docker build', 'build image',
                'stwórz obraz', 'create image',
            ],
            'exec': [
                'wejdź do kontenera', 'docker exec', 'execute in container',
                'bash w kontenerze', 'shell in container',
            ],
            'compose': [
                'docker-compose', 'compose up', 'compose down',
                'stack', 'docker compose',
            ],
            'prune': [
                'wyczyść docker', 'docker prune', 'clean docker',
                'usuń nieużywane', 'remove unused',
            ],
            'images': [
                'docker images', 'obrazy docker', 'list images', 'lista obrazów',
                'pokaż obrazy', 'show images', 'images', 'obrazy',
            ],
            'pull': [
                'docker pull', 'pobierz obraz', 'pull image', 'ściągnij obraz',
                'download image',
            ],
            'push': [
                'docker push', 'wypchnij obraz', 'push image', 'upload image',
                'opublikuj obraz',
            ],
            'tag': [
                'docker tag', 'otaguj obraz', 'tag image', 'rename image',
                'zmień tag',
            ],
            'inspect': [
                'docker inspect', 'inspekcja', 'inspect container', 'szczegóły kontenera',
                'container details', 'inspect image',
            ],
            'stats': [
                'docker stats', 'statystyki', 'container stats', 'użycie zasobów',
                'resource usage', 'cpu memory docker',
            ],
            'network_list': [
                'docker network ls', 'sieci docker', 'docker networks', 'list networks',
                'lista sieci',
            ],
            'network_create': [
                'docker network create', 'utwórz sieć', 'create network',
                'nowa sieć docker',
            ],
            'volume_list': [
                'docker volume ls', 'wolumeny', 'docker volumes', 'list volumes',
                'lista wolumenów',
            ],
            'volume_create': [
                'docker volume create', 'utwórz wolumen', 'create volume',
                'nowy wolumen',
            ],
            'cp': [
                'docker cp', 'kopiuj do kontenera', 'copy to container',
                'kopiuj z kontenera', 'copy from container',
            ],
            'diff': [
                'docker diff', 'zmiany w kontenerze', 'container changes',
                'filesystem changes',
            ],
            'history': [
                'docker history', 'historia obrazu', 'image history',
                'warstwy obrazu', 'image layers',
            ],
            'save': [
                'docker save', 'eksportuj obraz', 'export image', 'save image',
                'zapisz obraz',
            ],
            'load': [
                'docker load', 'importuj obraz', 'import image', 'load image',
                'wczytaj obraz',
            ],
            'compose_up': [
                'docker-compose up', 'compose up', 'uruchom stack', 'start stack',
                'uruchom compose',
            ],
            'compose_down': [
                'docker-compose down', 'compose down', 'zatrzymaj stack', 'stop stack',
                'zatrzymaj compose',
            ],
            'compose_ps': [
                'docker-compose ps', 'compose ps', 'stack status', 'status compose',
            ],
            'compose_logs': [
                'docker-compose logs', 'compose logs', 'logi stack', 'stack logs',
            ],
            'compose_build': [
                'docker-compose build', 'compose build', 'zbuduj stack',
                'build stack',
            ],
        },
        'kubernetes': {
            'get': [
                'kubectl get', 'kubectl', 'pody', 'pods', 'deployments', 'pokaż pody',
                'services', 'serwisy', 'namespace', 'nodes', 'nody',
                'configmap', 'secret', 'ingress', 'k8s get',
            ],
            'scale': [
                'skaluj', 'scale', 'replicas', 'replik', 'zwiększ',
                'zmniejsz', 'autoscale',
            ],
            'apply': [
                'zastosuj', 'apply', 'kubectl apply', 'wdróż',
                'deploy', 'deployment',
            ],
            'delete': [
                'usuń pod', 'delete pod', 'kubectl delete',
                'usuń deployment', 'remove',
            ],
            'logs': [
                'logi poda', 'kubectl logs', 'pod logs',
                'pokaż logi k8s', 'kubernetes logs',
            ],
            'describe': [
                'opisz', 'describe', 'szczegóły', 'details',
                'kubectl describe', 'info',
            ],
            'exec': [
                'wejdź do poda', 'kubectl exec', 'exec pod',
                'shell w podzie', 'bash pod',
            ],
            'rollout_status': [
                'kubectl rollout status', 'status rollout', 'deployment status',
                'status wdrożenia', 'rollout progress',
            ],
            'rollout_restart': [
                'kubectl rollout restart', 'rollout restart', 'restart deployment', 'restartuj deployment',
                'rolling restart', 'restart pods', 'zrestartuj deployment',
            ],
            'rollout_history': [
                'kubectl rollout history', 'historia wdrożeń', 'deployment history',
                'rollout revisions',
            ],
            'rollout_undo': [
                'kubectl rollout undo', 'cofnij wdrożenie', 'rollback',
                'undo deployment', 'poprzednia wersja',
            ],
            'events': [
                'kubectl get events', 'zdarzenia', 'events', 'k8s events',
                'cluster events', 'wydarzenia',
            ],
            'configmap_get': [
                'kubectl get configmap', 'pokaż configmap', 'list configmaps',
                'configmapy', 'config maps',
            ],
            'configmap_create': [
                'kubectl create configmap', 'utwórz configmap', 'create configmap',
                'nowy configmap',
            ],
            'secret_get': [
                'kubectl get secret', 'pokaż secret', 'list secrets',
                'sekrety', 'secrets',
            ],
            'secret_create': [
                'kubectl create secret', 'utwórz secret', 'create secret',
                'nowy secret',
            ],
            'namespace_list': [
                'kubectl get namespaces', 'pokaż namespaces', 'list namespaces',
                'przestrzenie nazw', 'ns list',
            ],
            'namespace_create': [
                'kubectl create namespace', 'utwórz namespace', 'create namespace',
                'nowy namespace', 'new ns',
            ],
            'top_pods': [
                'kubectl top pods', 'użycie zasobów podów', 'pod resources',
                'cpu memory pods', 'top pody',
            ],
            'top_nodes': [
                'kubectl top nodes', 'użycie zasobów nodów', 'node resources',
                'cpu memory nodes', 'top nody',
            ],
            'port_forward': [
                'kubectl port-forward', 'przekierowanie portów', 'port forward',
                'forward port', 'proxy port',
            ],
            'context': [
                'kubectl config', 'kontekst', 'context', 'zmień kontekst',
                'switch context', 'use context', 'current context',
            ],
            'cluster_info': [
                'kubectl cluster-info', 'informacje o klastrze', 'cluster info',
                'k8s info', 'kubernetes info',
            ],
        },
        'git': {
            'status': [
                'git status', 'status gita', 'status repo', 'co zmienione',
                'what changed', 'pokaż zmiany', 'zmiany w repo',
            ],
            'log': [
                'git log', 'historia commitów', 'commit history', 'log gita',
                'historia zmian', 'pokaż commity', 'show commits',
            ],
            'diff': [
                'git diff', 'różnice', 'differences', 'pokaż diff',
                'co się zmieniło', 'changes', 'zmiany w plikach',
            ],
            'branch': [
                'git branch', 'gałęzie', 'branches', 'pokaż gałęzie',
                'list branches', 'aktualna gałąź', 'current branch',
            ],
            'checkout': [
                'git checkout', 'przełącz gałąź', 'switch branch', 'zmień branch',
                'checkout branch', 'przejdź do gałęzi',
            ],
            'pull': [
                'git pull', 'pobierz zmiany', 'pull changes', 'zaktualizuj repo',
                'update repo', 'fetch and merge',
            ],
            'push': [
                'git push', 'wypchnij zmiany', 'push changes', 'opublikuj',
                'push to remote', 'wyślij commity',
            ],
            'commit': [
                'git commit', 'zatwierdź zmiany', 'commit changes', 'zrób commit',
                'zapisz zmiany', 'save changes',
            ],
            'add': [
                'git add', 'dodaj do staging', 'stage files', 'dodaj pliki',
                'add files', 'stage changes',
            ],
            'stash': [
                'git stash', 'schowaj zmiany', 'stash changes', 'odłóż zmiany',
                'save for later', 'tymczasowo schowaj',
            ],
            'merge': [
                'git merge', 'scal gałęzie', 'merge branches', 'połącz branch',
                'merge branch', 'scal zmiany',
            ],
            'rebase': [
                'git rebase', 'rebase', 'przenieś commity', 'rebase branch',
                'interactive rebase',
            ],
            'reset': [
                'git reset', 'cofnij commit', 'reset commit', 'undo commit',
                'anuluj zmiany', 'reset head',
            ],
            'clone': [
                'git clone', 'sklonuj repo', 'clone repository', 'pobierz repo',
                'download repo', 'skopiuj repo',
            ],
            'remote': [
                'git remote', 'zdalne repo', 'remote repos', 'pokaż remote',
                'list remotes', 'origin',
            ],
            'tag': [
                'git tag', 'tagi', 'tags', 'utwórz tag', 'create tag',
                'pokaż tagi', 'list tags', 'wersja',
            ],
            'blame': [
                'git blame', 'kto zmienił', 'who changed', 'blame file',
                'autor linii', 'line author',
            ],
            'show': [
                'git show', 'pokaż commit', 'show commit', 'szczegóły commita',
                'commit details',
            ],
            'cherry_pick': [
                'git cherry-pick', 'cherry pick', 'wybierz commit',
                'pick commit', 'przenieś commit',
            ],
            'fetch': [
                'git fetch', 'pobierz', 'fetch remote', 'fetch origin',
                'pobierz bez merge',
            ],
            'clean': [
                'git clean', 'wyczyść repo', 'clean untracked', 'usuń nieśledzone',
                'remove untracked',
            ],
        },
        'dql': {
            'query': [
                'znajdź entity', 'entity query', 'dql', 'graph query',
                'relacje', 'relations', 'powiązania', 'connections',
            ],
        },
    }
    
    # Domain-specific boost keywords (increase confidence)
    DOMAIN_BOOSTERS: dict[str, list[str]] = {
        'sql': ['tabela', 'table', 'kolumna', 'column', 'baza', 'database', 'sql', 'where', 'join', 'tabeli', 'z tabeli'],
        'shell': ['plik', 'file', 'katalog', 'directory', 'folder', 'ścieżka', 'path', 'bash', 'terminal',
                  'znajdź', 'skopiuj', 'usuń', 'utwórz', 'zmień', 'sprawdź', 'pokaż', 'uruchom', 'zatrzymaj',
                  'proces', 'dysk', 'sieć', 'port', 'backup', 'logi', 'test', 'build', 'debug'],
        'docker': ['docker', 'kontener', 'container', 'obraz', 'image', 'compose', 'dockerfile'],
        'kubernetes': ['kubernetes', 'k8s', 'kubectl', 'pod', 'deployment', 'namespace', 'helm', 'cluster', 'node', 'service'],
        'git': ['git', 'repo', 'repository', 'commit', 'branch', 'gałąź', 'merge', 'push', 'pull', 'clone'],
        'dql': ['entity', 'graph', 'node', 'edge', 'relation'],
    }
    
    def __init__(
        self,
        patterns: Optional[dict[str, dict[str, list[str]]]] = None,
        confidence_threshold: float = 0.5,
    ):
        """
        Initialize keyword detector.
        
        Args:
            patterns: Custom patterns to use (or default PATTERNS)
            confidence_threshold: Minimum confidence to return a match
        """
        self.patterns = patterns or {}
        self.confidence_threshold = confidence_threshold
        self.domain_boosters: dict[str, list[str]] = dict(self.DOMAIN_BOOSTERS)
        self.priority_intents: dict[str, list[str]] = dict(self.PRIORITY_INTENTS)
        self.fast_path_browser_keywords: list[str] = []
        self.fast_path_search_keywords: list[str] = []
        self.fast_path_common_images: set[str] = set()

        self._load_detector_config_from_json()
        self._load_patterns_from_json()

        if not self.patterns:
            self.patterns = dict(self.PATTERNS)

    def _load_detector_config_from_json(self) -> None:
        path = os.environ.get("NLP2CMD_KEYWORD_DETECTOR_CONFIG") or "./data/keyword_intent_detector_config.json"
        p = Path(path)
        if not p.exists():
            return
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return
        if not isinstance(payload, dict):
            return

        boosters = payload.get("domain_boosters")
        if isinstance(boosters, dict):
            loaded: dict[str, list[str]] = {}
            for d, items in boosters.items():
                if not isinstance(d, str) or not d.strip() or not isinstance(items, list):
                    continue
                clean = [x.strip() for x in items if isinstance(x, str) and x.strip()]
                if clean:
                    loaded[d.strip()] = clean
            if loaded:
                self.domain_boosters = loaded

        priority = payload.get("priority_intents")
        if isinstance(priority, dict):
            loaded_p: dict[str, list[str]] = {}
            for d, items in priority.items():
                if not isinstance(d, str) or not d.strip() or not isinstance(items, list):
                    continue
                clean = [x.strip() for x in items if isinstance(x, str) and x.strip()]
                if clean:
                    loaded_p[d.strip()] = clean
            if loaded_p:
                self.priority_intents = loaded_p

        fast_path = payload.get("fast_path")
        if isinstance(fast_path, dict):
            b = fast_path.get("browser_keywords")
            if isinstance(b, list):
                self.fast_path_browser_keywords = [x.strip() for x in b if isinstance(x, str) and x.strip()]

            s = fast_path.get("search_keywords")
            if isinstance(s, list):
                self.fast_path_search_keywords = [x.strip() for x in s if isinstance(x, str) and x.strip()]

            imgs = fast_path.get("common_images")
            if isinstance(imgs, list):
                self.fast_path_common_images = set(x.strip().lower() for x in imgs if isinstance(x, str) and x.strip())

    def _load_patterns_from_json(self) -> None:
        """Load patterns from external JSON file with fallback to embedded PATTERNS."""
        path = os.environ.get("NLP2CMD_PATTERNS_FILE") or "./data/patterns.json"
        p = Path(path)
        if not p.exists():
            # Fallback to embedded PATTERNS if no external file
            for domain, intents in self.PATTERNS.items():
                for intent, keywords in intents.items():
                    self.add_pattern(domain, intent, keywords)
            return
        try:
            payload = json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            # On error, fallback to embedded PATTERNS
            for domain, intents in self.PATTERNS.items():
                for intent, keywords in intents.items():
                    self.add_pattern(domain, intent, keywords)
            return
        if not isinstance(payload, dict):
            # Invalid format, fallback to embedded PATTERNS
            for domain, intents in self.PATTERNS.items():
                for intent, keywords in intents.items():
                    self.add_pattern(domain, intent, keywords)
            return

        # Expected format: {"shell": {"intent": ["kw", ...]}, "sql": {...}, ...}
        loaded_any = False
        for domain, intents in payload.items():
            if not isinstance(domain, str) or not domain:
                continue
            if not isinstance(intents, dict):
                continue
            for intent, keywords in intents.items():
                if not isinstance(intent, str) or not intent:
                    continue
                if not isinstance(keywords, list):
                    continue
                clean: list[str] = []
                for kw in keywords:
                    if isinstance(kw, str) and kw.strip():
                        clean.append(kw.strip())
                if clean:
                    self.add_pattern(domain, intent, clean)
                    loaded_any = True
        
        # If no valid patterns were loaded, fallback to embedded PATTERNS
        if not loaded_any:
            for domain, intents in self.PATTERNS.items():
                for intent, keywords in intents.items():
                    self.add_pattern(domain, intent, keywords)
    
    # Priority intents - check these first as they are more specific/destructive
    PRIORITY_INTENTS: dict[str, list[str]] = {
        'sql': ['delete', 'update', 'insert', 'aggregate'],
        'shell': ['open_url', 'search_web', 'file_operation', 'archive', 'process', 'disk', 'system_maintenance', 'development', 'security', 'process_management'],
        'docker': ['stop', 'prune', 'build', 'run', 'list', 'logs', 'exec', 'start', 'remove'],
        'kubernetes': ['delete', 'scale', 'describe', 'logs'],
    }
    
    def detect(self, text: str) -> DetectionResult:
        """
        Detect domain and intent from text.
        
        Args:
            text: Natural language input
            
        Returns:
            DetectionResult with domain, intent, confidence
        """
        text_lower = text.lower()

        # Fast-path: browser/URL opening queries.
        # Detect URLs or common website names in the query.
        url_pattern = re.search(r'\b([a-zA-Z0-9][\w\-]*\.(?:com|org|net|io|dev|pl|de|uk|eu|gov|edu|tv|co))\b', text_lower)
        browser_keywords = self.fast_path_browser_keywords
        has_browser_keyword = any(kw in text_lower for kw in browser_keywords)
        
        # Check if it's a search query (can be with or without URL)
        search_keywords = self.fast_path_search_keywords
        if any(kw in text_lower for kw in search_keywords):
            return DetectionResult(
                domain="shell",
                intent="search_web",
                confidence=0.9,
                matched_keyword="search+web",
            )
        
        # URL opening (needs URL pattern or browser keyword)
        if url_pattern or has_browser_keyword:
            return DetectionResult(
                domain="shell",
                intent="open_url",
                confidence=0.9,
                matched_keyword=url_pattern.group(1) if url_pattern else "browser",
            )

        # Fast-path: docker-like queries without explicit 'docker' keyword.
        # Example: "run nginx on port 8080".
        # Without this, generic shell 'development' keywords (e.g. 'run') can dominate.
        common_images = self.fast_path_common_images
        has_run_word = bool(re.search(r"\b(run|start|launch|uruchom|odpal|wystartuj)\b", text_lower))
        has_port = bool(re.search(r"\bport\b\s*\d+|\bon\s+port\s+\d+|\bporcie\s+\d+", text_lower))
        has_common_image = any(img in text_lower for img in common_images)
        if has_run_word and has_port and has_common_image:
            return DetectionResult(
                domain="docker",
                intent="run_detached",
                confidence=0.9,
                matched_keyword="run+port+image",
            )

        sql_boosters = self.domain_boosters.get('sql', [])
        sql_context = any(b.lower() in text_lower for b in sql_boosters)
        sql_explicit = bool(re.search(r"\b(select|update|delete|insert|from|where|join|sql|table|tabela)\b", text_lower))

        # Fast-path: if the user explicitly uses the docker CLI, prefer docker intents
        # (prevents shell/process keywords like 'ps' from dominating).
        if 'docker' in text_lower:
            if has_run_word and has_port and has_common_image:
                return DetectionResult(
                    domain="docker",
                    intent="run_detached",
                    confidence=0.9,
                    matched_keyword="run+port+image",
                )
            docker_intents = self.patterns.get('docker', {})
            priority = list(self.priority_intents.get('docker', []))
            ordered_intents = priority + [i for i in docker_intents.keys() if i not in priority]
            for intent in ordered_intents:
                keywords = docker_intents.get(intent, [])
                for kw in keywords:
                    if kw.lower() in text_lower:
                        confidence = 0.9
                        keyword_length_bonus = min(len(kw) / 25, 0.05)
                        confidence = min(confidence + keyword_length_bonus, 0.95)
                        return DetectionResult(
                            domain='docker',
                            intent=intent,
                            confidence=confidence,
                            matched_keyword=kw,
                        )
        
        # Fast-path: if the user explicitly uses kubernetes terms, prefer k8s intents
        # (prevents shell keywords like 'pokaż' from dominating).
        k8s_boosters = self.domain_boosters.get('kubernetes', [])
        if any(booster.lower() in text_lower for booster in k8s_boosters):
            k8s_intents = self.patterns.get('kubernetes', {})
            priority = list(self.priority_intents.get('kubernetes', []))
            ordered_intents = priority + [i for i in k8s_intents.keys() if i not in priority]
            for intent in ordered_intents:
                keywords = k8s_intents.get(intent, [])
                for kw in keywords:
                    if kw.lower() in text_lower:
                        confidence = 0.9
                        keyword_length_bonus = min(len(kw) / 25, 0.05)
                        confidence = min(confidence + keyword_length_bonus, 0.95)
                        return DetectionResult(
                            domain='kubernetes',
                            intent=intent,
                            confidence=confidence,
                            matched_keyword=kw,
                        )
        
        best_match: Optional[DetectionResult] = None
        best_score = 0.0
        
        # First pass: check priority intents (destructive operations)
        for domain, priority_intents in self.priority_intents.items():
            if domain not in self.patterns:
                continue

            if domain == 'sql' and not (sql_context or sql_explicit):
                continue

            # Guard: docker intents should only win when docker-specific boosters are present.
            # This prevents generic phrases like "pokaż logi" from overriding kubernetes.
            if domain == 'docker':
                docker_boosters = self.domain_boosters.get('docker', [])
                if not any(b.lower() in text_lower for b in docker_boosters):
                    continue

            for intent in priority_intents:
                if intent not in self.patterns[domain]:
                    continue
                
                # Special handling: prefer shell for file operations when shell context is present
                if domain == 'sql' and intent == 'delete':
                    shell_boosters = self.domain_boosters.get('shell', [])
                    shell_context = any(b.lower() in text_lower for b in shell_boosters)
                    sql_boosters = self.domain_boosters.get('sql', [])
                    sql_context = any(b.lower() in text_lower for b in sql_boosters)
                    
                    # Only skip SQL delete if shell context is strong AND no SQL context
                    if shell_context and not sql_context:
                        # Skip SQL delete intent when shell context is detected but no SQL context
                        continue
                
                keywords = self.patterns[domain][intent]
                for kw in keywords:
                    if kw.lower() in text_lower:
                        confidence = 0.85  # Higher base confidence for priority
                        keyword_length_bonus = min(len(kw) / 20, 0.10)
                        confidence = min(confidence + keyword_length_bonus, 0.95)
                        
                        position = text_lower.find(kw.lower())
                        position_bonus = 0.05 if position < 15 else 0.0
                        score = confidence + position_bonus
                        
                        # Special rule: SQL delete should always beat SQL select
                        if domain == 'sql' and intent == 'delete' and best_match and best_match.domain == 'sql' and best_match.intent == 'select':
                            score += 0.2  # Boost delete over select
                        
                        if score > best_score:
                            best_score = score
                            best_match = DetectionResult(
                                domain=domain,
                                intent=intent,
                                confidence=confidence,
                                matched_keyword=kw,
                            )
        
        # If we found a priority match, return it
        if best_match and best_match.confidence >= self.confidence_threshold:
            return best_match
        
        # Second pass: check all patterns
        for domain, intents in self.patterns.items():
            if domain == 'sql' and not (sql_context or sql_explicit):
                continue
            for intent, keywords in intents.items():
                for kw in keywords:
                    if kw.lower() in text_lower:
                        # Special handling: prefer shell for file operations when shell context is present
                        if domain == 'sql' and intent == 'delete':
                            shell_boosters = self.domain_boosters.get('shell', [])
                            shell_context = any(b.lower() in text_lower for b in shell_boosters)
                            if shell_context:
                                # Skip SQL delete intent when shell context is detected
                                continue
                        
                        # Base confidence
                        confidence = 0.7
                        
                        # Boost for longer keyword matches (more specific)
                        keyword_length_bonus = min(len(kw) / 20, 0.15)
                        confidence += keyword_length_bonus
                        
                        # Boost for domain-specific keywords
                        domain_boost = self._calculate_domain_boost(text_lower, domain)
                        confidence += domain_boost
                        
                        # Cap at 0.95
                        confidence = min(confidence, 0.95)
                        
                        # Calculate score (confidence + match position penalty)
                        position = text_lower.find(kw.lower())
                        position_bonus = 0.05 if position < 20 else 0.0
                        score = confidence + position_bonus
                        
                        if score > best_score:
                            best_score = score
                            best_match = DetectionResult(
                                domain=domain,
                                intent=intent,
                                confidence=confidence,
                                matched_keyword=kw,
                            )
        
        if best_match and best_match.confidence >= self.confidence_threshold:
            return best_match
        
        return DetectionResult(
            domain='unknown',
            intent='unknown',
            confidence=0.0,
            matched_keyword=None,
        )
    
    def _calculate_domain_boost(self, text: str, domain: str) -> float:
        """Calculate confidence boost based on domain-specific keywords."""
        boosters = self.domain_boosters.get(domain, [])
        matches = sum(1 for b in boosters if b.lower() in text)
        return min(matches * 0.05, 0.15)
    
    def detect_all(self, text: str) -> list[DetectionResult]:
        """
        Detect all matching domains and intents.
        
        Args:
            text: Natural language input
            
        Returns:
            List of DetectionResult, sorted by confidence descending
        """
        text_lower = text.lower()
        results: list[DetectionResult] = []
        seen: set[tuple[str, str]] = set()
        
        for domain, intents in self.patterns.items():
            for intent, keywords in intents.items():
                for kw in keywords:
                    if kw.lower() in text_lower:
                        key = (domain, intent)
                        if key not in seen:
                            seen.add(key)
                            confidence = 0.7 + self._calculate_domain_boost(text_lower, domain)
                            results.append(DetectionResult(
                                domain=domain,
                                intent=intent,
                                confidence=min(confidence, 0.95),
                                matched_keyword=kw,
                            ))
        
        return sorted(results, key=lambda r: r.confidence, reverse=True)
    
    def add_pattern(self, domain: str, intent: str, keywords: list[str]) -> None:
        """
        Add custom patterns.
        
        Args:
            domain: Domain name
            intent: Intent name
            keywords: Keywords to match
        """
        if domain not in self.patterns:
            self.patterns[domain] = {}
        if intent not in self.patterns[domain]:
            self.patterns[domain][intent] = []
        self.patterns[domain][intent].extend(keywords)
    
    def get_supported_domains(self) -> list[str]:
        """Get list of supported domains."""
        return list(self.patterns.keys())
    
    def get_supported_intents(self, domain: str) -> list[str]:
        """Get list of supported intents for a domain."""
        return list(self.patterns.get(domain, {}).keys())
