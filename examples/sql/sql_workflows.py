#!/usr/bin/env python3
"""
Example: SQL Query Generation and Validation

Demonstrates SQL adapter capabilities:
- Query generation from structured plans
- Safety policy enforcement
- Query validation
- Multiple dialects support
"""

from nlp2cmd import SQLAdapter
from nlp2cmd.adapters import SQLSafetyPolicy
from nlp2cmd.validators import SQLValidator


def print_section(title: str):
    """Print section header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def main():
    print_section("SQL Query Generation Demo")
    
    # =========================================================================
    # Basic Query Generation
    # =========================================================================
    print_section("1. Basic Query Generation")
    
    adapter = SQLAdapter(dialect="postgresql")
    
    # SELECT query
    plan = {
        "intent": "select",
        "entities": {
            "table": "users",
            "columns": ["id", "name", "email"],
            "filters": [
                {"field": "status", "operator": "=", "value": "active"}
            ]
        }
    }
    
    query = adapter.generate(plan)
    print("Plan:")
    print(f"  Intent: {plan['intent']}")
    print(f"  Table: {plan['entities']['table']}")
    print(f"  Columns: {plan['entities']['columns']}")
    print(f"\nGenerated SQL:\n  {query}")
    
    # =========================================================================
    # Complex Queries
    # =========================================================================
    print_section("2. Complex Queries")
    
    # JOIN query
    join_plan = {
        "intent": "select",
        "entities": {
            "table": "orders",
            "columns": ["o.id", "o.total", "u.name", "u.email"],
            "joins": [
                {
                    "type": "LEFT",
                    "table": "users",
                    "alias": "u",
                    "on": "o.user_id = u.id"
                }
            ],
            "alias": "o",
            "filters": [
                {"field": "o.status", "operator": "=", "value": "completed"}
            ],
            "order_by": [{"field": "o.created_at", "direction": "DESC"}],
            "limit": 10
        }
    }
    
    query = adapter.generate(join_plan)
    print("JOIN Query:")
    print(f"\n{query}")
    
    # Aggregation query
    agg_plan = {
        "intent": "aggregate",
        "entities": {
            "table": "orders",
            "aggregations": [
                {"function": "COUNT", "field": "*", "alias": "order_count"},
                {"function": "SUM", "field": "total", "alias": "total_revenue"},
                {"function": "AVG", "field": "total", "alias": "avg_order_value"}
            ],
            "group_by": ["user_id"],
            "having": [
                {"function": "COUNT", "field": "*", "operator": ">", "value": 5}
            ]
        }
    }
    
    query = adapter.generate(agg_plan)
    print("\nAggregation Query:")
    print(f"\n{query}")
    
    # =========================================================================
    # Safety Policy
    # =========================================================================
    print_section("3. Safety Policy Enforcement")
    
    # Create adapter with strict safety policy
    strict_policy = SQLSafetyPolicy(
        allow_delete=False,
        allow_drop=False,
        allow_truncate=False,
        require_where_clause=True,
        max_rows_affected=1000,
    )
    
    safe_adapter = SQLAdapter(
        dialect="postgresql",
        safety_policy=strict_policy
    )
    
    print("Safety Policy:")
    print(f"  Allow DELETE: {strict_policy.allow_delete}")
    print(f"  Allow DROP: {strict_policy.allow_drop}")
    print(f"  Require WHERE: {strict_policy.require_where_clause}")
    print(f"  Max rows: {strict_policy.max_rows_affected}")
    
    # Test DELETE without WHERE
    delete_plan = {
        "intent": "delete",
        "entities": {
            "table": "logs",
        }
    }
    
    print("\nAttempting DELETE without WHERE:")
    try:
        result = safe_adapter.generate(delete_plan)
        is_safe, reason = safe_adapter.check_safety(result)
        print(f"  Query: {result}")
        print(f"  Safe: {is_safe}")
        if reason:
            print(f"  Reason: {reason}")
    except Exception as e:
        print(f"  Blocked: {e}")
    
    # Test DELETE with WHERE
    delete_plan_safe = {
        "intent": "delete",
        "entities": {
            "table": "logs",
            "filters": [
                {"field": "created_at", "operator": "<", "value": "2024-01-01"}
            ]
        }
    }
    
    print("\nAttempting DELETE with WHERE:")
    result = safe_adapter.generate(delete_plan_safe)
    is_safe, reason = safe_adapter.check_safety(result)
    print(f"  Query: {result}")
    print(f"  Safe: {is_safe}")
    
    # =========================================================================
    # Query Validation
    # =========================================================================
    print_section("4. Query Validation")
    
    validator = SQLValidator(strict=False)
    
    # Valid query
    valid_query = "SELECT * FROM users WHERE id = 1"
    print(f"Query: {valid_query}")
    result = validator.validate(valid_query)
    print(f"Valid: {result.is_valid}")
    
    # Dangerous query
    dangerous_query = "DELETE FROM users"
    print(f"\nQuery: {dangerous_query}")
    result = validator.validate(dangerous_query)
    print(f"Valid: {result.is_valid}")
    if result.warnings:
        print("Warnings:")
        for w in result.warnings:
            print(f"  ⚠️  {w}")
    if result.suggestions:
        print("Suggestions:")
        for s in result.suggestions:
            print(f"  💡 {s}")
    
    # Query with syntax issues
    bad_syntax = "SELECT * FROM users WHERE (id = 1"
    print(f"\nQuery: {bad_syntax}")
    result = validator.validate(bad_syntax)
    print(f"Valid: {result.is_valid}")
    if result.errors:
        print("Errors:")
        for e in result.errors:
            print(f"  ❌ {e}")
    
    # =========================================================================
    # Multiple Dialects
    # =========================================================================
    print_section("5. SQL Dialects")
    
    dialects = ["postgresql", "mysql", "sqlite"]
    
    plan = {
        "intent": "select",
        "entities": {
            "table": "users",
            "columns": ["id", "name"],
            "limit": 10
        }
    }
    
    for dialect in dialects:
        adapter = SQLAdapter(dialect=dialect)
        query = adapter.generate(plan)
        print(f"{dialect.upper()}:")
        print(f"  {query}\n")
    
    # =========================================================================
    # INSERT and UPDATE
    # =========================================================================
    print_section("6. Data Modification Queries")
    
    adapter = SQLAdapter(dialect="postgresql")
    
    # INSERT
    insert_plan = {
        "intent": "insert",
        "entities": {
            "table": "users",
            "values": {
                "name": "John Doe",
                "email": "john@example.com",
                "status": "active"
            }
        }
    }
    
    query = adapter.generate(insert_plan)
    print("INSERT:")
    print(f"  {query}")
    
    # UPDATE
    update_plan = {
        "intent": "update",
        "entities": {
            "table": "users",
            "values": {
                "status": "inactive",
                "updated_at": "NOW()"
            },
            "filters": [
                {"field": "last_login", "operator": "<", "value": "2024-01-01"}
            ]
        }
    }
    
    query = adapter.generate(update_plan)
    print("\nUPDATE:")
    print(f"  {query}")
    
    # =========================================================================
    # Schema Context
    # =========================================================================
    print_section("7. Schema-Aware Generation")
    
    schema_context = {
        "tables": ["users", "orders", "products"],
        "columns": {
            "users": ["id", "name", "email", "created_at"],
            "orders": ["id", "user_id", "product_id", "quantity", "total"],
            "products": ["id", "name", "price", "stock"],
        },
        "relations": {
            "orders.user_id": "users.id",
            "orders.product_id": "products.id",
        }
    }
    
    adapter = SQLAdapter(
        dialect="postgresql",
        schema_context=schema_context
    )
    
    print("Schema Context:")
    print(f"  Tables: {schema_context['tables']}")
    print(f"  Relations: {list(schema_context['relations'].keys())}")
    
    # Generate query with context
    plan = {
        "intent": "select",
        "entities": {
            "table": "orders",
            "columns": ["*"],
        }
    }
    
    query = adapter.generate(plan)
    print(f"\nGenerated query uses schema context for validation")


if __name__ == "__main__":
    main()
