"""
Iteration 6: Structured Output (JSON Mode).

Enforced JSON output schema from LLM for reliable parsing.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Optional

from nlp2cmd.generation.llm_simple import LLMClient, LLMConfig


# JSON Schema for structured plan output
PLAN_SCHEMA = {
    "type": "object",
    "properties": {
        "domain": {
            "type": "string",
            "enum": ["sql", "shell", "docker", "kubernetes", "dql"],
            "description": "Target DSL domain"
        },
        "intent": {
            "type": "string",
            "description": "Primary intent (select, insert, find, run, get, etc.)"
        },
        "entities": {
            "type": "object",
            "properties": {
                "table": {"type": "string"},
                "columns": {"type": "array", "items": {"type": "string"}},
                "filters": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "field": {"type": "string"},
                            "operator": {"type": "string"},
                            "value": {}
                        }
                    }
                },
                "limit": {"type": "integer"},
                "path": {"type": "string"},
                "pattern": {"type": "string"},
                "container": {"type": "string"},
                "image": {"type": "string"},
                "namespace": {"type": "string"},
                "resource_type": {"type": "string"},
                "resource_name": {"type": "string"},
            }
        },
        "confidence": {
            "type": "number",
            "minimum": 0,
            "maximum": 1,
            "description": "Confidence in the interpretation"
        }
    },
    "required": ["domain", "intent", "entities"]
}


@dataclass
class StructuredPlan:
    """Structured execution plan from LLM."""
    
    domain: str
    intent: str
    entities: dict[str, Any]
    confidence: float = 0.9
    raw_response: str = ""
    
    def to_adapter_plan(self) -> dict[str, Any]:
        """Convert to adapter-compatible plan format."""
        return {
            "intent": self.intent,
            "entities": self.entities,
            "confidence": self.confidence,
        }


@dataclass
class StructuredPlanResult:
    """Result of structured planning."""
    
    plan: Optional[StructuredPlan]
    success: bool
    error: Optional[str] = None
    parse_attempts: int = 1
    latency_ms: float = 0.0


class StructuredLLMPlanner:
    """
    LLM with enforced JSON output schema.
    
    Uses JSON mode to ensure structured, parseable output
    that can be directly used with DSL adapters.
    
    Example:
        planner = StructuredLLMPlanner(llm_client)
        result = await planner.plan("Pokaż 10 użytkowników gdzie status = active")
        # result.plan.domain == 'sql'
        # result.plan.entities == {'table': 'users', 'limit': 10, 'filters': [...]}
    """
    
    SYSTEM_PROMPT = """Jesteś parserem NL do strukturalnego planu wykonania.
Analizujesz zapytanie użytkownika i zwracasz JSON z planem.

Dostępne domeny:
- sql: zapytania do bazy danych
- shell: operacje systemowe, pliki, procesy
- docker: kontenery, obrazy
- kubernetes: k8s, pody, deploymenty

Format odpowiedzi (TYLKO JSON, bez markdown):
{
  "domain": "sql|shell|docker|kubernetes",
  "intent": "select|insert|update|delete|find|run|get|scale|...",
  "entities": {
    "table": "nazwa_tabeli",
    "columns": ["col1", "col2"],
    "filters": [{"field": "x", "operator": "=", "value": "y"}],
    "limit": 10,
    "path": "/sciezka",
    "container": "nazwa",
    "namespace": "default"
  },
  "confidence": 0.95
}

