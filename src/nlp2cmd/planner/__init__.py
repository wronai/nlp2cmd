"""
LLM Planner for NLP2CMD.

Generates multi-step execution plans using LLM,
constrained to allowed actions from the registry.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

from nlp2cmd.registry import ActionRegistry, get_registry
from nlp2cmd.executor import ExecutionPlan, PlanStep, PlanValidator

logger = logging.getLogger(__name__)


@dataclass
class PlannerConfig:
    """Configuration for LLM Planner."""
    
    max_steps: int = 10
    require_confirmation_for_destructive: bool = True
    include_examples: bool = True
    temperature: float = 0.2  # Low temperature for more deterministic output
    max_tokens: int = 2000


@dataclass
class PlanningResult:
    """Result of plan generation."""
    
    success: bool
    plan: Optional[ExecutionPlan] = None
    error: Optional[str] = None
    raw_response: Optional[str] = None
    validation_errors: list[str] = field(default_factory=list)
    confidence: float = 0.0


class LLMPlanner:
    """
    Generates execution plans using LLM.
    
    The LLM is constrained to only use actions from the registry.
    It receives:
    - User intent and entities
    - Available actions with schemas
    - System context
    
    It outputs:
    - JSON plan with steps
    - Each step references a valid action
    """
    
    SYSTEM_PROMPT = """You are a task planner for a command execution system.

Your job is to create execution plans that accomplish user goals.

IMPORTANT RULES:
1. You can ONLY use actions from the provided action catalog
2. Output ONLY valid JSON - no explanations, no markdown
3. Each step must have an "action" field matching an available action
4. Use "foreach" to iterate over results from previous steps
5. Use "$variable_name" to reference results from previous steps
6. Use "$item" and "$index" inside foreach loops
7. Keep plans simple - prefer fewer steps

OUTPUT FORMAT:
{
  "steps": [
    {
      "action": "action_name",
      "params": { "param1": "value1" },
      "store_as": "result_variable"
    },
    {
      "action": "another_action",
      "foreach": "result_variable",
      "params": { "item": "$item" }
    }
  ]
}

AVAILABLE ACTIONS:
{{ACTION_CATALOG}}

USER CONTEXT:
{{USER_CONTEXT}}
"""

    EXAMPLES = [
        {
            "user_request": "Count ERROR occurrences in all log files",
            "plan": {
                "steps": [
                    {
                        "action": "shell_find",
                        "params": {"glob": "*.log"},
                        "store_as": "log_files"
                    },
                    {
                        "action": "shell_count_pattern",
                        "foreach": "log_files",
                        "params": {
                            "file": "$item",
                            "pattern": "ERROR"
                        },
                        "store_as": "counts"
                    },
                    {
                        "action": "summarize_results",
                        "params": {"data": "$counts"}
                    }
                ]
            }
        },
        {
            "user_request": "Show top 5 users by order count",
            "plan": {
                "steps": [
                    {
                        "action": "sql_aggregate",
                        "params": {
                            "table": "orders",
                            "aggregations": [
                                {"function": "COUNT", "field": "*", "alias": "order_count"}
                            ],
                            "grouping": ["user_id"]
                        },
                        "store_as": "user_orders"
                    },
                    {
                        "action": "sort_results",
                        "params": {
                            "data": "$user_orders",
                            "key": "order_count",
                            "reverse": True
                        },
                        "store_as": "sorted"
                    },
                    {
                        "action": "filter_results",
                        "params": {
                            "data": "$sorted",
                            "condition": "[:5]"
                        }
                    }
                ]
            }
        },
        {
            "user_request": "Scale nginx deployment to 5 replicas and show status",
            "plan": {
                "steps": [
                    {
                        "action": "k8s_scale",
                        "params": {
                            "deployment": "nginx",
                            "replicas": 5
                        }
                    },
                    {
                        "action": "k8s_get",
                        "params": {
                            "resource": "deployment",
                            "name": "nginx",
                            "output": "wide"
                        }
                    }
                ]
            }
        }
    ]
    
    def __init__(
        self,
        llm_client: Any = None,
        registry: Optional[ActionRegistry] = None,
        config: Optional[PlannerConfig] = None,
    ):
        """
        Initialize LLM Planner.
        
        Args:
            llm_client: LLM client (Anthropic, OpenAI, etc.)
            registry: Action registry
            config: Planner configuration
        """
        self.llm_client = llm_client
        self.registry = registry or get_registry()
        self.config = config or PlannerConfig()
        self.validator = PlanValidator(self.registry)
    
    def plan(
        self,
        intent: str,
        entities: dict[str, Any],
        text: str,
        context: Optional[dict[str, Any]] = None,
        domain: Optional[str] = None,
    ) -> PlanningResult:
        """
        Generate an execution plan.
        
        Args:
            intent: Detected intent
            entities: Extracted entities
            text: Original user text
            context: Additional context
            domain: Optional domain filter for actions
            
        Returns:
            PlanningResult with generated plan
        """
        context = context or {}
        
        # Build prompt
        prompt = self._build_prompt(intent, entities, text, context, domain)
        
        # Call LLM
        try:
            if self.llm_client:
                response = self._call_llm(prompt)
            else:
                # Fallback to rule-based planning
                response = self._rule_based_plan(intent, entities, domain)
            
            # Parse response
            plan_dict = self._parse_response(response)
            
            if plan_dict is None:
                return PlanningResult(
                    success=False,
                    error="Failed to parse LLM response as JSON",
                    raw_response=response,
                )
            
            # Create plan
            plan = ExecutionPlan.from_dict(plan_dict)
            
            # Validate plan
            is_valid, errors = self.validator.validate(plan)
            
            if not is_valid:
                return PlanningResult(
                    success=False,
                    plan=plan,
                    error="Plan validation failed",
                    validation_errors=errors,
                    raw_response=response,
                )
            
            return PlanningResult(
                success=True,
                plan=plan,
                raw_response=response,
                confidence=0.9,
            )
            
        except Exception as e:
            logger.exception("Plan generation failed")
            return PlanningResult(
                success=False,
                error=str(e),
            )
    
    def _build_prompt(
        self,
        intent: str,
        entities: dict[str, Any],
        text: str,
        context: dict[str, Any],
        domain: Optional[str],
    ) -> str:
        """Build the LLM prompt."""
        # Get action catalog
        action_catalog = self.registry.to_llm_prompt(domain)
        
        # Build user context
        user_context = f"""
