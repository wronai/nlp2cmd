#!/usr/bin/env python3
"""
NLP2CMD SQL Example

Demonstrates natural language to SQL transformation
with schema context and safety policies.

📚 Related Documentation:
- https://github.com/wronai/nlp2cmd/blob/main/docs/guides/user-guide.md
- https://github.com/wronai/nlp2cmd/blob/main/docs/api/README.md
- https://github.com/wronai/nlp2cmd/blob/main/THERMODYNAMIC_INTEGRATION.md

🚀 More Examples:
- https://github.com/wronai/nlp2cmd/tree/main/examples/use_cases
"""

from nlp2cmd import NLP2CMD, SQLAdapter, SQLSafetyPolicy


def main():
    # Configure schema context
    schema_context = {
        "tables": ["users", "orders", "products", "categories"],
        "columns": {
            "users": ["id", "name", "email", "city", "created_at", "active"],
            "orders": ["id", "user_id", "product_id", "quantity", "total", "created_at"],
            "products": ["id", "name", "price", "category_id", "stock"],
            "categories": ["id", "name", "description"],
        },
        "relations": {
            "orders.user_id": "users.id",
            "orders.product_id": "products.id",
            "products.category_id": "categories.id",
        },
        "primary_keys": {
            "users": "id",
            "orders": "id",
            "products": "id",
            "categories": "id",
        },
    }

    # Configure safety policy
    safety_policy = SQLSafetyPolicy(
        allow_delete=False,
        allow_truncate=False,
        allow_drop=False,
        require_where_on_update=True,
        require_where_on_delete=True,
        max_rows_affected=1000,
        blocked_tables=["audit_log", "system_config"],
    )

    # Create adapter and NLP2CMD instance
    adapter = SQLAdapter(
        dialect="postgresql",
        schema_context=schema_context,
        safety_policy=safety_policy,
    )

    nlp = NLP2CMD(adapter=adapter)

    # Example queries
    queries = [
        "Show all users from Warsaw",
        "Count orders per user this year",
        "Find products with low stock",
        "Show top 10 customers by order total",
        "List categories with more than 5 products",
    ]

    print("=" * 60)
    print("NLP2CMD SQL Examples")
    print("=" * 60)

    for query in queries:
        print(f"\n📝 Query: {query}")
        print("-" * 40)

        result = nlp.transform(query)

        print(f"Status: {result.status.value}")
        print(f"Confidence: {result.confidence:.0%}")
        print(f"\nGenerated SQL:")
        print(result.command)

        if result.warnings:
            print(f"\n⚠️ Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")

        if result.suggestions:
            print(f"\n💡 Suggestions:")
            for suggestion in result.suggestions:
                print(f"   - {suggestion}")

    # Example: Blocked operation
    print("\n" + "=" * 60)
    print("Safety Policy Demo: Blocked Operation")
    print("=" * 60)

    result = nlp.transform("Delete all inactive users")
    print(f"\n📝 Query: Delete all inactive users")
    print(f"Status: {result.status.value}")

    if result.errors:
        print(f"\n❌ Blocked:")
        for error in result.errors:
            print(f"   - {error}")

    if result.suggestions:
        print(f"\n💡 Alternative:")
        for suggestion in result.suggestions:
            print(f"   - {suggestion}")


if __name__ == "__main__":
    main()
