"""
SQL DSL Adapter for NLP2CMD.

Supports PostgreSQL, MySQL, SQLite, and MSSQL dialects.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Optional

from nlp2cmd.adapters.base import AdapterConfig, BaseDSLAdapter, SafetyPolicy


@dataclass
class SQLSafetyPolicy(SafetyPolicy):
    """SQL-specific safety policy."""

    allow_delete: bool = False
    allow_truncate: bool = False
    allow_drop: bool = False
    require_where_on_update: bool = True
    require_where_on_delete: bool = True
    max_rows_affected: int = 1000
    allowed_tables: list[str] = field(default_factory=list)
    blocked_tables: list[str] = field(default_factory=list)


@dataclass
class SchemaContext:
    """Database schema context for SQL generation."""

    tables: list[str] = field(default_factory=list)
    columns: dict[str, list[str]] = field(default_factory=dict)
    relations: dict[str, str] = field(default_factory=dict)
    primary_keys: dict[str, str] = field(default_factory=dict)
    indexes: dict[str, list[str]] = field(default_factory=dict)


class SQLAdapter(BaseDSLAdapter):
    """
    SQL adapter supporting multiple database dialects.

    Transforms natural language queries into SQL commands
    with support for PostgreSQL, MySQL, SQLite, and MSSQL.
    """

    DSL_NAME = "sql"
    DSL_VERSION = "1.0"

    DIALECTS = ["postgresql", "mysql", "sqlite", "mssql"]

    INTENTS = {
        "select": {
            "patterns": ["pokaż", "wyświetl", "znajdź", "pobierz", "select", "get", "show", "find"],
            "required_entities": ["table"],
            "optional_entities": ["columns", "filters", "ordering", "limit"],
        },
        "insert": {
            "patterns": ["dodaj", "wstaw", "utwórz", "insert", "add", "create"],
            "required_entities": ["table", "values"],
        },
        "update": {
            "patterns": ["zaktualizuj", "zmień", "ustaw", "update", "modify", "set"],
            "required_entities": ["table", "values"],
            "optional_entities": ["filters"],
        },
        "delete": {
            "patterns": ["usuń", "skasuj", "delete", "remove"],
            "required_entities": ["table"],
            "optional_entities": ["filters"],
        },
        "aggregate": {
            "patterns": ["policz", "zsumuj", "średnia", "count", "sum", "avg", "aggregate"],
            "required_entities": ["table", "aggregation"],
            "optional_entities": ["grouping", "filters"],
        },
        "join": {
            "patterns": ["połącz", "złącz", "join", "combine"],
            "required_entities": ["tables", "join_condition"],
        },
    }

    # SQL keywords for syntax validation
    SQL_KEYWORDS = {
        "SELECT", "FROM", "WHERE", "AND", "OR", "NOT", "IN", "LIKE",
        "ORDER", "BY", "GROUP", "HAVING", "LIMIT", "OFFSET",
        "JOIN", "LEFT", "RIGHT", "INNER", "OUTER", "ON",
        "INSERT", "INTO", "VALUES", "UPDATE", "SET", "DELETE",
        "CREATE", "ALTER", "DROP", "TABLE", "INDEX",
        "AS", "DISTINCT", "COUNT", "SUM", "AVG", "MIN", "MAX",
        "CASE", "WHEN", "THEN", "ELSE", "END", "NULL", "IS",
        "BETWEEN", "EXISTS", "UNION", "ALL", "ASC", "DESC",
    }

    def __init__(
        self,
        dialect: str = "postgresql",
        schema_context: Optional[dict[str, Any]] = None,
        safety_policy: Optional[SQLSafetyPolicy] = None,
        config: Optional[AdapterConfig] = None,
    ):
        """
        Initialize SQL adapter.

        Args:
            dialect: SQL dialect (postgresql, mysql, sqlite, mssql)
            schema_context: Database schema information
            safety_policy: SQL-specific safety policy
            config: Adapter configuration
        """
        super().__init__(config, safety_policy or SQLSafetyPolicy())

        if dialect not in self.DIALECTS:
            raise ValueError(f"Unsupported dialect: {dialect}. Use one of: {self.DIALECTS}")

        self.dialect = dialect
        self.schema = self._parse_schema_context(schema_context or {})

    def _parse_schema_context(self, ctx: dict[str, Any]) -> SchemaContext:
        """Parse schema context dictionary into SchemaContext object."""
        return SchemaContext(
            tables=ctx.get("tables", []),
            columns=ctx.get("columns", {}),
            relations=ctx.get("relations", {}),
            primary_keys=ctx.get("primary_keys", {}),
            indexes=ctx.get("indexes", {}),
        )

    def generate(self, plan: dict[str, Any]) -> str:
        """Generate SQL command from execution plan."""
        intent = plan.get("intent", "select")
        entities = plan.get("entities", {})

        generators = {
            "select": self._generate_select,
            "insert": self._generate_insert,
            "update": self._generate_update,
            "delete": self._generate_delete,
            "aggregate": self._generate_aggregate,
            "data_retrieval": self._generate_select,  # alias
            "aggregation": self._generate_aggregate,  # alias
        }

        generator = generators.get(intent, self._generate_select)
        return generator(entities)

    def _generate_select(self, entities: dict[str, Any]) -> str:
        """Generate SELECT statement."""
        table = entities.get("table", "unknown_table")
        columns = entities.get("columns", entities.get("projection", "*"))
        filters = entities.get("filters", [])
        ordering = entities.get("ordering", [])
        limit = entities.get("limit")
        joins = entities.get("joins", [])

        # Build column list
        if isinstance(columns, list):
            columns_str = ", ".join(columns)
        else:
            columns_str = str(columns)

        # Start building query
        sql = f"SELECT {columns_str}\nFROM {table}"

        # Add JOINs
        for join in joins:
            join_type = join.get("type", "INNER")
            join_table = join.get("table", "")
            join_on = join.get("on", "")
            sql += f"\n{join_type} JOIN {join_table} ON {join_on}"

        # Add WHERE clause
        if filters:
            where_clauses = []
            for f in filters:
                field = f.get("field", "")
                operator = f.get("operator", "=")
                value = self._format_value(f.get("value"))
                where_clauses.append(f"{field} {operator} {value}")
            sql += f"\nWHERE {' AND '.join(where_clauses)}"

        # Add ORDER BY
        if ordering:
            order_clauses = []
            for o in ordering:
                if isinstance(o, dict):
                    order_clauses.append(f"{o.get('field', '')} {o.get('direction', 'ASC')}")
                else:
                    order_clauses.append(str(o))
            sql += f"\nORDER BY {', '.join(order_clauses)}"

        # Add LIMIT
        if limit:
            sql += f"\nLIMIT {limit}"

        return sql + ";"

    def _generate_insert(self, entities: dict[str, Any]) -> str:
        """Generate INSERT statement."""
        table = entities.get("table", "unknown_table")
        values = entities.get("values", {})

        if not values:
            return f"INSERT INTO {table} DEFAULT VALUES;"

        columns = list(values.keys())
        value_list = [self._format_value(v) for v in values.values()]

        return (
            f"INSERT INTO {table} ({', '.join(columns)})\n"
            f"VALUES ({', '.join(value_list)});"
        )

    def _generate_update(self, entities: dict[str, Any]) -> str:
        """Generate UPDATE statement."""
        table = entities.get("table", "unknown_table")
        values = entities.get("values", {})
        filters = entities.get("filters", [])

        if not values:
            raise ValueError("UPDATE requires values to set")

        set_clauses = [f"{k} = {self._format_value(v)}" for k, v in values.items()]
        sql = f"UPDATE {table}\nSET {', '.join(set_clauses)}"

        if filters:
            where_clauses = []
            for f in filters:
                field = f.get("field", "")
                operator = f.get("operator", "=")
                value = self._format_value(f.get("value"))
                where_clauses.append(f"{field} {operator} {value}")
            sql += f"\nWHERE {' AND '.join(where_clauses)}"

        return sql + ";"

    def _generate_delete(self, entities: dict[str, Any]) -> str:
        """Generate DELETE statement."""
        table = entities.get("table", "unknown_table")
        filters = entities.get("filters", [])

        sql = f"DELETE FROM {table}"

        if filters:
            where_clauses = []
            for f in filters:
                field = f.get("field", "")
                operator = f.get("operator", "=")
                value = self._format_value(f.get("value"))
                where_clauses.append(f"{field} {operator} {value}")
            sql += f"\nWHERE {' AND '.join(where_clauses)}"

        return sql + ";"

    def _generate_aggregate(self, entities: dict[str, Any]) -> str:
        """Generate aggregate query with GROUP BY."""
        table = entities.get("base_table", entities.get("table", "unknown_table"))
        aggregations = entities.get("aggregations", [])
        grouping = entities.get("grouping", [])
        filters = entities.get("filters", [])
        joins = entities.get("joins", [])
        ordering = entities.get("ordering", [])

        # Build SELECT list
        select_items = []

        # Add grouping columns
        for col in grouping:
            select_items.append(col)

        # Add aggregations
        for agg in aggregations:
            func = agg.get("function", "COUNT")
            field = agg.get("field", "*")
            alias = agg.get("alias", f"{func.lower()}_{field}")
            select_items.append(f"{func}({field}) AS {alias}")

        if not select_items:
            select_items = ["COUNT(*) AS count"]

        sql = f"SELECT {', '.join(select_items)}\nFROM {table}"

        # Add JOINs
        for join in joins:
            join_type = join.get("type", "INNER")
            join_table = join.get("table", "")
            join_on = join.get("on", "")
            sql += f"\n{join_type} JOIN {join_table} ON {join_on}"

        # Add WHERE
        if filters:
            where_clauses = []
            for f in filters:
                field = f.get("field", "")
                operator = f.get("operator", "=")
                value = self._format_value(f.get("value"))
                where_clauses.append(f"{field} {operator} {value}")
            sql += f"\nWHERE {' AND '.join(where_clauses)}"

        # Add GROUP BY
        if grouping:
            sql += f"\nGROUP BY {', '.join(grouping)}"

        # Add ORDER BY
        if ordering:
            order_clauses = []
            for o in ordering:
                if isinstance(o, dict):
                    order_clauses.append(f"{o.get('field', '')} {o.get('direction', 'ASC')}")
                else:
                    order_clauses.append(str(o))
            sql += f"\nORDER BY {', '.join(order_clauses)}"

        return sql + ";"

    def _format_value(self, value: Any) -> str:
        """Format a value for SQL."""
        if value is None:
            return "NULL"
        if isinstance(value, bool):
            return "TRUE" if value else "FALSE"
        if isinstance(value, (int, float)):
            return str(value)
        if isinstance(value, str):
            # Handle special temporal values
            if value == "INTERVAL_LAST_MONTH":
                return self._interval_expr("1 month")
            if value == "YEAR_START":
                return self._year_start_expr()
            # Escape single quotes
            escaped = value.replace("'", "''")
            return f"'{escaped}'"
        return str(value)

    def _interval_expr(self, interval: str) -> str:
        """Generate dialect-specific interval expression."""
        if self.dialect == "postgresql":
            return f"NOW() - INTERVAL '{interval}'"
        elif self.dialect == "mysql":
            return f"DATE_SUB(NOW(), INTERVAL {interval.split()[0]} {interval.split()[1].upper()})"
        elif self.dialect == "sqlite":
            return f"datetime('now', '-{interval}')"
        else:
            return f"DATEADD({interval.split()[1]}, -{interval.split()[0]}, GETDATE())"

    def _year_start_expr(self) -> str:
        """Generate dialect-specific year start expression."""
        if self.dialect == "postgresql":
            return "DATE_TRUNC('year', CURRENT_DATE)"
        elif self.dialect == "mysql":
            return "DATE_FORMAT(CURRENT_DATE, '%Y-01-01')"
        elif self.dialect == "sqlite":
            return "date('now', 'start of year')"
        else:
            return "DATEADD(yy, DATEDIFF(yy, 0, GETDATE()), 0)"

    def validate_syntax(self, command: str) -> dict[str, Any]:
        """Validate SQL syntax."""
        errors = []
        warnings = []

        # Check parentheses balance
        if command.count("(") != command.count(")"):
            errors.append("Unbalanced parentheses")

        # Check quote balance
        single_quotes = command.count("'") - command.count("\\'") * 2
        if single_quotes % 2 != 0:
            errors.append("Unclosed string literal")

        # Check for common issues
        command_upper = command.upper()

        if "DELETE FROM" in command_upper and "WHERE" not in command_upper:
            warnings.append("DELETE without WHERE will affect all rows")

        if "UPDATE" in command_upper and "SET" in command_upper and "WHERE" not in command_upper:
            warnings.append("UPDATE without WHERE will affect all rows")

        # Try to use sqlparse if available
        try:
            import sqlparse

            parsed = sqlparse.parse(command)
            if not parsed or not parsed[0].tokens:
                errors.append("Failed to parse SQL statement")
        except ImportError:
            pass  # sqlparse not available

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
        }

    def check_safety(self, command: str) -> dict[str, Any]:
        """Check SQL command against safety policy."""
        policy: SQLSafetyPolicy = self.config.safety_policy  # type: ignore

        command_upper = command.upper()

        # Check DELETE
        if "DELETE" in command_upper and not policy.allow_delete:
            return {
                "allowed": False,
                "reason": "DELETE operations are disabled by safety policy",
                "alternatives": ["Use soft-delete: UPDATE table SET deleted_at = NOW() WHERE ..."],
            }

        # Check TRUNCATE
        if "TRUNCATE" in command_upper and not policy.allow_truncate:
            return {
                "allowed": False,
                "reason": "TRUNCATE operations are disabled by safety policy",
            }

        # Check DROP
        if "DROP" in command_upper and not policy.allow_drop:
            return {
                "allowed": False,
                "reason": "DROP operations are disabled by safety policy",
            }

        # Check WHERE requirement for UPDATE
        if (
            policy.require_where_on_update
            and "UPDATE" in command_upper
            and "WHERE" not in command_upper
        ):
            return {
                "allowed": False,
                "reason": "UPDATE without WHERE clause is not allowed",
            }

        # Check WHERE requirement for DELETE
        if (
            policy.require_where_on_delete
            and "DELETE" in command_upper
            and "WHERE" not in command_upper
        ):
            return {
                "allowed": False,
                "reason": "DELETE without WHERE clause is not allowed",
            }

        # Check blocked tables
        for table in policy.blocked_tables:
            if re.search(rf"\b{table}\b", command, re.IGNORECASE):
                return {
                    "allowed": False,
                    "reason": f"Access to table '{table}' is blocked",
                }

        return {"allowed": True}

    def _pretty_format(self, command: str) -> str:
        """Pretty format SQL command."""
        try:
            import sqlparse

            return sqlparse.format(
                command,
                reindent=True,
                keyword_case="upper",
                identifier_case="lower",
            )
        except ImportError:
            return command

    def get_schema_context(self) -> dict[str, Any]:
        """Get schema context."""
        return {
            "tables": self.schema.tables,
            "columns": self.schema.columns,
            "relations": self.schema.relations,
        }
