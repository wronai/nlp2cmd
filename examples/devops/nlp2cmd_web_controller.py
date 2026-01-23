"""
NLP2CMD Web Controller - Natural Language DevOps Layer.

This module provides a control plane that interprets natural language commands
to configure and manage web application infrastructure.

Example usage:
    controller = NLP2CMDWebController()
    
    # Deploy a chat service
    await controller.execute("Uruchom serwis czatu na porcie 8080 z Redis jako backend")
    
    # Configure email integration
    await controller.execute("Skonfiguruj klienta email dla konta jan@example.com")
"""

from __future__ import annotations

import asyncio
import json
import os
import subprocess
import yaml
from dataclasses import dataclass, field
from typing import Any, Callable, Optional
from enum import Enum
from pathlib import Path
from datetime import datetime

# Import NLP2CMD core components
from nlp2cmd.core import NLP2CMD, LLMBackend
from nlp2cmd.generation.llm_simple import LiteLLMClient
from nlp2cmd.adapters.shell import ShellAdapter
from nlp2cmd.adapters.docker import DockerAdapter
from nlp2cmd.adapters.kubernetes import KubernetesAdapter


class ServiceType(Enum):
    """Types of services that can be managed."""
    FRONTEND = "frontend"
    BACKEND_API = "backend_api"
    DATABASE = "database"
    CACHE = "cache"
    MESSAGE_QUEUE = "message_queue"
    EMAIL_SERVICE = "email_service"
    CHAT_SERVICE = "chat_service"
    CONTACT_FORM = "contact_form"


@dataclass
class ServiceConfig:
    """Configuration for a managed service."""
    name: str
    service_type: ServiceType
    port: int
    image: Optional[str] = None
    env_vars: dict[str, str] = field(default_factory=dict)
    volumes: list[str] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)
    healthcheck: Optional[str] = None
    replicas: int = 1


@dataclass
class DeploymentPlan:
    """Plan for deploying services."""
    services: list[ServiceConfig]
    network: str = "nlp2cmd-network"
    compose_version: str = "3.8"
    
    def to_compose(self) -> dict[str, Any]:
        """Convert to docker-compose format."""
        services = {}
        dependency_services = {}
        
        for svc in self.services:
            service_def = {
                "image": svc.image or f"nlp2cmd/{svc.name}:latest",
                "ports": [f"{svc.port}:{svc.port}"],
                "environment": svc.env_vars,
                "networks": [self.network],
            }
            if svc.volumes:
                service_def["volumes"] = svc.volumes
            if svc.depends_on:
                service_def["depends_on"] = svc.depends_on
                # Auto-add dependency services
                for dep in svc.depends_on:
                    if dep == "redis" and dep not in dependency_services:
                        dependency_services[dep] = self._create_redis_service()
                    elif dep == "postgres" and dep not in dependency_services:
                        dependency_services[dep] = self._create_postgres_service()
            if svc.healthcheck:
                service_def["healthcheck"] = {
                    "test": svc.healthcheck,
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3,
                }
            if svc.replicas > 1:
                service_def["deploy"] = {"replicas": svc.replicas}
            
            services[svc.name] = service_def
        
        # Add dependency services
        services.update(dependency_services)
        
        # Collect all volumes from services
        volumes = {}
        for service_name, service_def in services.items():
            if 'volumes' in service_def:
                for volume in service_def['volumes']:
                    if ':' in volume and not volume.startswith('/'):
                        # Named volume (e.g., "postgres_data:/var/lib/postgresql/data")
                        volume_name = volume.split(':')[0]
                        volumes[volume_name] = None  # Use default driver
        
        return {
            "services": services,
            "networks": {
                self.network: {"driver": "bridge"}
            },
            "volumes": volumes
        }
    
    def _create_redis_service(self) -> dict[str, Any]:
        """Create Redis service configuration."""
        return {
            "image": "redis:7-alpine",
            "ports": ["6379:6379"],
            "networks": [self.network],
        }
    
    def _create_postgres_service(self) -> dict[str, Any]:
        """Create PostgreSQL service configuration."""
        return {
            "image": "postgres:15-alpine",
            "ports": ["5432:5432"],
            "environment": {
                "POSTGRES_DB": "nlp2cmd_db",
                "POSTGRES_USER": "nlp2cmd",
                "POSTGRES_PASSWORD": "${DB_PASSWORD}"
            },
            "networks": [self.network],
            "volumes": ["postgres_data:/var/lib/postgresql/data"],
            "healthcheck": {
                "test": "pg_isready -U nlp2cmd",
                "interval": "30s",
                "timeout": "10s",
                "retries": 3,
            }
        }


class OutputFileManager:
    """Manages saving generated configurations to files."""
    
    def __init__(self, output_dir: str = "./generated"):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(exist_ok=True)
    
    def save_docker_compose(self, compose_config: dict[str, Any], filename: str = "docker-compose.yml") -> str:
        """Save Docker Compose configuration to file."""
        filepath = self.output_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("# Generated by NLP2CMD\n")
            f.write("# Natural Language to DevOps Configuration\n")
            f.write(f"# Generated at: {datetime.now().isoformat()}\n\n")
            yaml.dump(compose_config, f, default_flow_style=False, sort_keys=False)
        
        return str(filepath)
    
    def save_service_config(self, service_config: dict[str, Any], service_name: str) -> str:
        """Save individual service configuration to JSON file."""
        filepath = self.output_dir / f"{service_name}-config.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(service_config, f, indent=2, ensure_ascii=False)
        
        return str(filepath)
    
    def save_deployment_plan(self, plan: dict[str, Any], name: str) -> str:
        """Save complete deployment plan to JSON file."""
        filepath = self.output_dir / f"{name}-deployment.json"
        
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(plan, f, indent=2, ensure_ascii=False)
        
        return str(filepath)


