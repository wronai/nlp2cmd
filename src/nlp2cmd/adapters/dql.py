"""
DQL (Doctrine Query Language) Adapter for NLP2CMD.

Supports Doctrine ORM query generation for PHP/Symfony applications.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from nlp2cmd.adapters.base import AdapterConfig, BaseDSLAdapter, SafetyPolicy


@dataclass
class DQLSafetyPolicy(SafetyPolicy):
    """DQL-specific safety policy."""

    allow_delete: bool = False
    allow_update: bool = True
    require_where: bool = True
    max_results: int = 1000


@dataclass
class EntityContext:
    """Doctrine entity context."""

    entities: dict[str, dict[str, Any]] = field(default_factory=dict)
    aliases: dict[str, str] = field(default_factory=dict)


class DQLAdapter(BaseDSLAdapter):
    """
    DQL adapter for Doctrine ORM queries.

    Transforms natural language into DQL queries
    with QueryBuilder syntax for PHP/Symfony applications.
    """

    DSL_NAME = "dql"
    DSL_VERSION = "1.0"

    INTENTS = {
        "select": {
            "patterns": ["pobierz", "znajdź", "get", "find", "select"],
            "required_entities": ["entity"],
            "optional_entities": ["fields", "filters", "ordering", "limit"],
        },
        "count": {
            "patterns": ["policz", "count", "ile"],
            "required_entities": ["entity"],
            "optional_entities": ["filters"],
        },
        "aggregate": {
            "patterns": ["suma", "średnia", "sum", "avg", "aggregate"],
            "required_entities": ["entity", "field", "function"],
        },
        "join": {
            "patterns": ["połącz", "join", "z relacją"],
            "required_entities": ["entity", "relation"],
        },
    }

    def __init__(
        self,
        entity_context: Optional[dict[str, Any]] = None,
        safety_policy: Optional[DQLSafetyPolicy] = None,
        config: Optional[AdapterConfig] = None,
    ):
        """
        Initialize DQL adapter.

        Args:
            entity_context: Doctrine entity definitions
            safety_policy: DQL-specific safety policy
            config: Adapter configuration
        """
        super().__init__(config, safety_policy or DQLSafetyPolicy())
        self.entities = self._parse_entity_context(entity_context or {})

    def _parse_entity_context(self, ctx: dict[str, Any]) -> EntityContext:
        """Parse entity context."""
        return EntityContext(
            entities=ctx.get("entities", {}),
            aliases=ctx.get("aliases", {}),
        )

    def _get_entity_fqcn(self, name: str) -> str:
        """Get fully qualified class name for entity."""
        return self.entities.aliases.get(name, f"App\\Entity\\{name}")

    def generate(self, plan: dict[str, Any]) -> str:
        """Generate DQL from execution plan."""
        intent = plan.get("intent", "select")
        entities = plan.get("entities", {})
        output_format = entities.get("output_format", "query_builder")

        if output_format == "dql":
            return self._generate_raw_dql(intent, entities)
        return self._generate_query_builder(intent, entities)

    def _generate_query_builder(self, intent: str, entities: dict[str, Any]) -> str:
        """Generate QueryBuilder syntax."""
        generators = {
            "select": self._generate_qb_select,
            "entity_retrieval": self._generate_qb_select,
            "count": self._generate_qb_count,
            "aggregate": self._generate_qb_aggregate,
            "aggregation": self._generate_qb_aggregate,
        }

        generator = generators.get(intent, self._generate_qb_select)
        return generator(entities)

    def _generate_qb_select(self, entities: dict[str, Any]) -> str:
        """Generate SELECT QueryBuilder."""
        entity = entities.get("root_entity", entities.get("entity", "Entity"))
        alias = entity[0].lower()
        fields = entities.get("fields", entities.get("projection", []))
        joins = entities.get("joins", [])
        filters = entities.get("filters", [])
        grouping = entities.get("grouping", [])
        having = entities.get("having", [])
        ordering = entities.get("ordering", [])
        limit = entities.get("limit")

        lines = [
            f"$qb = $this->createQueryBuilder('{alias}')"
        ]

        # SELECT fields
        if fields and fields != "*":
            if isinstance(fields, list):
                # Check if we need partial select
                all_fields = [f for f in fields if f.startswith(alias + ".")]
                if all_fields:
                    field_str = ", ".join(f.split(".")[-1] for f in all_fields)
                    lines.append(f"    ->select('PARTIAL {alias}.{{id, {field_str}}}')")
            else:
                lines.append(f"    ->select('{fields}')")

        # JOINs
        join_aliases = {alias: entity}
        for i, join in enumerate(joins):
            join_type = join.get("type", "LEFT").lower()
            relation = join.get("relation", "")
            join_alias = join.get("alias", f"j{i}")
            join_aliases[join_alias] = join.get("target", "")

            method = f"{join_type}Join" if join_type != "inner" else "innerJoin"
            lines.append(f"    ->{method}('{alias}.{relation}', '{join_alias}')")

        # WHERE filters
        param_count = 0
        for f in filters:
            field = f.get("field", "")
            operator = f.get("operator", "=")
            value = f.get("value")

            param_name = f"param{param_count}"
            param_count += 1

            if operator == "=":
                lines.append(f"    ->andWhere('{field} = :{param_name}')")
            elif operator in [">", "<", ">=", "<="]:
                lines.append(f"    ->andWhere('{field} {operator} :{param_name}')")
            elif operator.upper() == "LIKE":
                lines.append(f"    ->andWhere('{field} LIKE :{param_name}')")
            elif operator.upper() == "IN":
                lines.append(f"    ->andWhere('{field} IN (:{param_name})')")
            elif operator.upper() == "IS NULL":
                lines.append(f"    ->andWhere('{field} IS NULL')")
                continue

            lines.append(f"    ->setParameter('{param_name}', {self._php_value(value)})")

        # GROUP BY
        if grouping:
            for group_field in grouping:
                lines.append(f"    ->groupBy('{group_field}')")

        # HAVING
        for h in having:
            agg = h.get("aggregation", "COUNT")
            field = h.get("field", "*")
            op = h.get("operator", ">")
            value = h.get("value", 0)
            param_name = h.get("param", "minCount")
            lines.append(f"    ->having('{agg}({field}) {op} :{param_name}')")
            lines.append(f"    ->setParameter('{param_name}', {value})")

        # ORDER BY
        for o in ordering:
            if isinstance(o, dict):
                lines.append(
                    f"    ->orderBy('{o.get('field', '')}', '{o.get('direction', 'ASC')}')"
                )
            else:
                lines.append(f"    ->orderBy('{o}')")

        # LIMIT
        if limit:
            lines.append(f"    ->setMaxResults({limit})")

        # Close and execute
        lines.append(";")
        lines.append("")
        lines.append("return $qb->getQuery()->getResult();")

        return "\n".join(lines)

    def _generate_qb_count(self, entities: dict[str, Any]) -> str:
        """Generate COUNT QueryBuilder."""
        entity = entities.get("entity", "Entity")
        alias = entity[0].lower()
        filters = entities.get("filters", [])

        lines = [
            f"$qb = $this->createQueryBuilder('{alias}')",
            f"    ->select('COUNT({alias})')"
        ]

        for f in filters:
            field = f.get("field", "")
            operator = f.get("operator", "=")
            value = f.get("value")
            lines.append(f"    ->andWhere('{field} {operator} :param')")
            lines.append(f"    ->setParameter('param', {self._php_value(value)})")

        lines.append(";")
        lines.append("")
        lines.append("return $qb->getQuery()->getSingleScalarResult();")

        return "\n".join(lines)

    def _generate_qb_aggregate(self, entities: dict[str, Any]) -> str:
        """Generate aggregate QueryBuilder."""
        entity = entities.get("base_table", entities.get("entity", "Entity"))
        alias = entity[0].lower() if entity else "e"
        aggregations = entities.get("aggregations", [])
        grouping = entities.get("grouping", [])
        joins = entities.get("joins", [])
        filters = entities.get("filters", [])
        ordering = entities.get("ordering", [])

        # Build select items
        select_items = []
        for g in grouping:
            select_items.append(f"'{g}'")

        for agg in aggregations:
            func = agg.get("function", "COUNT")
            field = agg.get("field", "*")
            alias_name = agg.get("alias", f"{func.lower()}Result")
            select_items.append(f"'{func}({field}) AS {alias_name}'")

        lines = [
            f"$qb = $this->createQueryBuilder('{alias}')",
            f"    ->select([{', '.join(select_items)}])"
        ]

        # JOINs
        for i, join in enumerate(joins):
            join_type = join.get("type", "INNER").lower()
            join_table = join.get("table", "")
            join_on = join.get("on", "")
            join_alias = join_table[0].lower() if join_table else f"j{i}"

            method = f"{join_type}Join" if join_type != "inner" else "innerJoin"
            lines.append(f"    ->{method}('{alias}.{join_table.lower()}s', '{join_alias}')")

        # WHERE
        param_count = 0
        for f in filters:
            field = f.get("field", "")
            op = f.get("operator", ">=")
            value = f.get("value")
            param_name = f"param{param_count}"
            param_count += 1
            lines.append(f"    ->andWhere('{field} {op} :{param_name}')")
            lines.append(f"    ->setParameter('{param_name}', {self._php_value(value)})")

        # GROUP BY
        if grouping:
            lines.append(f"    ->groupBy('{', '.join(grouping)}')")

        # ORDER BY
        for o in ordering:
            if isinstance(o, dict):
                lines.append(
                    f"    ->orderBy('{o.get('field', '')}', '{o.get('direction', 'DESC')}')"
                )

        lines.append(";")
        lines.append("")
        lines.append("return $qb->getQuery()->getArrayResult();")

        return "\n".join(lines)

    def _generate_raw_dql(self, intent: str, entities: dict[str, Any]) -> str:
        """Generate raw DQL string."""
        entity = entities.get("root_entity", entities.get("entity", "Entity"))
        entity_fqcn = self._get_entity_fqcn(entity)
        alias = entity[0].lower()
        fields = entities.get("fields", ["*"])
        joins = entities.get("joins", [])
        filters = entities.get("filters", [])
        grouping = entities.get("grouping", [])
        ordering = entities.get("ordering", [])
        limit = entities.get("limit")

        # SELECT
        if fields == ["*"] or fields == "*":
            select_str = alias
        elif isinstance(fields, list):
            select_str = ", ".join(fields)
        else:
            select_str = fields

        dql = f"SELECT {select_str}\nFROM {entity_fqcn} {alias}"

        # JOINs
        for join in joins:
            join_type = join.get("type", "LEFT")
            relation = join.get("relation", "")
            join_alias = join.get("alias", relation[0].lower())
            dql += f"\n{join_type} JOIN {alias}.{relation} {join_alias}"

        # WHERE
        if filters:
            where_clauses = []
            for f in filters:
                field = f.get("field", "")
                op = f.get("operator", "=")
                value = f.get("value")
                where_clauses.append(f"{field} {op} {self._dql_value(value)}")
            dql += f"\nWHERE {' AND '.join(where_clauses)}"

        # GROUP BY
        if grouping:
            dql += f"\nGROUP BY {', '.join(grouping)}"

        # ORDER BY
        if ordering:
            order_parts = []
            for o in ordering:
                if isinstance(o, dict):
                    order_parts.append(f"{o.get('field', '')} {o.get('direction', 'ASC')}")
                else:
                    order_parts.append(str(o))
            dql += f"\nORDER BY {', '.join(order_parts)}"

        return dql

    def _php_value(self, value: Any) -> str:
        """Format value for PHP."""
        if value is None:
            return "null"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            if value.startswith("new "):  # PHP constructor
                return value
            return f"'{value}'"
        if isinstance(value, list):
            items = ", ".join(self._php_value(v) for v in value)
            return f"[{items}]"
        return str(value)

    def _dql_value(self, value: Any) -> str:
        """Format value for DQL."""
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "true" if value else "false"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            return f"'{value}'"
        return str(value)

    def validate_syntax(self, command: str) -> dict[str, Any]:
        """Validate DQL/QueryBuilder syntax."""
        errors = []
        warnings = []

        # Check for common issues
        if "createQueryBuilder" in command:
            if "getQuery()" not in command:
                warnings.append("QueryBuilder chain should end with getQuery()")

            if "->select(" not in command and "->select('" not in command:
                # Not necessarily an error - default select
                pass

        # Check for unclosed parentheses
        if command.count("(") != command.count(")"):
            errors.append("Unbalanced parentheses")

        # Check for unclosed quotes
        single = command.count("'")
        if single % 2 != 0:
            errors.append("Unclosed string literal")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def check_safety(self, command: str) -> dict[str, Any]:
        """Check DQL against safety policy."""
        policy: DQLSafetyPolicy = self.config.safety_policy  # type: ignore
        command_upper = command.upper()

        if "DELETE" in command_upper and not policy.allow_delete:
            return {
                "allowed": False,
                "reason": "DELETE operations are not allowed",
            }

        if "UPDATE" in command_upper and not policy.allow_update:
            return {
                "allowed": False,
                "reason": "UPDATE operations are not allowed",
            }

        return {"allowed": True}
