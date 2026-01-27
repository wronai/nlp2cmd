#!/usr/bin/env python3
"""
NLP2CMD LLM Integration Example

Demonstrates integration with LLM backends:
- Claude (Anthropic)
- GPT (OpenAI)
- Custom backends

Note: Requires API keys to run.
"""

import os
from typing import Optional

from nlp2cmd import NLP2CMD, SQLAdapter
from nlp2cmd.core import NLPBackend, ExecutionPlan, Entity, LLMBackend, RuleBasedBackend


class MockLLMBackend(NLPBackend):
    """
    Mock LLM backend for demonstration.
    In production, replace with actual LLM calls.
    """

    # Simulated LLM responses
    RESPONSES = {
        "show all users": {
            "intent": "select",
            "entities": {
                "table": "users",
                "columns": "*"
            },
            "confidence": 0.95
        },
        "find users from warsaw": {
            "intent": "select",
            "entities": {
                "table": "users",
                "columns": "*",
                "filters": [
                    {"field": "city", "operator": "=", "value": "Warsaw"}
                ]
            },
            "confidence": 0.92
        },
        "count orders by status": {
            "intent": "aggregate",
            "entities": {
                "base_table": "orders",
                "aggregations": [
                    {"function": "COUNT", "field": "*", "alias": "count"}
                ],
                "grouping": ["status"]
            },
            "confidence": 0.90
        },
        "show top 10 customers by total spending": {
            "intent": "aggregate",
            "entities": {
                "base_table": "users",
                "aggregations": [
                    {"function": "SUM", "field": "orders.total", "alias": "total_spent"}
                ],
                "joins": [
                    {"type": "LEFT", "table": "orders", "on": "users.id = orders.user_id"}
                ],
                "grouping": ["users.id", "users.name"],
                "ordering": [{"field": "total_spent", "direction": "DESC"}],
                "limit": 10
            },
            "confidence": 0.88
        },
        "update user email where id is 123": {
            "intent": "update",
            "entities": {
                "table": "users",
                "values": {
                    "email": "new@example.com"
                },
                "filters": [
                    {"field": "id", "operator": "=", "value": 123}
                ]
            },
            "confidence": 0.85
        },
    }

    def generate_plan(self, text: str, context: Optional[dict] = None) -> ExecutionPlan:
        """Generate execution plan from text using mock LLM."""
        text_lower = text.lower().strip()

        # Find best matching response
        best_match = None
        best_score = 0

        for key, response in self.RESPONSES.items():
            # Simple keyword matching (real LLM would do better)
            score = sum(1 for word in key.split() if word in text_lower)
            if score > best_score:
                best_score = score
                best_match = response

        if best_match:
            return ExecutionPlan(
                intent=best_match["intent"],
                entities=best_match["entities"],
                confidence=best_match["confidence"]
            )

        # Default fallback
        return ExecutionPlan(
            intent="unknown",
            entities={},
            confidence=0.3
        )


def demonstrate_mock_llm():
    """Demonstrate with mock LLM backend."""
    print("=" * 70)
    print("Mock LLM Backend Demonstration")
    print("=" * 70)

    adapter = SQLAdapter(
        dialect="postgresql",
        schema_context={
            "tables": ["users", "orders", "products"],
            "columns": {
                "users": ["id", "name", "email", "city"],
                "orders": ["id", "user_id", "total", "status"],
            }
        }
    )

    backend = MockLLMBackend()
    nlp = NLP2CMD(adapter=adapter, nlp_backend=backend)

    # Test queries
    queries = [
        "Show all users",
        "Find users from Warsaw",
        "Count orders by status",
        "Show top 10 customers by total spending",
        "Update user email where id is 123",
    ]

    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 50)

        # Generate plan using mock LLM
        plan = backend.generate_plan(query)
        print(f"Intent: {plan.intent}")
        print(f"Confidence: {plan.confidence:.0%}")

        # Generate SQL
        command = adapter.generate(plan.model_dump())
        print(f"\nGenerated SQL:")
        print(f"   {command}")


def demonstrate_rule_based_fallback():
    """Demonstrate with rule-based fallback."""
    print("\n" + "=" * 70)
    print("Rule-Based Fallback Demonstration")
    print("=" * 70)

    # Rule-based backend for simple patterns
    rules = {
        "select": ["show", "display", "get", "find", "list", "query"],
        "insert": ["add", "create", "insert", "new"],
        "update": ["update", "change", "modify", "set"],
        "delete": ["delete", "remove", "drop"],
        "aggregate": ["count", "sum", "average", "total", "max", "min"],
    }

    backend = RuleBasedBackend(rules=rules)

    queries = [
        "show users",
        "count orders",
        "add new product",
        "update customer info",
        "remove old records",
    ]

    for query in queries:
        print(f"\n📝 Query: {query}")
        intent, confidence = backend.extract_intent(query)
        print(f"   Detected intent: {intent} (confidence: {confidence:.0%})")