class DockerManager:
    """Manages Docker Compose operations and container lifecycle."""
    
    def __init__(self, compose_file_path: str, output_dir: str = "./generated"):
        self.compose_file = Path(output_dir) / compose_file_path
        self.compose_dir = Path(output_dir)
        self.running_containers = set()
    
    async def start_services(self, show_logs: bool = True) -> dict[str, Any]:
        """Start Docker Compose services and optionally show logs."""
        if not self.compose_file.exists():
            return {
                "status": "error",
                "message": f"Plik Docker Compose nie istnieje: {self.compose_file}"
            }
        
        try:
            # Start services in detached mode
            print(f"\n🚀 Uruchamianie usług z: {self.compose_file}")
            print("-" * 50)
            
            result = subprocess.run(
                ["docker-compose", "-f", self.compose_file.name, "up", "-d"],
                cwd=self.compose_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                return {
                    "status": "error",
                    "message": f"Błąd uruchamiania: {result.stderr}"
                }
            
            print("✅ Usługi uruchomione pomyślnie")
            
            # Get container status
            status_result = await self.get_container_status()
            
            # Show logs if requested
            if show_logs:
                await self.show_logs(follow=False, lines=10)
            
            return {
                "status": "success",
                "message": "Usługi uruchomione pomyślnie",
                "container_status": status_result
            }
            
        except subprocess.TimeoutExpired:
            return {
                "status": "error",
                "message": "Timeout podczas uruchamiania usług"
            }
        except Exception as e:
            return {
                "status": "error",
                "message": f"Błąd: {str(e)}"
            }
    
    async def get_container_status(self) -> dict[str, Any]:
        """Get status of all containers."""
        try:
            result = subprocess.run(
                ["docker-compose", "-f", self.compose_file.name, "ps"],
                cwd=self.compose_dir,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                # Skip header line (first line with column names)
                container_lines = [line.strip() for line in lines[1:] if line.strip()]
                
                containers = []
                for line in container_lines:
                    parts = line.split()
                    if len(parts) >= 6:
                        container_name = parts[0]
                        image = parts[1]
                        
                        # Find status column (contains "Up" or other status)
                        status = "unknown"
                        ports = ""
                        
                        # Status is typically around column 5-6, look for "Up"
                        for i, part in enumerate(parts):
                            if part == "Up" and i > 0:
                                # Status spans from this position to before ports
                                status = " ".join(parts[i:i+3])  # Up + time info
                                # Find ports (usually after status)
                                if i + 3 < len(parts):
                                    remaining = " ".join(parts[i+3:])
                                    if "->" in remaining:
                                        ports = remaining
                                break
                        
                        containers.append({
                            "name": container_name,
                            "status": status,
                            "ports": ports,
                            "image": image
                        })
                
                return {
                    "status": "success",
                    "containers": containers,
                    "total": len(containers)
                }
            else:
                return {
                    "status": "error",
                    "message": f"Błąd sprawdzania statusu: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Błąd sprawdzania statusu: {str(e)}"
            }
    
    async def show_logs(self, follow: bool = False, lines: int = 20, service: Optional[str] = None) -> None:
        """Show logs from containers."""
        try:
            cmd = ["docker-compose", "-f", self.compose_file.name, "logs"]
            
            if follow:
                cmd.append("--follow")
            if lines:
                cmd.extend(["--tail", str(lines)])
            if service:
                cmd.append(service)
            
            print(f"\n📋 Logi kontenerów{' (follow)' if follow else ''}:")
            print("-" * 50)
            
            if follow:
                # For follow mode, we need to stream the output
                process = subprocess.Popen(
                    cmd,
                    cwd=self.compose_dir,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1
                )
                
                try:
                    for line in iter(process.stdout.readline, ''):
                        if line:
                            print(line.rstrip())
                        else:
                            break
                except KeyboardInterrupt:
                    print("\n👋 Przerywam pokazywanie logów...")
                    process.terminate()
                    process.wait()
            else:
                # For non-follow mode, just capture and show
                result = subprocess.run(
                    cmd,
                    cwd=self.compose_dir,
                    capture_output=True,
                    text=True,
                    timeout=15
                )
                
                if result.stdout:
                    print(result.stdout)
                if result.stderr:
                    print(f"⚠️ Błędy: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            print("⏰ Timeout podczas pobierania logów")
        except Exception as e:
            print(f"❌ Błąd pokazywania logów: {str(e)}")
    
    async def stop_services(self) -> dict[str, Any]:
        """Stop and remove containers."""
        try:
            print(f"\n🛑 Zatrzymywanie usług...")
            
            result = subprocess.run(
                ["docker-compose", "-f", self.compose_file.name, "down"],
                cwd=self.compose_dir,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                print("✅ Usługi zatrzymane pomyślnie")
                return {
                    "status": "success",
                    "message": "Usługi zatrzymane i usunięte"
                }
            else:
                return {
                    "status": "error",
                    "message": f"Błąd zatrzymywania: {result.stderr}"
                }
                
        except Exception as e:
            return {
                "status": "error",
                "message": f"Błąd zatrzymywania: {str(e)}"
            }


class NLCommandParser:
    """
    Parse natural language commands into structured actions.
    
    Supports Polish and English commands for:
    - Service deployment (uruchom, deploy, start)
    - Configuration (skonfiguruj, configure, setup)
    - Scaling (skaluj, scale)
    - Monitoring (pokaż, show, status)
    """
    
    # Intent patterns (Polish + English)
    DEPLOY_PATTERNS = [
        "uruchom", "deploy", "start", "wystartuj", "włącz", "run",
        "utwórz", "create", "zbuduj", "build"
    ]
    
    CONFIG_PATTERNS = [
        "skonfiguruj", "configure", "setup", "ustaw", "set",
        "połącz", "connect", "podłącz"
    ]
    
    SCALE_PATTERNS = [
        "skaluj", "scale", "zwiększ", "increase", "zmniejsz", "decrease"
    ]
    
    STATUS_PATTERNS = [
        "pokaż", "show", "status", "sprawdź", "check", "list", "wyświetl"
    ]
    
    STOP_PATTERNS = [
        "zatrzymaj", "stop", "wyłącz", "disable", "usuń", "remove", "delete"
    ]
    
    TEST_PATTERNS = [
        "testuj", "test", "sprawdź działanie", "ping", "połącz", "verify", "validate"
    ]
    
    MONITOR_PATTERNS = [
        "monitoring", "monitoruj", "zużycie", "zasoby", "resource", "metrics", "dashboard"
    ]
    
    LOG_PATTERNS = [
        "logi", "logs", "dziennik", "journal", "show logs", "pokaż logi"
    ]
    
    RESTART_PATTERNS = [
        "restartuj", "zrestartuj", "uruchom ponownie", "reboot", "reload"
    ]
    
    # Service type detection
    SERVICE_KEYWORDS = {
        ServiceType.CHAT_SERVICE: ["czat", "chat", "komunikator", "messenger", "websocket"],
        ServiceType.EMAIL_SERVICE: ["email", "mail", "poczta", "imap", "smtp"],
        ServiceType.CONTACT_FORM: ["kontakt", "contact", "formularz", "form"],
        ServiceType.DATABASE: ["baza", "database", "db", "postgres", "mysql", "mongo"],
        ServiceType.CACHE: ["cache", "redis", "memcached", "pamięć"],
        ServiceType.FRONTEND: ["frontend", "react", "vue", "angular", "strona", "page"],
        ServiceType.BACKEND_API: ["api", "backend", "serwer", "server", "rest"],
    }
    
    def parse(self, text: str) -> dict[str, Any]:
        """Parse natural language command."""
        text_lower = text.lower()
        
        # Detect intent
        intent = self._detect_intent(text_lower)
        
        # Detect service type
        service_type = self._detect_service_type(text_lower)
        
        # Extract entities
        entities = self._extract_entities(text_lower)
        
        return {
            "intent": intent,
            "service_type": service_type,
            "entities": entities,
            "original_text": text,
        }
    
    def _detect_intent(self, text: str) -> str:
        """Detect command intent."""
        for pattern in self.DEPLOY_PATTERNS:
            if pattern in text:
                return "deploy"
        
        for pattern in self.CONFIG_PATTERNS:
            if pattern in text:
                return "configure"
        
        for pattern in self.SCALE_PATTERNS:
            if pattern in text:
                return "scale"
        
        for pattern in self.STATUS_PATTERNS:
            if pattern in text:
                return "status"
        
        for pattern in self.LOG_PATTERNS:
            if pattern in text:
                return "logs"
        
        for pattern in self.TEST_PATTERNS:
            if pattern in text:
                return "test"
        
        for pattern in self.MONITOR_PATTERNS:
            if pattern in text:
                return "monitor"
        
        for pattern in self.RESTART_PATTERNS:
            if pattern in text:
                return "restart"
        
        for pattern in self.STOP_PATTERNS:
            if pattern in text:
                return "stop"
        
        return "unknown"
    
    def _detect_service_type(self, text: str) -> Optional[ServiceType]:
        """Detect service type from text."""
        for svc_type, keywords in self.SERVICE_KEYWORDS.items():
            for keyword in keywords:
                if keyword in text:
                    return svc_type
        return None
    
    def _extract_entities(self, text: str) -> dict[str, Any]:
        """Extract entities from text."""
        import re
        
        entities = {}
        
        # Extract port numbers
        port_match = re.search(r'port[ue]?\s*[:=]?\s*(\d+)|na\s+porcie\s+(\d+)|:(\d+)', text)
        if port_match:
            entities["port"] = int(next(g for g in port_match.groups() if g))
        
        # Extract email addresses
        email_match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
        if email_match:
            entities["email"] = email_match.group()
        
        # Extract hostnames/URLs
        host_match = re.search(r'host[a]?\s*[:=]?\s*([\w\.-]+)|serwer[a]?\s+([\w\.-]+)', text)
        if host_match:
            entities["host"] = next(g for g in host_match.groups() if g)
        
        # Extract replica count
        replica_match = re.search(r'(\d+)\s*(replik|instancj|kopii|replicas?|instances?)', text)
        if replica_match:
            entities["replicas"] = int(replica_match.group(1))
        
        # Extract database name
        db_match = re.search(r'baz[aęy]\s+([\w_]+)|database\s+([\w_]+)', text)
        if db_match:
            entities["database"] = next(g for g in db_match.groups() if g)
        
        # Extract credentials hints
        if "hasło" in text or "password" in text:
            entities["needs_password"] = True
        if "użytkownik" in text or "user" in text:
            entities["needs_username"] = True
        
        return entities


class NLP2CMDWebController:
    """
    Main controller for NLP2CMD-powered web infrastructure.
    
    This class orchestrates the deployment and management of web services
    based on natural language commands, with integrated LLM fallback.
    """
    
    def __init__(self, output_dir: str = "./generated", use_llm_fallback: bool = True, auto_install: bool = False):
        self.parser = NLCommandParser()
        self.services: dict[str, ServiceConfig] = {}
        self.deployment_history: list[dict[str, Any]] = []
        self.file_manager = OutputFileManager(output_dir)
        self.docker_manager: Optional[DockerManager] = None
        self.use_llm_fallback = use_llm_fallback
        self.auto_install = auto_install
        
        # Initialize NLP2CMD components
        self.nlp2cmd_instances = {
            "shell": NLP2CMD(adapter=ShellAdapter()),
            "docker": NLP2CMD(adapter=DockerAdapter()),
            "kubernetes": NLP2CMD(adapter=KubernetesAdapter()),
        }
        
        # Initialize LLM fallback if enabled
        if self.use_llm_fallback:
            try:
                self.llm_client = LiteLLMClient()
            except ImportError:
                if auto_install:
                    import subprocess
                    subprocess.run(["pip", "install", "litellm"], check=True, capture_output=True)
                    self.llm_client = LiteLLMClient()
                else:
                    self.llm_client = None
        else:
            self.llm_client = None
        
        # Service templates
        self.templates = {
            ServiceType.CHAT_SERVICE: self._create_chat_template,
            ServiceType.EMAIL_SERVICE: self._create_email_template,
            ServiceType.CONTACT_FORM: self._create_contact_template,
            ServiceType.DATABASE: self._create_database_template,
            ServiceType.CACHE: self._create_cache_template,
        }
    
    async def execute(self, command: str, dsl: str = "auto") -> dict[str, Any]:
        """
        Execute a natural language command.
        
        Args:
            command: Natural language command in Polish or English
            dsl: DSL type to use (auto, shell, docker, kubernetes)
            
        Returns:
            Result dictionary with status and generated configurations
        """
        # First try the custom parser for DevOps-specific commands
        parsed = self.parser.parse(command)
        
        # If it's a DevOps command we understand, handle it
        if parsed["intent"] != "unknown" and parsed["service_type"] is not None:
            # Route to handler
            handlers = {
                "deploy": self._handle_deploy,
                "configure": self._handle_configure,
                "scale": self._handle_scale,
                "status": self._handle_status,
                "logs": self._handle_logs,
                "test": self._handle_test,
                "monitor": self._handle_monitor,
                "restart": self._handle_restart,
                "stop": self._handle_stop,
            }
            
            handler = handlers.get(parsed["intent"], self._handle_unknown)
            result = await handler(parsed)
        else:
            # Fall back to NLP2CMD core for general commands
            result = await self._execute_with_nlp2cmd(command, dsl)
        
        # Record in history
        self.deployment_history.append({
            "command": command,
            "parsed": parsed,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        
        return result
    
    async def _handle_deploy(self, parsed: dict) -> dict[str, Any]:
        """Handle deploy intent."""
        service_type = parsed.get("service_type")
        entities = parsed.get("entities", {})
        
        if service_type and service_type in self.templates:
            # Create service from template
            config = self.templates[service_type](entities)
            self.services[config.name] = config
            
            # Generate deployment artifacts
            plan = DeploymentPlan(services=[config])
            compose = plan.to_compose()
            
            # Save files to disk
            compose_file = self.file_manager.save_docker_compose(compose, f"{config.name}-docker-compose.yml")
            service_file = self.file_manager.save_service_config({
                "name": config.name,
                "service_type": config.service_type.value,
                "port": config.port,
                "image": config.image,
                "env_vars": config.env_vars,
                "volumes": config.volumes,
                "depends_on": config.depends_on,
                "healthcheck": config.healthcheck,
                "replicas": config.replicas,
            }, config.name)
            
            # Initialize Docker manager and start services
            compose_filename = f"{config.name}-docker-compose.yml"
            self.docker_manager = DockerManager(compose_filename, self.file_manager.output_dir)
            docker_result = await self.docker_manager.start_services(show_logs=False)
            
            result = {
                "status": "success",
                "action": "deploy",
                "service": config.name,
                "config": {
                    "port": config.port,
                    "image": config.image,
                    "env_vars": config.env_vars,
                },
                "docker_compose": compose,
                "files_saved": {
                    "docker_compose": compose_file,
                    "service_config": service_file,
                },
                "docker_execution": docker_result,
                "message": f"Przygotowano deployment dla {config.name} na porcie {config.port}",
                "note": f"Pliki zapisane w: {self.file_manager.output_dir}"
            }
            
            # Show container status if Docker started successfully
            if docker_result.get("status") == "success":
                container_status = docker_result.get("container_status", {})
                if container_status.get("containers"):
                    result["containers"] = container_status["containers"]
                    result["container_count"] = container_status["total"]
            
            return result
        
        return {
            "status": "error",
            "message": "Nie rozpoznano typu usługi. Dostępne: chat, email, contact, database, cache",
        }
    
    async def _handle_configure(self, parsed: dict) -> dict[str, Any]:
        """Handle configure intent."""
        service_type = parsed.get("service_type")
        entities = parsed.get("entities", {})
        
        if service_type == ServiceType.EMAIL_SERVICE:
            return await self._configure_email(entities)
        
        if service_type == ServiceType.CHAT_SERVICE:
            return await self._configure_chat(entities)
        
        return {
            "status": "needs_input",
            "message": "Potrzebuję więcej informacji do konfiguracji.",
            "required": ["service_type", "credentials"],
        }
    
    async def _handle_scale(self, parsed: dict) -> dict[str, Any]:
        """Handle scale intent."""
        entities = parsed.get("entities", {})
        replicas = entities.get("replicas", 2)
        
        return {
            "status": "success",
            "action": "scale",
            "replicas": replicas,
            "kubectl_command": f"kubectl scale deployment --replicas={replicas}",
            "docker_command": f"docker-compose up --scale service={replicas}",
        }
    
    async def _handle_status(self, parsed: dict) -> dict[str, Any]:
        """Handle status intent."""
        return {
            "status": "success",
            "action": "status",
            "services": {name: {"port": cfg.port, "type": cfg.service_type.value} 
                        for name, cfg in self.services.items()},
            "commands": {
                "docker": "docker-compose ps",
                "kubernetes": "kubectl get pods",
            }
        }
    
    async def _handle_stop(self, parsed: dict) -> dict[str, Any]:
        """Handle stop intent."""
        return {
            "status": "success",
            "action": "stop",
            "commands": {
                "docker": "docker-compose down",
                "kubernetes": "kubectl delete deployment",
            }
        }
    
    async def _handle_unknown(self, parsed: dict) -> dict[str, Any]:
        """
        Handle unknown intent by trying NLP2CMD core with LLM fallback.
        """
        command = parsed.get("original_text", "")
        
        # Try NLP2cmd core as fallback
        result = await self._execute_with_nlp2cmd(command, "auto")
        
        if result.get("status") == "error":
            return {
                "status": "clarification_needed",
                "message": "Nie zrozumiałem polecenia. Przykłady:",
                "examples": [
                    "Uruchom serwis czatu na porcie 8080",
                    "Skonfiguruj email dla jan@example.com",
                    "Pokaż status usług",
                    "Uruchom docker",
                    "Stwórz plik konfiguracyjny",
                ],
                "nlp2cmd_result": result,
            }
        
        return result
    
    async def _execute_with_nlp2cmd(self, command: str, dsl: str) -> dict[str, Any]:
        """
        Execute command using NLP2CMD core with LLM fallback.
        """
        try:
            # Use the appropriate NLP2CMD instance
            nlp2cmd = self.nlp2cmd_instances.get(dsl, self.nlp2cmd_instances["shell"])
            
            # Transform the command
            result = nlp2cmd.transform(command)
            
            if result.command and not result.command.startswith("#"):
                return {
                    "status": "success",
                    "action": "command_generated",
                    "command": result.command,
                    "dsl": dsl,
                    "confidence": getattr(result, "confidence", 0.0),
                    "plan": result.plan.model_dump() if hasattr(result, "plan") else None,
                    "message": f"Wygenerowano komendę: {result.command}",
                }
            else:
                # Try LLM fallback if enabled
                if self.use_llm_fallback and self.llm_client:
                    return await self._try_llm_fallback(command)
                else:
                    return {
                        "status": "error",
                        "message": "Nie udało się wygenerować komendy",
                        "suggestion": "Włącz --auto-install aby użyć LLM fallback",
                    }
        
        except Exception as e:
            return {
                "status": "error",
                "message": f"Błąd podczas przetwarzania: {str(e)}",
            }
    
    async def _try_llm_fallback(self, command: str) -> dict[str, Any]:
        """
        Try to generate command using LLM fallback.
        """
        try:
            system_prompt = """Jesteś ekspertem linii komend. Konwertuj prośbę użytkownika na prawidłową komendę shell.

Zasady:
- Odpowiedz TYLKO komendą, bez wyjaśnień
- Używaj standardowych komend shell/Dockera
- Dla polskich słów kluczowych (uruchom, stwórz, pokaż) użyj odpowiedników angielskich
- Trzymaj komendy proste i wykonywalne"""
            
            response = await self.llm_client.complete(
                user=command,
                system=system_prompt,
                max_tokens=200,
                temperature=0.1
            )
            
            command = response.strip()
            
            if command and not command.startswith("#") and not command.lower().startswith(("i'm sorry", "sorry", "i cannot", "cannot")):
                return {
                    "status": "success",
                    "action": "llm_fallback",
                    "command": command,
                    "dsl": "shell",
                    "message": "Wygenerowano komendę za pomocą LLM fallback",
                    "llm_used": True,
                }
            else:
                return {
                    "status": "error",
                    "message": "LLM fallback nie udał się wygenerować prawidłowej komendy",
                }
        except Exception as e:
            return {
                "status": "error",
                "message": f"LLM fallback nieudany: {str(e)}",
            }
    
    async def _handle_logs(self, parsed: dict) -> dict[str, Any]:
        """Handle logs intent."""
        service_type = parsed.get("service_type")
        
        if service_type:
            service_name = self._get_service_name_by_type(service_type)
            return {
                "status": "success",
                "action": "logs",
                "service": service_name,
                "message": f"Pokazywanie logów dla {service_name}",
                "docker_command": f"docker-compose logs -f {service_name}" if service_name else "docker-compose logs -f"
            }
        else:
            return {
                "status": "success",
                "action": "logs",
                "message": "Pokazywanie logów wszystkich usług",
                "docker_command": "docker-compose logs -f"
            }
    
    async def _handle_test(self, parsed: dict) -> dict[str, Any]:
        """Handle test intent."""
        service_type = parsed.get("service_type")
        entities = parsed.get("entities", {})
        
        if service_type:
            service_name = self._get_service_name_by_type(service_type)
            return {
                "status": "success",
                "action": "test",
                "service": service_name,
                "message": f"Testowanie połączenia z {service_name}",
                "test_commands": self._get_test_commands(service_type, entities)
            }
        else:
            return {
                "status": "needs_input",
                "message": "Potrzebuję więcej informacji do konfiguracji.",
                "required": ["service_type"]
            }
    
    async def _handle_monitor(self, parsed: dict) -> dict[str, Any]:
        """Handle monitor intent."""
        return {
            "status": "success",
            "action": "monitor",
            "message": "Uruchamianie monitoringu usług",
            "monitoring_tools": ["docker stats", "htop", "docker-compose ps"],
            "dashboard_url": "http://localhost:3000/grafana"
        }
    
    async def _handle_restart(self, parsed: dict) -> dict[str, Any]:
        """Handle restart intent."""
        service_type = parsed.get("service_type")
        
        if service_type:
            service_name = self._get_service_name_by_type(service_type)
            return {
                "status": "success",
                "action": "restart",
                "service": service_name,
                "message": f"Restartowanie {service_name}",
                "docker_command": f"docker-compose restart {service_name}"
            }
        else:
            return {
                "status": "success",
                "action": "restart",
                "message": "Restartowanie wszystkich usług",
                "docker_command": "docker-compose restart"
            }
    
    def _get_service_name_by_type(self, service_type: ServiceType) -> str:
        """Get service name by service type."""
        type_to_name = {
            ServiceType.CHAT_SERVICE: "chat-service",
            ServiceType.EMAIL_SERVICE: "email-service",
            ServiceType.CONTACT_FORM: "contact-service",
            ServiceType.DATABASE: "postgres",
            ServiceType.CACHE: "redis",
        }
        return type_to_name.get(service_type, "unknown")
    
    def _get_test_commands(self, service_type: ServiceType, entities: dict) -> list[str]:
        """Get test commands for service type."""
        commands = []
        
        if service_type == ServiceType.CACHE:
            commands.append("docker exec redis redis-cli ping")
            commands.append("telnet localhost 6379")
        elif service_type == ServiceType.DATABASE:
            commands.append("docker exec postgres pg_isready -U nlp2cmd")
            commands.append("psql -h localhost -U nlp2cmd -d postgresql -c 'SELECT 1;'")
        elif service_type == ServiceType.CHAT_SERVICE:
            port = entities.get("port", 8080)
            commands.append(f"curl -f http://localhost:{port}/health")
            commands.append(f"curl -f http://localhost:{port}/api/status")
        
        return commands
    
    async def save_full_deployment_plan(self, name: str = "full-deployment") -> dict[str, Any]:
        """Save complete deployment plan with all services."""
        if not self.services:
            return {
                "status": "error",
                "message": "Brak usług do zapisania. Najpierw dodaj usługi."
            }
        
        # Create deployment plan with all services
        plan = DeploymentPlan(services=list(self.services.values()))
        compose = plan.to_compose()
        
        # Save files
        compose_file = self.file_manager.save_docker_compose(compose, f"{name}-docker-compose.yml")
        
        # Include dependency services in deployment plan
        all_services = {}
        for name, config in self.services.items():
            all_services[name] = {
                "name": config.name,
                "service_type": config.service_type.value,
                "port": config.port,
                "image": config.image,
                "env_vars": config.env_vars,
                "volumes": config.volumes,
                "depends_on": config.depends_on,
                "healthcheck": config.healthcheck,
                "replicas": config.replicas,
            }
        
        # Add dependency services to the plan
        for service_name, service_def in compose["services"].items():
            if service_name not in all_services:
                # This is a dependency service (redis, postgres, etc.)
                if service_name == "redis":
                    all_services[service_name] = {
                        "name": service_name,
                        "service_type": "cache",
                        "port": 6379,
                        "image": "redis:7-alpine",
                        "env_vars": {},
                        "volumes": [],
                        "depends_on": [],
                        "healthcheck": None,
                        "replicas": 1,
                    }
                elif service_name == "postgres":
                    all_services[service_name] = {
                        "name": service_name,
                        "service_type": "database", 
                        "port": 5432,
                        "image": "postgres:15-alpine",
                        "env_vars": {
                            "POSTGRES_DB": "nlp2cmd_db",
                            "POSTGRES_USER": "nlp2cmd",
                            "POSTGRES_PASSWORD": "${DB_PASSWORD}"
                        },
                        "volumes": ["postgres_data:/var/lib/postgresql/data"],
                        "depends_on": [],
                        "healthcheck": "pg_isready -U nlp2cmd",
                        "replicas": 1,
                    }
        
        deployment_file = self.file_manager.save_deployment_plan({
            "services": all_services,
            "deployment_plan": compose,
            "generated_at": datetime.now().isoformat(),
            "total_services": len(all_services),
        }, name)
        
        return {
            "status": "success",
            "message": f"Zapisano pełen plan deployment z {len(all_services)} usługami (w tym zależności)",
            "files_saved": {
                "docker_compose": compose_file,
                "deployment_plan": deployment_file,
            },
            "output_directory": str(self.file_manager.output_dir)
        }
    
    def get_generated_files_info(self) -> dict[str, Any]:
        """Get information about generated files."""
        if not self.file_manager.output_dir.exists():
            return {
                "status": "info",
                "message": "Brak wygenerowanych plików",
                "output_directory": str(self.file_manager.output_dir)
            }
        
        files = []
        for file_path in self.file_manager.output_dir.iterdir():
            if file_path.is_file():
                files.append({
                    "name": file_path.name,
                    "path": str(file_path),
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(file_path.stat().st_mtime).isoformat()
                })
        
        return {
            "status": "info",
            "output_directory": str(self.file_manager.output_dir),
            "files": files,
            "total_files": len(files)
        }
    
    async def show_container_logs(self, follow: bool = False, lines: int = 20, service: Optional[str] = None) -> dict[str, Any]:
        """Show logs from running containers."""
        if not self.docker_manager:
            return {
                "status": "error",
                "message": "Brak aktywnego menedżera Docker. Najpierw uruchom usługę."
            }
        
        await self.docker_manager.show_logs(follow=follow, lines=lines, service=service)
        
        return {
            "status": "success",
            "message": "Logi wyświetlone"
        }
    
    async def get_container_status(self) -> dict[str, Any]:
        """Get current status of all containers."""
        if not self.docker_manager:
            return {
                "status": "error",
                "message": "Brak aktywnego menedżera Docker. Najpierw uruchom usługę."
            }
        
        return await self.docker_manager.get_container_status()
    
    async def stop_containers(self) -> dict[str, Any]:
        """Stop all running containers."""
        if not self.docker_manager:
            return {
                "status": "error",
                "message": "Brak aktywnego menedżera Docker. Najpierw uruchom usługę."
            }
        
        result = await self.docker_manager.stop_services()
        
        # Reset docker manager after stopping
        if result.get("status") == "success":
            self.docker_manager = None
        
        return result
    
    # Service templates
    def _create_chat_template(self, entities: dict) -> ServiceConfig:
        """Create chat service configuration."""
        port = entities.get("port", 8080)
        return ServiceConfig(
            name="chat-service",
            service_type=ServiceType.CHAT_SERVICE,
            port=port,
            image="nginx:alpine",  # Use nginx for testing
            env_vars={
                "PORT": str(port),
                "REDIS_URL": "redis://redis:6379",
                "WS_ENABLED": "true",
            },
            depends_on=["redis"],
        )
    
    def _create_email_template(self, entities: dict) -> ServiceConfig:
        """Create email service configuration."""
        port = entities.get("port", 8082)
        email = entities.get("email", "contact@example.com")
        
        # Extract domain from email for SMTP/IMAP hosts
        if "@" in email:
            domain = email.split("@")[1]
            imap_host = f"imap.{domain}"
            smtp_host = f"smtp.{domain}"
        else:
            imap_host = "imap.gmail.com"
            smtp_host = "smtp.gmail.com"
        
        return ServiceConfig(
            name="email-service",
            service_type=ServiceType.EMAIL_SERVICE,
            port=port,
            image="nginx:alpine",  # Use nginx for testing
            env_vars={
                "PORT": str(port),
                "EMAIL_ADDRESS": email,
                "IMAP_HOST": imap_host,
                "SMTP_HOST": smtp_host,
                "EMAIL_SERVICE_ENABLED": "true",
            },
        )
    
    def _create_contact_template(self, entities: dict) -> ServiceConfig:
        """Create contact form service configuration."""
        port = entities.get("port", 8081)
        email = entities.get("email", "contact@example.com")
        
        return ServiceConfig(
            name="contact-service",
            service_type=ServiceType.CONTACT_FORM,
            port=port,
            image="nginx:alpine",  # Use nginx for testing
            env_vars={
                "PORT": str(port),
                "CONTACT_FORM_ENABLED": "true",
                "RECIPIENT_EMAIL": email,
                "SMTP_HOST": "smtp.gmail.com",
            },
        )
    
    def _create_database_template(self, entities: dict) -> ServiceConfig:
        """Create database service configuration."""
        return ServiceConfig(
            name="postgres",
            service_type=ServiceType.DATABASE,
            port=5432,
            image="postgres:15-alpine",
            env_vars={
                "POSTGRES_DB": entities.get("database", "nlp2cmd_db"),
                "POSTGRES_USER": "nlp2cmd",
                "POSTGRES_PASSWORD": "${DB_PASSWORD}",
            },
            volumes=["postgres_data:/var/lib/postgresql/data"],
            healthcheck="pg_isready -U nlp2cmd",
        )
    
    def _create_cache_template(self, entities: dict) -> ServiceConfig:
        """Create cache service configuration."""
        return ServiceConfig(
            name="redis",
            service_type=ServiceType.CACHE,
            port=6379,
            image="redis:7-alpine",
            volumes=["redis_data:/data"],
            healthcheck="redis-cli ping",
        )
    
    async def _configure_email(self, entities: dict) -> dict[str, Any]:
        """Configure email service with credentials."""
        email = entities.get("email", "")
        
        return {
            "status": "configuration_ready",
            "service": "email",
            "config": {
                "email": email,
                "imap_host": self._guess_imap_host(email),
                "smtp_host": self._guess_smtp_host(email),
            },
            "env_file_content": f"""
# Email Configuration
EMAIL_ADDRESS={email}
EMAIL_PASSWORD=${{EMAIL_PASSWORD}}
IMAP_HOST={self._guess_imap_host(email)}
IMAP_PORT=993
SMTP_HOST={self._guess_smtp_host(email)}
SMTP_PORT=587
""".strip(),
            "next_step": "Ustaw zmienną EMAIL_PASSWORD w pliku .env",
        }
    
    async def _configure_chat(self, entities: dict) -> dict[str, Any]:
        """Configure chat service."""
        port = entities.get("port", 8080)
        
        return {
            "status": "configuration_ready",
            "service": "chat",
            "config": {
                "port": port,
                "websocket_path": "/ws",
                "redis_required": True,
            },
            "message": f"Serwis czatu gotowy na porcie {port}",
        }
    
    def _guess_imap_host(self, email: str) -> str:
        """Guess IMAP host from email domain."""
        if not email or "@" not in email:
            return "imap.example.com"
        
        domain = email.split("@")[1].lower()
        
        known_hosts = {
            "gmail.com": "imap.gmail.com",
            "outlook.com": "outlook.office365.com",
            "hotmail.com": "outlook.office365.com",
            "yahoo.com": "imap.mail.yahoo.com",
            "wp.pl": "imap.wp.pl",
            "onet.pl": "imap.poczta.onet.pl",
            "interia.pl": "imap.interia.pl",
        }
        
        return known_hosts.get(domain, f"imap.{domain}")
    
    def _guess_smtp_host(self, email: str) -> str:
        """Guess SMTP host from email domain."""
        if not email or "@" not in email:
            return "smtp.example.com"
        
        domain = email.split("@")[1].lower()
        
        known_hosts = {
            "gmail.com": "smtp.gmail.com",
            "outlook.com": "smtp.office365.com",
            "hotmail.com": "smtp.office365.com",
            "yahoo.com": "smtp.mail.yahoo.com",
            "wp.pl": "smtp.wp.pl",
            "onet.pl": "smtp.poczta.onet.pl",
            "interia.pl": "smtp.interia.pl",
        }
        
        return known_hosts.get(domain, f"smtp.{domain}")


# Convenience function
async def run_command(command: str, dsl: str = "auto", use_llm: bool = True, auto_install: bool = False) -> dict[str, Any]:
    """Quick way to run a single NLP2CMD command."""
    controller = NLP2CMDWebController(use_llm_fallback=use_llm, auto_install=auto_install)
    return await controller.execute(command, dsl=dsl)


# Flask/FastAPI integration example
class NLP2CMDWebAPI:
    """
    Example web API integration for NLP2CMD.
    
    This class shows how to integrate NLP2CMD with web frameworks
    like Flask or FastAPI.
    """
    
    def __init__(self):
        self.controller = NLP2CMDWebController(
            output_dir="./web_generated",
            use_llm_fallback=True,
            auto_install=True
        )
    
    async def process_command(self, command: str, dsl: str = "auto") -> dict[str, Any]:
        """
        Process command from web interface.
        
        Returns JSON-serializable result.
        """
        try:
            result = await self.controller.execute(command, dsl)
            
            # Add web-specific metadata
            result["web_api"] = {
                "version": "1.0",
                "timestamp": datetime.now().isoformat(),
                "processed_by": "nlp2cmd-web-api",
            }
            
            return result
        except Exception as e:
            return {
                "status": "error",
                "message": f"Web API error: {str(e)}",
                "web_api": {
                    "version": "1.0",
                    "timestamp": datetime.now().isoformat(),
                    "error": True,
                },
            }
    
    def get_status(self) -> dict[str, Any]:
        """Get API status and capabilities."""
        return {
            "status": "running",
            "capabilities": {
                "devops_commands": True,
                "llm_fallback": True,
                "auto_install": True,
                "supported_dsls": ["shell", "docker", "kubernetes", "auto"],
                "languages": ["pl", "en"],
            },
            "endpoints": {
                "/process": "POST - Process natural language command",
                "/status": "GET - Get API status",
                "/history": "GET - Get command history",
                "/services": "GET - List deployed services",
            },
        }
    
    def get_history(self, limit: int = 10) -> dict[str, Any]:
        """Get command history."""
        history = self.controller.deployment_history[-limit:]
        return {
            "status": "success",
            "history": history,
            "total": len(history),
        }
    
    def get_services(self) -> dict[str, Any]:
        """Get deployed services."""
        services = {}
        for name, config in self.controller.services.items():
            services[name] = {
                "type": config.service_type.value,
                "port": config.port,
                "image": config.image,
                "status": "deployed",
            }
        
        return {
            "status": "success",
            "services": services,
            "total": len(services),
        }


# Example FastAPI endpoint definitions
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class CommandRequest(BaseModel):
    command: str
    dsl: str = "auto"

class CommandResponse(BaseModel):
    status: str
    message: str
    command: Optional[str] = None
    action: Optional[str] = None

app = FastAPI(title="NLP2CMD Web API", version="1.0")
nlp_api = NLP2CMDWebAPI()

@app.post("/process", response_model=CommandResponse)
async def process_command(request: CommandRequest):
    result = await nlp_api.process_command(request.command, request.dsl)
    if result["status"] == "error":
        raise HTTPException(status_code=400, detail=result)
    return result

@app.get("/status")
async def get_status():
    return nlp_api.get_status()

@app.get("/history")
async def get_history(limit: int = 10):
    return nlp_api.get_history(limit)

@app.get("/services")
async def get_services():
    return nlp_api.get_services()
"""

# Example Flask endpoint definitions
"""
from flask import Flask, request, jsonify

app = Flask(__name__)
nlp_api = NLP2CMDWebAPI()

@app.route('/process', methods=['POST'])
def process_command():
    data = request.get_json()
    if not data or 'command' not in data:
        return jsonify({'error': 'Command required'}), 400
    
    command = data['command']
    dsl = data.get('dsl', 'auto')
    
    # Run async function in Flask context
    import asyncio
    result = asyncio.run(nlp_api.process_command(command, dsl))
    
    if result['status'] == 'error':
        return jsonify(result), 400
    return jsonify(result)

@app.route('/status')
def get_status():
    return jsonify(nlp_api.get_status())
"""
