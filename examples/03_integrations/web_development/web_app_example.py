#!/usr/bin/env python3
"""
Prosty przykład aplikacji webowej używającej nlp2cmd jako backendu.

Uruchomienie:
    pip install fastapi uvicorn
    python web_app_example.py

Następnie otwórz http://localhost:8000 w przeglądarce.
"""

import sys
from pathlib import Path
# Dodaj ścieżkę do src
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from fastapi import FastAPI, HTTPException, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import asyncio
import json
from datetime import datetime

# Import NLP2CMD
from nlp2cmd_web_controller import NLP2CMDWebAPI

# Inicjalizacja aplikacji FastAPI
app = FastAPI(
    title="NLP2CMD Web Interface",
    description="Interfejs webowy do generowania komend z języka naturalnego",
    version="1.0.0"
)

# Inicjalizacja API nlp2cmd
nlp_api = NLP2CMDWebAPI()

# Templates dla interfejsu webowego
templates = Jinja2Templates(directory="templates")

# Modele danych
class CommandRequest(BaseModel):
    command: str
    dsl: str = "auto"

class CommandResponse(BaseModel):
    status: str
    message: str
    command: Optional[str] = None
    action: Optional[str] = None
    dsl: Optional[str] = None
    confidence: Optional[float] = None
    llm_used: Optional[bool] = None

class HistoryResponse(BaseModel):
    status: str
    history: List[Dict[str, Any]]
    total: int

# Endpointy API
@app.post("/api/process", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    """Przetwarzaj komendę z języka naturalnego."""
    try:
        result = await nlp_api.process_command(request.command, request.dsl)
        
        if result["status"] == "error":
            raise HTTPException(status_code=400, detail=result)
        
        return CommandResponse(
            status=result["status"],
            message=result.get("message", ""),
            command=result.get("command"),
            action=result.get("action"),
            dsl=result.get("dsl"),
            confidence=result.get("confidence"),
            llm_used=result.get("llm_used", False)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/status")
async def get_status():
    """Pobierz status API."""
    return nlp_api.get_status()

@app.get("/api/history", response_model=HistoryResponse)
async def get_history(limit: int = 10):
    """Pobierz historię komend."""
    return nlp_api.get_history(limit)

@app.get("/api/services")
async def get_services():
    """Pobierz wdrożone usługi."""
    return nlp_api.get_services()

# Endpointy HTML
@app.get("/")
async def home(request: Request):
    """Strona główna z interfejsem użytkownika."""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "title": "NLP2CMD - Natural Language to Commands"
    })

@app.get("/history")
async def history_page(request: Request):
    """Strona z historią komend."""
    history_data = nlp_api.get_history(20)
    return templates.TemplateResponse("history.html", {
        "request": request,
        "title": "Historia - NLP2CMD",
        "history": history_data["history"],
        "total": history_data["total"]
    })

@app.get("/services")
async def services_page(request: Request):
    """Strona z usługami."""
    services_data = nlp_api.get_services()
    return templates.TemplateResponse("services.html", {
        "request": request,
        "title": "Usługi - NLP2CMD",
        "services": services_data["services"],
        "total": services_data["total"]
    })

# Przykładowe komendy dla interfejsu
EXAMPLE_COMMANDS = [
    {"command": "Uruchom docker", "description": "Uruchamia kontener Dockera"},
    {"command": "Pokaż logi kontenera", "description": "Wyświetla logi kontenera"},
    {"command": "Stwórz plik konfiguracyjny", "description": "Tworzy nowy plik konfiguracyjny"},
    {"command": "Uruchom serwis czatu na porcie 8080", "description": "Wdraża serwis czatu"},
    {"command": "Skonfiguruj email dla jan@example.com", "description": "Konfiguruje usługę email"},
    {"command": "Pokaż status usług", "description": "Wyświetla status wszystkich usług"},
    {"command": "Skaluj serwis do 3 replik", "description": "Skaluje liczbę replik"},
    {"command": "Zrestartuj kontener bazy danych", "description": "Restartuje kontener bazy"},
]

@app.get("/api/examples")
async def get_examples():
    """Pobierz przykładowe komendy."""
    return {"examples": EXAMPLE_COMMANDS}

if __name__ == "__main__":
    import uvicorn
    
    print("🚀 Uruchamianie NLP2CMD Web Interface...")
    print("📝 Otwórz http://localhost:8001 w przeglądarce")
    print("🔗 API dostępne pod http://localhost:8001/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)
