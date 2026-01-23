"""
Iteration 4: Simple LLM Integration (Single Domain).

LLM-based SQL generation - start with one domain before expanding.
"""

from __future__ import annotations

import re
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional, Protocol


class LLMClient(Protocol):
    """Protocol for LLM client implementations."""
    
    async def complete(
        self,
        user: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> str:
        """Generate completion from LLM."""
        ...


class LiteLLMClient:
    def __init__(
        self,
        model: Optional[str] = None,
        api_base: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: Optional[float] = None,
    ):
        self.model = model or os.environ.get("NLP2CMD_LLM_MODEL") or "ollama/qwen2.5-coder:7b"
        self.api_base = api_base or os.environ.get("NLP2CMD_LLM_API_BASE") or "http://localhost:11434"
        self.api_key = api_key or os.environ.get("NLP2CMD_LLM_API_KEY") or ""
        self.timeout = timeout or float(os.environ.get("NLP2CMD_LLM_TIMEOUT") or 30)

    async def complete(
        self,
        user: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> str:
        try:
            import litellm
            from litellm import completion
        except ImportError as e:
            raise ImportError("litellm is required for LiteLLMClient. Install with: pip install litellm") from e

        litellm.api_base = self.api_base
        if self.api_key:
            litellm.api_key = self.api_key
        litellm.timeout = self.timeout

        messages: list[dict[str, str]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": user})

        import asyncio

        def _call() -> str:
            resp = completion(
                model=self.model,
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs,
            )
            return str(resp.choices[0].message["content"])

        return await asyncio.to_thread(_call)


@dataclass
class LLMConfig:
    """Configuration for LLM generators."""
    
    model: str = "gpt-4"
    max_tokens: int = 500
    temperature: float = 0.1
    timeout: float = 30.0
    retry_count: int = 3
    

@dataclass
class LLMGenerationResult:
    """Result of LLM generation."""
    
    command: str
    raw_response: str
    model: str
    tokens_used: int = 0
    latency_ms: float = 0.0
    success: bool = True
    error: Optional[str] = None


class BaseLLMGenerator(ABC):
    """Base class for LLM-based DSL generators."""
    
    DOMAIN: str = "base"
    
    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[LLMConfig] = None,
    ):
        self.llm = llm_client
        self.config = config or LLMConfig()
    
    @abstractmethod
    def get_system_prompt(self) -> str:
        """Get the system prompt for this domain."""
        ...
    
    @abstractmethod
    def extract_command(self, response: str) -> str:
        """Extract command from LLM response."""
        ...
    
    async def generate(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
        previous_errors: Optional[list[str]] = None,
    ) -> LLMGenerationResult:
        """
        Generate DSL command from natural language.
        
        Args:
            text: Natural language input
            context: Additional context (schema, history, etc.)
            previous_errors: Errors from previous attempts (for retry)
            
        Returns:
            LLMGenerationResult with generated command
        """
        import time
        start = time.time()
        
        try:
            # Build prompt
            system = self.get_system_prompt()
            user_prompt = self._build_user_prompt(text, context, previous_errors)
            
            # Call LLM
            response = await self.llm.complete(
                user=user_prompt,
                system=system,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            
            # Extract command
            command = self.extract_command(response)
            
            latency = (time.time() - start) * 1000
            
            return LLMGenerationResult(
                command=command,
                raw_response=response,
                model=self.config.model,
                latency_ms=latency,
                success=True,
            )
            
        except Exception as e:
            latency = (time.time() - start) * 1000
            return LLMGenerationResult(
                command=f"# Error: {e}",
                raw_response="",
                model=self.config.model,
                latency_ms=latency,
                success=False,
                error=str(e),
            )
    
    def _build_user_prompt(
        self,
        text: str,
        context: Optional[dict[str, Any]],
        previous_errors: Optional[list[str]],
    ) -> str:
        """Build the user prompt."""
        parts = [text]
        
        if context:
            if "schema" in context:
                parts.append(f"\nDostępne tabele/schemat: {context['schema']}")
            if "history" in context:
                parts.append(f"\nPoprzednie komendy: {context['history']}")
        
        if previous_errors:
            parts.append(f"\nPoprzednie błędy (popraw): {'; '.join(previous_errors)}")
        
        return "\n".join(parts)


class SimpleLLMSQLGenerator(BaseLLMGenerator):
    """
    LLM-based SQL generation - single domain first.
    
    Example:
        generator = SimpleLLMSQLGenerator(llm_client)
        result = await generator.generate("Pokaż 10 ostatnich zamówień")
        # result.command == "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;"
    """
    
    DOMAIN = "sql"
    
    SYSTEM_PROMPT = """Jesteś generatorem SQL. Użytkownik opisuje co chce, ty generujesz SQL.

Zasady:
1. Odpowiadaj TYLKO poprawnym SQL, bez wyjaśnień
2. Format: jedna kwerenda SQL zakończona średnikiem
3. Używaj standardowego SQL (kompatybilnego z PostgreSQL)
4. Jeśli nie jesteś pewien tabeli, użyj nazwy sugerowanej przez kontekst
5. Dla zapytań o "ostatnie" rekordy, sortuj malejąco po dacie i użyj LIMIT

Dostępne tabele (domyślne):
- users (id, name, email, status, created_at)
- orders (id, user_id, total, status, created_at)
- products (id, name, price, category, stock)
- categories (id, name, parent_id)

Odpowiedz TYLKO kodem SQL."""
    
    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[LLMConfig] = None,
        schema_context: Optional[dict[str, list[str]]] = None,
    ):
        super().__init__(llm_client, config)
        self.schema = schema_context or {}
    
    def get_system_prompt(self) -> str:
        """Get SQL-specific system prompt."""
        prompt = self.SYSTEM_PROMPT
        
        if self.schema:
            schema_str = "\n".join(
                f"- {table} ({', '.join(cols)})"
                for table, cols in self.schema.items()
            )
            prompt = prompt.replace(
                "Dostępne tabele (domyślne):",
                f"Dostępne tabele:\n{schema_str}\n\nTabele domyślne (jeśli brak powyżej):"
            )
        
        return prompt
    
    def extract_command(self, response: str) -> str:
        """Extract SQL from LLM response."""
        response = response.strip()
        
        # Remove markdown code blocks
        if "```sql" in response:
            match = re.search(r'```sql\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        if "```" in response:
            match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        # Return as-is if no code block
        return response


class SimpleLLMShellGenerator(BaseLLMGenerator):
    """LLM-based Shell command generation."""
    
    DOMAIN = "shell"
    
    SYSTEM_PROMPT = """Jesteś generatorem komend Shell/Bash. Użytkownik opisuje co chce, ty generujesz komendę.

Zasady:
1. Odpowiadaj TYLKO komendą shell, bez wyjaśnień
2. Używaj standardowych narzędzi Unix (find, grep, ls, ps, etc.)
3. Unikaj niebezpiecznych operacji (rm -rf /, sudo bez potrzeby)
4. Dla złożonych operacji używaj pipe (|)
5. Cytuj argumenty ze spacjami

Odpowiedz TYLKO komendą shell."""
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    def extract_command(self, response: str) -> str:
        """Extract shell command from response."""
        response = response.strip()
        
        # Remove markdown code blocks
        if "```bash" in response or "```shell" in response:
            match = re.search(r'```(?:bash|shell|sh)?\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        if "```" in response:
            match = re.search(r'```\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return response


class SimpleLLMDockerGenerator(BaseLLMGenerator):
    """LLM-based Docker command generation."""
    
    DOMAIN = "docker"
    
    SYSTEM_PROMPT = """Jesteś generatorem komend Docker. Użytkownik opisuje co chce, ty generujesz komendę.

Zasady:
1. Odpowiadaj TYLKO komendą docker, bez wyjaśnień
2. Używaj docker lub docker-compose
3. Zawsze dodawaj tagi do obrazów (:latest jeśli brak)
4. Dla uruchamiania kontenerów używaj -d (detached)
5. Dodawaj --name dla łatwiejszego zarządzania

Odpowiedz TYLKO komendą docker."""
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    def extract_command(self, response: str) -> str:
        """Extract docker command from response."""
        response = response.strip()
        
        if "```" in response:
            match = re.search(r'```(?:bash|shell|docker)?\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return response


class SimpleLLMKubernetesGenerator(BaseLLMGenerator):
    """LLM-based Kubernetes command generation."""
    
    DOMAIN = "kubernetes"
    
    SYSTEM_PROMPT = """Jesteś generatorem komend kubectl. Użytkownik opisuje co chce, ty generujesz komendę.

Zasady:
1. Odpowiadaj TYLKO komendą kubectl, bez wyjaśnień
2. Używaj pełnych nazw zasobów (pods, deployments, services)
3. Zawsze dodawaj -n namespace jeśli wspomniany
4. Dla get używaj -o wide lub -o yaml gdy potrzeba szczegółów
5. Dla niebezpiecznych operacji dodaj --dry-run=client

Odpowiedz TYLKO komendą kubectl."""
    
    def get_system_prompt(self) -> str:
        return self.SYSTEM_PROMPT
    
    def extract_command(self, response: str) -> str:
        """Extract kubectl command from response."""
        response = response.strip()
        
        if "```" in response:
            match = re.search(r'```(?:bash|shell|yaml)?\s*(.*?)\s*```', response, re.DOTALL)
            if match:
                return match.group(1).strip()
        
        return response


# Mock LLM for testing without actual API calls
class MockLLMClient:
    """Mock LLM client for testing."""
    
    def __init__(self, responses: Optional[dict[str, str]] = None):
        self.responses = responses or {}
        self.call_count = 0
        self.last_prompt: Optional[str] = None
    
    async def complete(
        self,
        user: str,
        system: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.1,
        **kwargs: Any,
    ) -> str:
        """Return mock response."""
        self.call_count += 1
        self.last_prompt = user
        
        # Check for specific responses
        for key, response in self.responses.items():
            if key.lower() in user.lower():
                return response
        
        # Default responses based on keywords
        user_lower = user.lower()
        
        if "użytkownik" in user_lower or "users" in user_lower:
            return "SELECT * FROM users;"
        if "zamówien" in user_lower or "orders" in user_lower:
            return "SELECT * FROM orders ORDER BY created_at DESC LIMIT 10;"
        if "plik" in user_lower or "find" in user_lower:
            return "find . -name '*.py' -type f"
        if "kontener" in user_lower or "docker" in user_lower:
            return "docker ps -a"
        if "pod" in user_lower or "kubectl" in user_lower:
            return "kubectl get pods -A"
        
        return "SELECT 1;"
