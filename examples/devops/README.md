# NLP2CMD Web Examples

**Natural Language → Backend/DevOps Configuration**

Ten projekt demonstruje jak NLP2CMD może służyć jako inteligentna warstwa backend/DevOps, konfigurując aplikacje webowe za pomocą poleceń w języku naturalnym.

## 🎯 Koncepcja

Zamiast ręcznie pisać pliki konfiguracyjne (docker-compose, .env, Dockerfile), użytkownik wydaje polecenia w języku naturalnym:

```
"Uruchom serwis czatu na porcie 8080 z Redis jako backend"
"Skonfiguruj email dla jan@gmail.com"  
"Skaluj aplikację do 3 instancji"
```

NLP2CMD parsuje te polecenia i automatycznie:
- Generuje konfigurację Docker/Kubernetes
- Tworzy odpowiednie backendy (FastAPI)
- Konfiguruje bazy danych i cache
- Ustawia zmienne środowiskowe

## 📁 Struktura Projektu

```
nlp2cmd-web-examples/
├── demo.py                      # Główny skrypt demonstracyjny
├── shared/
│   └── nlp2cmd_web_controller.py  # Kontroler NLP2CMD
├── communicator/                # Przykład 1: Chat
│   ├── chat_example.py
│   ├── docker-compose.yml
│   ├── chat-backend/
│   └── chat-frontend/
├── contact-page/                # Przykład 2: Kontakt
│   ├── contact_example.py
│   ├── docker-compose.yml
│   ├── contact-backend/
│   └── contact-frontend/
└── email-client/                # Przykład 3: Email
    ├── email_example.py
    ├── docker-compose.yml
    ├── email-backend/
    └── email-frontend/
```

## 🚀 Szybki Start

### Tryb Interaktywny

```bash
cd examples/devops
python demo.py
```

Pozwala wydawać polecenia w języku naturalnym i obserwować generowaną konfigurację.

### Uruchomienie Konkretnego Przykładu

```bash
# Przykład 1: Komunikator
python demo.py --example 1
cd communicator
docker-compose up --build

# Przykład 2: Strona Kontaktu
python demo.py --example 2
cd contact-page
docker-compose up --build

# Przykład 3: Klient Email
python demo.py --example 3
cd email-client
docker-compose up --build

# Wszystkie przykłady
python demo.py --example all
```

## 📋 Przykłady

### 1. 💬 Komunikator (Real-Time Chat)

**Polecenia NLP:**
- "Uruchom komunikator na porcie 8080"
- "Dodaj Redis dla sesji czatu"
- "Skaluj do 3 instancji"

**Technologie:**
- FastAPI + WebSocket
- Redis (pub/sub, sesje)
- React (frontend)

**Porty:** 
- Frontend: http://localhost:3000
- API: http://localhost:8080
- WebSocket: ws://localhost:8080/ws

### 2. 📧 Strona Kontaktowa

**Polecenia NLP:**
- "Stwórz formularz kontaktowy wysyłający na contact@firma.pl"
- "Skonfiguruj SMTP dla Gmail"
- "Dodaj bazę do archiwizacji wiadomości"

**Technologie:**
- FastAPI + PostgreSQL
- SMTP (wysyłanie emaili)
- Rate limiting
- Walidacja formularzy

**Porty:**
- Frontend: http://localhost:3001
- API: http://localhost:8081

### 3. 📬 Klient Email (IMAP)

**Polecenia NLP:**
- "Skonfiguruj klienta email dla jan@gmail.com"
- "Połącz z IMAP imap.gmail.com"
- "Pokaż ostatnie 20 wiadomości"

**Technologie:**
- FastAPI + IMAP
- Redis (cache wiadomości)
- Web UI (podgląd skrzynki)

**Porty:**
- Frontend: http://localhost:3002
- API: http://localhost:8082

## 🔧 Architektura

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend (React)                          │
└─────────────────────────────┬───────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                 NLP2CMD Control Plane                        │
│  ┌───────────┐  ┌───────────┐  ┌─────────────────────────┐  │
│  │  Parser   │→ │  Router   │→ │ Docker/K8s Adapters     │  │
│  └───────────┘  └───────────┘  └─────────────────────────┘  │
└─────────────────────────────┬───────────────────────────────┘
                              │
          ┌───────────────────┼───────────────────┐
          ▼                   ▼                   ▼
   ┌─────────────┐     ┌─────────────┐     ┌─────────────┐
   │   Backend   │     │   Database  │     │   Cache     │
   │  (FastAPI)  │     │ (PostgreSQL)│     │   (Redis)   │
   └─────────────┘     └─────────────┘     └─────────────┘
```

## 🗣️ Obsługiwane Polecenia

### Deployment
- "Uruchom [serwis] na porcie [port]"
- "Deploy [aplikację] z [zależnościami]"
- "Wystartuj [kontener]"

### Konfiguracja
- "Skonfiguruj [serwis] dla [parametry]"
- "Ustaw [zmienna] na [wartość]"
- "Połącz z [zewnętrzny serwis]"

### Skalowanie
- "Skaluj [serwis] do [N] instancji"
- "Zwiększ liczbę replik"

### Monitoring
- "Pokaż status usług"
- "Sprawdź logi [serwisu]"

## ⚙️ Konfiguracja

### Zmienne Środowiskowe

Każdy przykład zawiera plik `.env.example` z wymaganymi zmiennymi:

```bash
# Skopiuj i edytuj
cp .env.example .env
nano .env
```

### Gmail - Hasło Aplikacji

Dla integracji z Gmail (kontakt, email client):

1. Włącz 2FA: https://myaccount.google.com/security
2. Wygeneruj hasło aplikacji: https://myaccount.google.com/apppasswords
3. Użyj hasła aplikacji w konfiguracji (nie zwykłego hasła)

## 🔒 Bezpieczeństwo

- Wszystkie hasła w `.env` (git-ignored)
- Rate limiting dla formularzy
- Walidacja input'ów
- CORS konfigurowalny
- Brak hardcodowanych credentials

## 📝 Integracja z NLP2CMD

Ten projekt demonstruje integrację z głównym projektem NLP2CMD:

```python
from nlp2cmd_web_controller import NLP2CMDWebController

controller = NLP2CMDWebController()

# Wykonaj polecenie w języku naturalnym
result = await controller.execute(
    "Uruchom serwis czatu na porcie 8080 z Redis"
)

# Wynik zawiera wygenerowaną konfigurację
print(result['docker_compose'])  # docker-compose.yml
print(result['config'])          # zmienne środowiskowe
```

## 🤝 Rozszerzenie

Aby dodać nowy typ usługi:

1. Dodaj wzorzec w `NLCommandParser.SERVICE_KEYWORDS`
2. Stwórz template w `NLP2CMDWebController.templates`
3. Zaimplementuj backend w nowym katalogu

## 📄 Licencja

MIT License - zobacz główny projekt NLP2CMD.
