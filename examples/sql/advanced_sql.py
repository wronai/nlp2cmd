#!/usr/bin/env python3
"""
NLP2CMD Advanced SQL Example

Demonstrates complex SQL transformations including:
- Multi-table joins
- Aggregations with grouping
- Subqueries
- Complex filtering
- Schema-aware generation
"""

from nlp2cmd import NLP2CMD, SQLAdapter, SQLSafetyPolicy


def main():
    # Define comprehensive schema context
    schema_context = {
        "tables": [
            "users", "orders", "products", "categories",
            "order_items", "reviews", "addresses", "payments"
        ],
        "columns": {
            "users": [
                "id", "email", "name", "created_at", "status",
                "subscription_tier", "last_login", "country"
            ],
            "orders": [
                "id", "user_id", "status", "total", "created_at",
                "shipped_at", "delivered_at", "shipping_address_id"
            ],
            "products": [
                "id", "name", "price", "category_id", "stock",
                "created_at", "is_active", "sku"
            ],
            "categories": [
                "id", "name", "parent_id", "description"
            ],
            "order_items": [
                "id", "order_id", "product_id", "quantity", "unit_price"
            ],
            "reviews": [
                "id", "product_id", "user_id", "rating", "comment", "created_at"
            ],
            "addresses": [
                "id", "user_id", "street", "city", "country", "postal_code"
            ],
            "payments": [
                "id", "order_id", "amount", "status", "method", "created_at"
            ],
        },
        "relations": {
            "orders.user_id": "users.id",
            "orders.shipping_address_id": "addresses.id",
            "products.category_id": "categories.id",
            "order_items.order_id": "orders.id",
            "order_items.product_id": "products.id",
            "reviews.product_id": "products.id",
            "reviews.user_id": "users.id",
            "addresses.user_id": "users.id",
            "payments.order_id": "orders.id",
        },
        "primary_keys": {
            "users": "id",
            "orders": "id",
            "products": "id",
            "categories": "id",
            "order_items": "id",
            "reviews": "id",
            "addresses": "id",
            "payments": "id",
        },
        "indexes": {
            "users": ["email", "created_at"],
            "orders": ["user_id", "created_at", "status"],
            "products": ["category_id", "sku"],
        },
    }

    # Create adapter with permissive safety for demo
    adapter = SQLAdapter(
        dialect="postgresql",
        schema_context=schema_context,
        safety_policy=SQLSafetyPolicy(
            allow_delete=False,
            require_where_on_update=True,
        ),
    )

    nlp = NLP2CMD(adapter=adapter)

    print("=" * 70)
    print("NLP2CMD Advanced SQL Examples")
    print("=" * 70)

    # Example 1: Basic SELECT with JOIN
    print("\n" + "─" * 70)
    print("1. JOIN Query: Orders with User Information")
    print("─" * 70)

    plan1 = {
        "intent": "select",
        "entities": {
            "table": "orders",
            "columns": ["orders.id", "orders.total", "users.name", "users.email"],
            "joins": [
                {
                    "type": "INNER",
                    "table": "users",
                    "on": "orders.user_id = users.id"
                }
            ],
            "filters": [
                {"field": "orders.status", "operator": "=", "value": "completed"}
            ],
            "ordering": [{"field": "orders.total", "direction": "DESC"}],
            "limit": 10
        }
    }

    print("Plan:", plan1["entities"])
    print("\nGenerated SQL:")
    print(adapter.generate(plan1))

    # Example 2: Aggregation with GROUP BY
    print("\n" + "─" * 70)
    print("2. Aggregation: Sales by Category")
    print("─" * 70)

    plan2 = {
        "intent": "aggregate",
        "entities": {
            "base_table": "order_items",
            "aggregations": [
                {"function": "SUM", "field": "order_items.quantity * order_items.unit_price", "alias": "total_sales"},
                {"function": "COUNT", "field": "DISTINCT orders.id", "alias": "order_count"},
            ],
            "joins": [
                {
                    "type": "INNER",
                    "table": "products",
                    "on": "order_items.product_id = products.id"
                },
                {
                    "type": "INNER",
                    "table": "categories",
                    "on": "products.category_id = categories.id"
                },
                {
                    "type": "INNER",
                    "table": "orders",
                    "on": "order_items.order_id = orders.id"
                },
            ],
            "filters": [
                {"field": "orders.created_at", "operator": ">=", "value": "YEAR_START"}
            ],
            "grouping": ["categories.name"],
            "ordering": [{"field": "total_sales", "direction": "DESC"}],
        }
    }

    print("Plan:", plan2["entities"])
    print("\nGenerated SQL:")
    print(adapter.generate(plan2))

    # Example 3: Complex filtering with multiple conditions
    print("\n" + "─" * 70)
    print("3. Complex Filtering: Active Premium Users")
    print("─" * 70)

    plan3 = {
        "intent": "select",
        "entities": {
            "table": "users",
            "columns": ["id", "name", "email", "subscription_tier", "last_login"],
            "filters": [
                {"field": "status", "operator": "=", "value": "active"},
                {"field": "subscription_tier", "operator": "IN", "value": ["premium", "enterprise"]},
                {"field": "last_login", "operator": ">=", "value": "INTERVAL_LAST_MONTH"},
            ],
            "ordering": [{"field": "last_login", "direction": "DESC"}],
        }
    }

    print("Plan:", plan3["entities"])
    print("\nGenerated SQL:")
    print(adapter.generate(plan3))

    # Example 4: Products with Average Rating
    print("\n" + "─" * 70)
    print("4. Aggregation with HAVING: Top Rated Products")
    print("─" * 70)

    plan4 = {
        "intent": "aggregate",
        "entities": {
            "base_table": "products",
            "aggregations": [
                {"function": "AVG", "field": "reviews.rating", "alias": "avg_rating"},
                {"function": "COUNT", "field": "reviews.id", "alias": "review_count"},
            ],
            "joins": [
                {
                    "type": "LEFT",
                    "table": "reviews",
                    "on": "products.id = reviews.product_id"
                }
            ],
            "filters": [
                {"field": "products.is_active", "operator": "=", "value": True}
            ],
            "grouping": ["products.id", "products.name"],
            "having": [
                {"aggregation": "COUNT", "field": "reviews.id", "operator": ">=", "value": 5, "param": "minReviews"}
            ],
            "ordering": [{"field": "avg_rating", "direction": "DESC"}],
            "limit": 20
        }
    }

    print("Plan:", plan4["entities"])
    print("\nGenerated SQL:")
    print(adapter.generate(plan4))

    # Example 5: Customer Lifetime Value
    print("\n" + "─" * 70)
    print("5. Customer Lifetime Value Analysis")
    print("─" * 70)

    plan5 = {
        "intent": "aggregate",
        "entities": {
            "base_table": "users",
            "aggregations": [
                {"function": "COUNT", "field": "orders.id", "alias": "total_orders"},
                {"function": "SUM", "field": "orders.total", "alias": "lifetime_value"},
                {"function": "AVG", "field": "orders.total", "alias": "avg_order_value"},
                {"function": "MAX", "field": "orders.created_at", "alias": "last_order_date"},
            ],
            "joins": [
                {
                    "type": "LEFT",
                    "table": "orders",
                    "on": "users.id = orders.user_id"
                }
            ],
            "filters": [
                {"field": "users.status", "operator": "=", "value": "active"}
            ],
            "grouping": ["users.id", "users.name", "users.email"],
            "ordering": [{"field": "lifetime_value", "direction": "DESC"}],
            "limit": 100
        }
    }

    print("Plan:", plan5["entities"])
    print("\nGenerated SQL:")
    print(adapter.generate(plan5))

    # Example 6: Insert statement
    print("\n" + "─" * 70)
    print("6. INSERT: New User")
    print("─" * 70)

    plan6 = {
        "intent": "insert",
        "entities": {
            "table": "users",
            "values": {
                "email": "john@example.com",
                "name": "John Doe",
                "status": "active",
                "subscription_tier": "free",
                "country": "PL",
            }
        }
    }

    print("Plan:", plan6["entities"])
    print("\nGenerated SQL:")
    print(adapter.generate(plan6))

    # Example 7: Update with conditions
    print("\n" + "─" * 70)
    print("7. UPDATE: Upgrade User Subscription")
    print("─" * 70)

    plan7 = {
        "intent": "update",
        "entities": {
            "table": "users",
            "values": {
                "subscription_tier": "premium",
            },
            "filters": [
                {"field": "email", "operator": "=", "value": "john@example.com"}
            ]
        }
    }

    print("Plan:", plan7["entities"])
    print("\nGenerated SQL:")
    print(adapter.generate(plan7))

    # Demonstrate safety policy
    print("\n" + "=" * 70)
    print("Safety Policy Demonstration")
    print("=" * 70)

    # Try to delete without WHERE
    plan_unsafe = {
        "intent": "delete",
        "entities": {
            "table": "users",
            "filters": []  # No filters = affects all rows
        }
    }

    command = adapter.generate(plan_unsafe)
    safety_check = adapter.check_safety(command)

    print("\nAttempted command:", command)
    print("Safety check result:", safety_check)

    if not safety_check["allowed"]:
        print(f"❌ Blocked: {safety_check.get('reason', 'Safety violation')}")


if __name__ == "__main__":
    main()
