"""
Unified command history tracker for all DSL types.

Automatically records:
- All command executions
- Schema usage patterns
- Success/failure rates
- Performance metrics
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class SchemaUsage:
    """Record of schema usage."""
    schema_name: str
    schema_type: str  # appspec, dynamic, browser, learned
    action_id: str
    parameters: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "schema_name": self.schema_name,
            "schema_type": self.schema_type,
            "action_id": self.action_id,
            "parameters": self.parameters,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> SchemaUsage:
        return cls(
            schema_name=data["schema_name"],
            schema_type=data["schema_type"],
            action_id=data["action_id"],
            parameters=data.get("parameters", {}),
        )


@dataclass
class CommandRecord:
    """Record of a command execution."""
    timestamp: str
    query: str  # Original natural language query
    dsl: str  # sql, shell, docker, kubernetes, browser, dql
    intent: Optional[str] = None  # Detected intent
    command: str = ""  # Generated command
    success: bool = True
    exit_code: Optional[int] = None
    duration_ms: float = 0.0
    error: Optional[str] = None
    schema_usage: Optional[SchemaUsage] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "query": self.query,
            "dsl": self.dsl,
            "intent": self.intent,
            "command": self.command,
            "success": self.success,
            "exit_code": self.exit_code,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "schema_usage": self.schema_usage.to_dict() if self.schema_usage else None,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> CommandRecord:
        schema_usage = None
        if data.get("schema_usage"):
            schema_usage = SchemaUsage.from_dict(data["schema_usage"])
        
        return cls(
            timestamp=data["timestamp"],
            query=data["query"],
            dsl=data["dsl"],
            intent=data.get("intent"),
            command=data.get("command", ""),
            success=data.get("success", True),
            exit_code=data.get("exit_code"),
            duration_ms=data.get("duration_ms", 0.0),
            error=data.get("error"),
            schema_usage=schema_usage,
            metadata=data.get("metadata", {}),
        )


class CommandHistory:
    """
    Unified command history tracker.
    
    Automatically records all command executions and schema usage.
    """
    
    def __init__(self, history_file: Optional[Path] = None):
        if history_file is None:
            history_file = Path.home() / ".nlp2cmd" / "command_history.json"
        
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.records: list[CommandRecord] = []
        self._load()
    
    def _load(self):
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [CommandRecord.from_dict(r) for r in data.get("records", [])]
            except Exception:
                self.records = []
    
    def _save(self):
        """Save history to file."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(
                    {
                        "records": [r.to_dict() for r in self.records],
                        "last_updated": datetime.now().isoformat(),
                        "total_commands": len(self.records),
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            # Silent fail - don't break execution if history can't be saved
            pass
    
    def record(
        self,
        query: str,
        dsl: str,
        command: str = "",
        intent: Optional[str] = None,
        success: bool = True,
        exit_code: Optional[int] = None,
        duration_ms: float = 0.0,
        error: Optional[str] = None,
        schema_usage: Optional[SchemaUsage] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Record a command execution."""
        record = CommandRecord(
            timestamp=datetime.now().isoformat(),
            query=query,
            dsl=dsl,
            intent=intent,
            command=command,
            success=success,
            exit_code=exit_code,
            duration_ms=duration_ms,
            error=error,
            schema_usage=schema_usage,
            metadata=metadata or {},
        )
        
        self.records.append(record)
        self._save()
    
    def get_recent(self, limit: int = 50) -> list[CommandRecord]:
        """Get recent command records."""
        return self.records[-limit:]
    
    def get_by_dsl(self, dsl: str, limit: int = 50) -> list[CommandRecord]:
        """Get commands for a specific DSL."""
        filtered = [r for r in self.records if r.dsl == dsl]
        return filtered[-limit:]
    
    def get_stats(self) -> dict[str, Any]:
        """Get overall statistics."""
        if not self.records:
            return {
                "total_commands": 0,
                "success_rate": 0.0,
                "by_dsl": {},
            }
        
        successful = sum(1 for r in self.records if r.success)
        
        # Count by DSL
        dsl_counts: dict[str, int] = {}
        dsl_success: dict[str, int] = {}
        for record in self.records:
            dsl_counts[record.dsl] = dsl_counts.get(record.dsl, 0) + 1
            if record.success:
                dsl_success[record.dsl] = dsl_success.get(record.dsl, 0) + 1
        
        by_dsl = {}
        for dsl, count in dsl_counts.items():
            by_dsl[dsl] = {
                "total": count,
                "successful": dsl_success.get(dsl, 0),
                "success_rate": dsl_success.get(dsl, 0) / count if count > 0 else 0.0,
            }
        
        # Average duration
        durations = [r.duration_ms for r in self.records if r.duration_ms > 0]
        avg_duration = sum(durations) / len(durations) if durations else 0.0
        
        return {
            "total_commands": len(self.records),
            "successful_commands": successful,
            "failed_commands": len(self.records) - successful,
            "success_rate": successful / len(self.records),
            "by_dsl": by_dsl,
            "avg_duration_ms": avg_duration,
            "first_command": self.records[0].timestamp if self.records else None,
            "last_command": self.records[-1].timestamp if self.records else None,
        }
    
    def get_schema_usage_stats(self) -> dict[str, Any]:
        """Get statistics about schema usage."""
        schema_records = [r for r in self.records if r.schema_usage]
        
        if not schema_records:
            return {
                "total_schema_uses": 0,
                "schemas": {},
            }
        
        # Count by schema
        schema_counts: dict[str, dict[str, Any]] = {}
        for record in schema_records:
            if record.schema_usage:
                name = record.schema_usage.schema_name
                if name not in schema_counts:
                    schema_counts[name] = {
                        "total_uses": 0,
                        "successful_uses": 0,
                        "schema_type": record.schema_usage.schema_type,
                        "actions": {},
                    }
                
                schema_counts[name]["total_uses"] += 1
                if record.success:
                    schema_counts[name]["successful_uses"] += 1
                
                action_id = record.schema_usage.action_id
                if action_id not in schema_counts[name]["actions"]:
                    schema_counts[name]["actions"][action_id] = 0
                schema_counts[name]["actions"][action_id] += 1
        
        # Calculate success rates
        for schema_data in schema_counts.values():
            total = schema_data["total_uses"]
            schema_data["success_rate"] = schema_data["successful_uses"] / total if total > 0 else 0.0
        
        return {
            "total_schema_uses": len(schema_records),
            "unique_schemas": len(schema_counts),
            "schemas": schema_counts,
        }
    
    def get_popular_queries(self, limit: int = 10) -> list[tuple[str, int]]:
        """Get most popular queries."""
        query_counts: dict[str, int] = {}
        for record in self.records:
            query_counts[record.query] = query_counts.get(record.query, 0) + 1
        
        sorted_queries = sorted(
            query_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        return sorted_queries[:limit]
    
    def get_failed_commands(self, limit: int = 20) -> list[CommandRecord]:
        """Get recent failed commands for analysis."""
        failed = [r for r in self.records if not r.success]
        return failed[-limit:]
    
    def clear(self):
        """Clear all history."""
        self.records = []
        self._save()
    
    def export_analytics(self, output_file: Path):
        """Export detailed analytics to JSON."""
        analytics = {
            "generated_at": datetime.now().isoformat(),
            "overall_stats": self.get_stats(),
            "schema_usage": self.get_schema_usage_stats(),
            "popular_queries": self.get_popular_queries(20),
            "recent_failures": [r.to_dict() for r in self.get_failed_commands(10)],
        }
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analytics, f, indent=2, ensure_ascii=False)


# Global instance for automatic tracking
_global_history: Optional[CommandHistory] = None


def get_global_history() -> CommandHistory:
    """Get or create global command history instance."""
    global _global_history
    if _global_history is None:
        _global_history = CommandHistory()
    return _global_history


def record_command(
    query: str,
    dsl: str,
    command: str = "",
    **kwargs,
):
    """Convenience function to record to global history."""
    history = get_global_history()
    history.record(query=query, dsl=dsl, command=command, **kwargs)