Intent: {intent}
Entities: {json.dumps(entities, indent=2)}
Original request: {text}
"""
        
        if context:
            user_context += f"\nAdditional context: {json.dumps(context, indent=2)}"
        
        # Build system prompt
        system_prompt = self.SYSTEM_PROMPT.replace(
            "{{ACTION_CATALOG}}", action_catalog
        ).replace(
            "{{USER_CONTEXT}}", user_context
        )
        
        # Add examples if configured
        if self.config.include_examples:
            examples_text = "\n\nEXAMPLES:\n"
            for ex in self.EXAMPLES[:3]:
                examples_text += f"\nRequest: {ex['user_request']}\n"
                examples_text += f"Plan: {json.dumps(ex['plan'], indent=2)}\n"
            system_prompt += examples_text
        
        # Final instruction
        system_prompt += f"\n\nNow create a plan for: {text}"
        
        return system_prompt
    
    def _call_llm(self, prompt: str) -> str:
        """Call the LLM API."""
        if hasattr(self.llm_client, "messages"):
            # Anthropic client
            response = self.llm_client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        
        elif hasattr(self.llm_client, "chat"):
            # OpenAI client
            response = self.llm_client.chat.completions.create(
                model="gpt-4",
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return response.choices[0].message.content
        
        else:
            raise ValueError("Unknown LLM client type")
    
    def _parse_response(self, response: str) -> Optional[dict[str, Any]]:
        """Parse LLM response as JSON."""
        # Try direct parse
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
        
        # Try to extract JSON from response
        import re
        
        # Look for JSON block
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", response)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Look for { ... } pattern
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            try:
                return json.loads(json_match.group(0))
            except json.JSONDecodeError:
                pass
        
        return None
    
    def _rule_based_plan(
        self,
        intent: str,
        entities: dict[str, Any],
        domain: Optional[str],
    ) -> str:
        """Generate plan using rule-based logic (fallback)."""
        steps = []
        
        # Map intent to action
        intent_action_map = {
            "select": "sql_select",
            "insert": "sql_insert",
            "update": "sql_update",
            "delete": "sql_delete",
            "aggregate": "sql_aggregate",
            "file_search": "shell_find",
            "count_occurrences": "shell_count_pattern",
            "container_run": "docker_run",
            "container_stop": "docker_stop",
            "get": "k8s_get",
            "scale": "k8s_scale",
            "logs": "k8s_logs",
        }
        
        action = intent_action_map.get(intent)
        
        if action:
            steps.append({
                "action": action,
                "params": entities,
                "store_as": f"{intent}_result"
            })
        
        # Add summarize step for complex queries
        if intent in ("aggregate", "file_search"):
            steps.append({
                "action": "summarize_results",
                "params": {"data": f"${intent}_result"}
            })
        
        return json.dumps({"steps": steps})
    
    def get_action_catalog(self, domain: Optional[str] = None) -> str:
        """Get the action catalog for reference."""
        return self.registry.to_llm_prompt(domain)


__all__ = [
    "LLMPlanner",
    "PlannerConfig",
    "PlanningResult",
]
