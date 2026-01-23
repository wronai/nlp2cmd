# NLP2CMD jako Backend Webowy

Ten dokument opisuje jak używać NLP2CMD jako backendu w aplikacjach webowych.

## 📋 Spis treści

1. [Wprowadzenie](#wprowadzenie)
2. [Instalacja](#instalacja)
3. [Szybki start](#szybki-start)
4. [Przykłady integracji](#przykłady-integracji)
5. [API Reference](#api-reference)
6. [Konfiguracja](#konfiguracja)
7. [Przykłady użycia](#przykłady-użycia)

## 🚀 Wprowadzenie

NLP2CMD może być używany jako backend w aplikacjach webowych do:
- Przekształcania języka naturalnego w komendy
- Automatyzacji zadań DevOps
- Generowania konfiguracji
- Zarządzania kontenerami

### Kluczowe funkcje

- ✅ **Wsparcie dla języka polskiego i angielskiego**
- ✅ **LLM fallback z Ollama** (bez potrzeby API keys)
- ✅ **Auto-instalacja zależności**
- ✅ **Wiele DSL: shell, docker, kubernetes**
- ✅ **REST API**
- ✅ **Historia komend**
- ✅ **Zarządzanie usługami**

## 📦 Instalacja

```bash
# Klonuj repozytorium
git clone https://github.com/wronai/nlp2cmd.git
cd nlp2cmd

# Zainstaluj zależności
pip install -e .

# Dla web API (opcjonalnie)
pip install fastapi uvicorn jinja2
```

## ⚡ Szybki start

### 1. Uruchomienie przykładowej aplikacji

```bash
cd examples/devops
python web_app_example.py
```

Otwórz http://localhost:8000 w przeglądarce.

### 2. Użycie jako moduł

```python
from nlp2cmd_web_controller import NLP2CMDWebController

# Inicjalizacja
controller = NLP2CMDWebController(
    use_llm_fallback=True,
    auto_install=True
)

# Użycie
result = await controller.execute("Uruchom docker na porcie 8080")
print(result["command"])  # docker run -d -p 8080:8080 nginx
```

## 🔧 Przykłady integracji

### FastAPI

```python
from fastapi import FastAPI
from nlp2cmd_web_controller import NLP2CMDWebAPI

app = FastAPI()
nlp_api = NLP2CMDWebAPI()

@app.post("/process")
async def process_command(command: str, dsl: str = "auto"):
    result = await nlp_api.process_command(command, dsl)
    return result
```

### Flask

```python
from flask import Flask, request, jsonify
from nlp2cmd_web_controller import NLP2CMDWebAPI
import asyncio

app = Flask(__name__)
nlp_api = NLP2CMDWebAPI()

@app.route('/process', methods=['POST'])
def process_command():
    data = request.get_json()
    result = asyncio.run(nlp_api.process_command(
        data['command'], 
        data.get('dsl', 'auto')
    ))
    return jsonify(result)
```

### Docker

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .
RUN pip install fastapi uvicorn

EXPOSE 8000

CMD ["uvicorn", "web_app_example:app", "--host", "0.0.0.0", "--port", "8000"]
```

## 📚 API Reference

### Endpoints

#### POST /api/process
Przetwarza komendę z języka naturalnego.

**Request:**
```json
{
    "command": "Uruchom docker",
    "dsl": "auto"
}
```

**Response:**
```json
{
    "status": "success",
    "command": "docker run -d -p 8080:8080 nginx",
    "dsl": "docker",
    "action": "llm_fallback",
    "llm_used": true,
    "message": "Wygenerowano komendę za pomocą LLM fallback"
}
```

#### GET /api/status
Zwraca status i możliwości API.

#### GET /api/history?limit=10
Zwraca historię komend.

#### GET /api/services
Zwraca wdrożone usługi.

#### GET /api/examples
Zwraca przykładowe komendy.

### Typy DSL

- `auto` - Automatyczne wykrycie
- `shell` - Komendy shell
- `docker` - Komendy Docker
- `kubernetes` - Komendy Kubernetes

## ⚙️ Konfiguracja

### Zmienne środowiskowe

```bash
# Model LLM (domyślnie: ollama/qwen2.5-coder:7b)
export NLP2CMD_LLM_MODEL="ollama/llama3:8b"

# API base LLM (domyślnie: http://localhost:11434)
export NLP2CMD_LLM_API_BASE="http://localhost:11434"

# Timeout LLM (domyślnie: 30s)
export NLP2CMD_LLM_TIMEOUT="60"
```

### Opcje kontrolera

```python
controller = NLP2CMDWebController(
    output_dir="./generated",      # Katalog na wygenerowane pliki
    use_llm_fallback=True,        # Użyj LLM fallback
    auto_install=False            # Auto-instalacja zależności
)
```

## 💡 Przykłady użycia

### DevOps automation

```python
# Wdrożenie serwisu
result = await controller.execute("Uruchom serwis czatu na porcie 8080 z Redis")

# Zarządzanie kontenerami
result = await controller.execute("Pokaż logi kontenera nginx")

# Skalowanie
result = await controller.execute("Skaluj serwis do 3 replik")
```

### Generowanie konfiguracji

```python
# Konfiguracja email
result = await controller.execute("Skonfiguruj email dla jan@example.com")

# Baza danych
result = await controller.execute("Stwórz bazę PostgreSQL z hasłem")
```

### Shell commands

```python
# Pliki
result = await controller.execute("Stwórz plik konfiguracyjny JSON")

# System
result = await controller.execute("Pokaż zużycie dysku")
```

## 🔒 Bezpieczeństwo

### Best practices

1. **Walidacja inputów** - Zawsze waliduj komendy przed wykonaniem
2. **Sandboxing** - Uruchamiaj komendy w izolowanym środowisku
3. **Logowanie** - Loguj wszystkie komendy i wyniki
4. **Limitowanie** - Ustaw limity na czas i zasoby

### Przykład walidacji

```python
import re

def validate_command(command: str) -> bool:
    # Blokuj niebezpieczne komendy
    dangerous = ['rm -rf', 'sudo', 'chmod 777', '> /dev/sda']
    for bad in dangerous:
        if bad in command:
            return False
    return True
```

## 🚀 Wdrażanie

### Docker Compose

```yaml
version: '3.8'
services:
  nlp2cmd-api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - NLP2CMD_LLM_MODEL=ollama/qwen2.5-coder:7b
    volumes:
      - ./generated:/app/generated
  
  ollama:
    image: ollama/ollama
    ports:
      - "11434:11434"
    volumes:
      - ollama_data:/root/.ollama

volumes:
  ollama_data:
```

### Kubernetes

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: nlp2cmd-api
spec:
  replicas: 3
  selector:
    matchLabels:
      app: nlp2cmd-api
  template:
    metadata:
      labels:
        app: nlp2cmd-api
    spec:
      containers:
      - name: api
        image: nlp2cmd:latest
        ports:
        - containerPort: 8000
        env:
        - name: NLP2CMD_LLM_MODEL
          value: "ollama/qwen2.5-coder:7b"
```

## 🛠️ Rozszerzenia

### Dodawanie własnych adapterów

```python
from nlp2cmd.adapters.base import BaseDSLAdapter

class CustomAdapter(BaseDSLAdapter):
    def transform(self, text: str):
        # Własna logika transformacji
        return TransformResult(
            command="custom-command",
            dsl_type="custom"
        )

# Użycie
controller.nlp2cmd_instances["custom"] = NLP2CMD(
    adapter=CustomAdapter()
)
```

### Własne szablony

```python
def _create_custom_template(self, entities: dict) -> ServiceConfig:
    return ServiceConfig(
        name="custom-service",
        service_type=ServiceType.CUSTOM,
        port=entities.get("port", 9000),
        image="custom:latest",
    )

controller.templates[ServiceType.CUSTOM] = _create_custom_template
```

## 📝 Przykłady komend

### Polskie
- "Uruchom docker"
- "Pokaż logi kontenera"
- "Stwórz plik konfiguracyjny"
- "Skaluj serwis do 5 replik"
- "Zrestartuj bazę danych"

### Angielskie
- "Deploy docker container"
- "Show container logs"
- "Create config file"
- "Scale service to 5 replicas"
- "Restart database"

## 🤝 Współpraca

- GitHub: https://github.com/wronai/nlp2cmd
- Dokumentacja: https://nlp2cmd.readthedocs.io
- Issues: https://github.com/wronai/nlp2cmd/issues

## 📄 Licencja

MIT License - zobacz plik LICENSE dla szczegółów.