Wypełnij tylko relevantne pola entities dla danej domeny.
Odpowiedz TYLKO poprawnym JSON."""

    def __init__(
        self,
        llm_client: LLMClient,
        config: Optional[LLMConfig] = None,
        schema: Optional[dict[str, Any]] = None,
    ):
        self.llm = llm_client
        self.config = config or LLMConfig(temperature=0.0)
        self.schema = schema or PLAN_SCHEMA
    
    async def plan(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
    ) -> StructuredPlanResult:
        """
        Generate structured plan from natural language.
        
        Args:
            text: Natural language input
            context: Additional context (schema info, etc.)
            
        Returns:
            StructuredPlanResult with parsed plan
        """
        import time
        start = time.time()
        
        try:
            # Build prompt
            user_prompt = text
            if context:
                if "available_tables" in context:
                    user_prompt += f"\n\nDostępne tabele: {context['available_tables']}"
            
            # Call LLM with JSON mode hint
            response = await self.llm.complete(
                user=user_prompt,
                system=self.SYSTEM_PROMPT,
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
            )
            
            # Parse JSON
            plan = self._parse_response(response)
            
            latency = (time.time() - start) * 1000
            
            return StructuredPlanResult(
                plan=plan,
                success=True,
                latency_ms=latency,
            )
            
        except json.JSONDecodeError as e:
            latency = (time.time() - start) * 1000
            return StructuredPlanResult(
                plan=None,
                success=False,
                error=f"JSON parse error: {e}",
                latency_ms=latency,
            )
        except Exception as e:
            latency = (time.time() - start) * 1000
            return StructuredPlanResult(
                plan=None,
                success=False,
                error=str(e),
                latency_ms=latency,
            )
    
    def _parse_response(self, response: str) -> StructuredPlan:
        """Parse LLM response into StructuredPlan."""
        response = response.strip()
        
        # Remove markdown code blocks if present
        if response.startswith("```"):
            lines = response.split("\n")
            lines = [l for l in lines if not l.startswith("```")]
            response = "\n".join(lines)
        
        # Parse JSON
        data = json.loads(response)
        
        # Validate required fields
        if "domain" not in data:
            raise ValueError("Missing 'domain' in response")
        if "intent" not in data:
            raise ValueError("Missing 'intent' in response")
        
        return StructuredPlan(
            domain=data.get("domain", "unknown"),
            intent=data.get("intent", "unknown"),
            entities=data.get("entities", {}),
            confidence=data.get("confidence", 0.9),
            raw_response=response,
        )
    
    async def plan_with_retry(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
        max_retries: int = 3,
    ) -> StructuredPlanResult:
        """Plan with automatic retry on parse failure."""
        last_error = None
        
        for attempt in range(max_retries):
            result = await self.plan(text, context)
            
            if result.success:
                result.parse_attempts = attempt + 1
                return result
            
            last_error = result.error
        
        return StructuredPlanResult(
            plan=None,
            success=False,
            error=f"Failed after {max_retries} attempts: {last_error}",
            parse_attempts=max_retries,
        )


@dataclass
class MultiStepPlan:
    """Multi-step execution plan."""
    
    steps: list[StructuredPlan]
    dependencies: dict[int, list[int]] = field(default_factory=dict)
    
    def get_execution_order(self) -> list[int]:
        """Get topologically sorted execution order."""
        visited = set()
        order = []
        
        def visit(step_idx: int):
            if step_idx in visited:
                return
            visited.add(step_idx)
            for dep in self.dependencies.get(step_idx, []):
                visit(dep)
            order.append(step_idx)
        
        for i in range(len(self.steps)):
            visit(i)
        
        return order


class MultiStepPlanner(StructuredLLMPlanner):
    """
    Iteration 8: Multi-Step Plans.
    
    Decompose complex queries into multiple executable steps.
    """
    
    DECOMPOSITION_PROMPT = """Rozłóż zapytanie na sekwencję prostych kroków.
Każdy krok to jedna operacja w jednej domenie.

Format odpowiedzi (TYLKO JSON):
{
  "steps": [
    {
      "domain": "shell",
      "intent": "find",
      "entities": {"path": "/var/log", "pattern": "*.log"},
      "confidence": 0.9
    },
    {
      "domain": "shell", 
      "intent": "count",
      "entities": {"depends_on": 0},
      "confidence": 0.85
    }
  ]
}

Użyj "depends_on" aby wskazać zależności między krokami (indeks poprzedniego kroku).
Odpowiedz TYLKO poprawnym JSON."""

    async def decompose(
        self,
        text: str,
        context: Optional[dict[str, Any]] = None,
    ) -> tuple[MultiStepPlan, bool, Optional[str]]:
        """
        Decompose complex query into steps.
        
        Returns:
            Tuple of (MultiStepPlan, success, error)
        """
        try:
            response = await self.llm.complete(
                user=text,
                system=self.DECOMPOSITION_PROMPT,
                max_tokens=1000,
                temperature=0.0,
            )
            
            # Parse response
            response = response.strip()
            if response.startswith("```"):
                lines = response.split("\n")
                lines = [l for l in lines if not l.startswith("```")]
                response = "\n".join(lines)
            
            data = json.loads(response)
            steps_data = data.get("steps", [])
            
            steps = []
            dependencies: dict[int, list[int]] = {}
            
            for i, step_data in enumerate(steps_data):
                step = StructuredPlan(
                    domain=step_data.get("domain", "unknown"),
                    intent=step_data.get("intent", "unknown"),
                    entities=step_data.get("entities", {}),
                    confidence=step_data.get("confidence", 0.9),
                )
                steps.append(step)
                
                # Extract dependencies
                if "depends_on" in step_data.get("entities", {}):
                    dep = step_data["entities"]["depends_on"]
                    if isinstance(dep, int):
                        dependencies[i] = [dep]
                    elif isinstance(dep, list):
                        dependencies[i] = dep
            
            return MultiStepPlan(steps=steps, dependencies=dependencies), True, None
            
        except Exception as e:
            return MultiStepPlan(steps=[]), False, str(e)