def demonstrate_real_llm_setup():
    """Show how to set up real LLM backends."""
    print("\n" + "=" * 70)
    print("Real LLM Backend Setup")
    print("=" * 70)

    print("""
To use real LLM backends, you need API keys:

1. ANTHROPIC (Claude):
   ```python
   import os
   from nlp2cmd.core import LLMBackend

   backend = LLMBackend(
       model="claude-sonnet-4-20250514",
       api_key=os.environ["ANTHROPIC_API_KEY"]
   )
   ```

2. OPENAI (GPT):
   ```python
   backend = LLMBackend(
       model="gpt-4",
       api_key=os.environ["OPENAI_API_KEY"]
   )
   ```

3. CUSTOM SYSTEM PROMPT:
   ```python
   custom_prompt = '''
   You are a SQL query generator. Given natural language input,
   respond with a JSON object containing:
   - intent: the query type (select, insert, update, delete, aggregate)
   - entities: extracted parameters (table, columns, filters, etc.)
   - confidence: your confidence score (0.0-1.0)
   
   Respond ONLY with valid JSON.
   '''

   backend = LLMBackend(
       model="claude-sonnet-4-20250514",
       api_key=api_key,
       system_prompt=custom_prompt
   )
   ```
""")

    # Check if API keys are available
    has_anthropic = "ANTHROPIC_API_KEY" in os.environ
    has_openai = "OPENAI_API_KEY" in os.environ

    print("\n🔑 API Key Status:")
    print(f"   ANTHROPIC_API_KEY: {'✅ Available' if has_anthropic else '❌ Not set'}")
    print(f"   OPENAI_API_KEY: {'✅ Available' if has_openai else '❌ Not set'}")

    if has_anthropic:
        print("\n" + "─" * 50)
        print("Testing Claude backend...")
        try:
            backend = LLMBackend(
                model="claude-sonnet-4-20250514",
                api_key=os.environ["ANTHROPIC_API_KEY"]
            )

            adapter = SQLAdapter(dialect="postgresql")
            nlp = NLP2CMD(adapter=adapter, nlp_backend=backend)

            # Test query
            plan = backend.generate_plan("Show all active users")
            print(f"✅ Claude response: intent={plan.intent}, confidence={plan.confidence:.0%}")

        except Exception as e:
            print(f"❌ Error: {e}")


def demonstrate_hybrid_approach():
    """Demonstrate hybrid LLM + rule-based approach."""
    print("\n" + "=" * 70)
    print("Hybrid Approach: LLM + Rule-Based")
    print("=" * 70)

    print("""
For production systems, consider a hybrid approach:

1. Use rule-based for simple, well-defined queries:
   - "show users" → SELECT * FROM users
   - "count orders" → SELECT COUNT(*) FROM orders

2. Use LLM for complex, ambiguous queries:
   - "find customers who haven't ordered in 3 months"
   - "show products with above-average ratings"

Benefits:
- Lower latency for simple queries
- Lower API costs
- Better handling of edge cases

Example implementation:
   ```python
   class HybridBackend(NLPBackend):
       def __init__(self, rule_backend, llm_backend, llm_threshold=0.7):
           self.rule_backend = rule_backend
           self.llm_backend = llm_backend
           self.llm_threshold = llm_threshold
       
       def generate_plan(self, text, context=None):
           # Try rule-based first
           intent, confidence = self.rule_backend.extract_intent(text)
           
           if confidence >= self.llm_threshold:
               # Use rule-based result
               return self._plan_from_rules(text, intent)
           else:
               # Fall back to LLM
               return self.llm_backend.generate_plan(text, context)
   ```
""")


def main():
    """Run all demonstrations."""
    demonstrate_mock_llm()
    demonstrate_rule_based_fallback()
    demonstrate_real_llm_setup()
    demonstrate_hybrid_approach()

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print("""
NLP2CMD supports multiple NLP backends:

1. 📝 Rule-Based (default):
   - Pattern matching for simple queries
   - No external dependencies
   - Fast and predictable

2. 🤖 LLM Backends:
   - Claude (Anthropic) - Recommended for complex queries
   - GPT (OpenAI) - Alternative LLM option
   - Custom - Implement your own

3. 🔀 Hybrid:
   - Combine rule-based and LLM
   - Best of both worlds

Choose based on your needs:
- Simple queries → Rule-based
- Complex queries → LLM
- Production → Hybrid approach
""")


if __name__ == "__main__":
    main()
