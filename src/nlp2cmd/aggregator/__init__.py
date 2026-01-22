"""
Result Aggregator for NLP2CMD.

Aggregates results from multi-step execution,
formats output for user consumption, and prepares
data for optional LLM summarization.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

from nlp2cmd.executor import ExecutionResult, StepResult, StepStatus


class OutputFormat(Enum):
    """Output format types."""
    
    TEXT = "text"
    TABLE = "table"
    JSON = "json"
    MARKDOWN = "markdown"
    SUMMARY = "summary"


@dataclass
class AggregatedResult:
    """Aggregated result from plan execution."""
    
    success: bool
    data: Any
    summary: str
    format: OutputFormat
    step_count: int
    total_duration_ms: float
    trace_id: str
    details: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class ResultAggregator:
    """
    Aggregates and formats execution results.
    
    Provides:
    - Multi-step result aggregation
    - Multiple output formats
    - Data summarization
    - Error reporting
    """
    
    def __init__(self, default_format: OutputFormat = OutputFormat.TEXT):
        """
        Initialize aggregator.
        
        Args:
            default_format: Default output format
        """
        self.default_format = default_format
    
    def aggregate(
        self,
        execution_result: ExecutionResult,
        format: Optional[OutputFormat] = None,
        include_details: bool = True,
    ) -> AggregatedResult:
        """
        Aggregate execution results.
        
        Args:
            execution_result: Result from plan executor
            format: Output format
            include_details: Include step-by-step details
            
        Returns:
            AggregatedResult
        """
        format = format or self.default_format
        
        # Collect step details
        details = []
        if include_details:
            for step in execution_result.steps:
                details.append(self._format_step_detail(step))
        
        # Generate summary
        summary = self._generate_summary(execution_result)
        
        # Format main data
        data = self._format_data(execution_result.final_result, format)
        
        return AggregatedResult(
            success=execution_result.success,
            data=data,
            summary=summary,
            format=format,
            step_count=len(execution_result.steps),
            total_duration_ms=execution_result.total_duration_ms,
            trace_id=execution_result.trace_id,
            details=details,
            metadata=execution_result.metadata,
        )
    
    def _format_step_detail(self, step: StepResult) -> dict[str, Any]:
        """Format a single step's details."""
        detail = {
            "step": step.step_index + 1,
            "action": step.action,
            "status": step.status.value,
            "duration_ms": step.duration_ms,
        }
        
        if step.status == StepStatus.FAILED:
            detail["error"] = step.error
        elif step.status == StepStatus.SUCCESS:
            # Truncate large results
            if step.result is not None:
                if isinstance(step.result, (list, dict)):
                    result_str = json.dumps(step.result)
                    if len(result_str) > 200:
                        detail["result_preview"] = result_str[:200] + "..."
                        detail["result_size"] = len(step.result) if isinstance(step.result, list) else len(result_str)
                    else:
                        detail["result"] = step.result
                else:
                    detail["result"] = step.result
        
        if step.iterations > 1:
            detail["iterations"] = step.iterations
        
        return detail
    
    def _generate_summary(self, result: ExecutionResult) -> str:
        """Generate a human-readable summary."""
        lines = []
        
        # Overall status
        status_emoji = "✅" if result.success else "❌"
        lines.append(f"{status_emoji} Execution {'completed' if result.success else 'failed'}")
        
        # Step summary
        success_count = sum(1 for s in result.steps if s.status == StepStatus.SUCCESS)
        failed_count = sum(1 for s in result.steps if s.status == StepStatus.FAILED)
        skipped_count = sum(1 for s in result.steps if s.status == StepStatus.SKIPPED)
        
        lines.append(f"   Steps: {success_count} succeeded, {failed_count} failed, {skipped_count} skipped")
        lines.append(f"   Duration: {result.total_duration_ms:.1f}ms")
        lines.append(f"   Trace ID: {result.trace_id}")
        
        # Error details
        if not result.success:
            for step in result.steps:
                if step.status == StepStatus.FAILED:
                    lines.append(f"\n   ❌ Step {step.step_index + 1} ({step.action}): {step.error}")
        
        # Result preview
        if result.final_result is not None:
            lines.append("\n   📊 Result:")
            preview = self._preview_result(result.final_result)
            for line in preview.split("\n"):
                lines.append(f"      {line}")
        
        return "\n".join(lines)
    
    def _preview_result(self, result: Any, max_items: int = 5) -> str:
        """Generate a preview of the result."""
        if result is None:
            return "None"
        
        if isinstance(result, list):
            if len(result) == 0:
                return "Empty list"
            
            items = result[:max_items]
            preview = f"List with {len(result)} items:\n"
            
            for i, item in enumerate(items):
                if isinstance(item, dict):
                    preview += f"  [{i}] {json.dumps(item)[:100]}\n"
                else:
                    preview += f"  [{i}] {str(item)[:100]}\n"
            
            if len(result) > max_items:
                preview += f"  ... and {len(result) - max_items} more"
            
            return preview
        
        if isinstance(result, dict):
            return f"Dict with {len(result)} keys: {list(result.keys())[:5]}"
        
        if isinstance(result, str):
            if len(result) > 200:
                return result[:200] + "..."
            return result
        
        return str(result)
    
    def _format_data(self, data: Any, format: OutputFormat) -> Any:
        """Format data according to output format."""
        if data is None:
            return None
        
        if format == OutputFormat.JSON:
            return data  # Return as-is for JSON
        
        if format == OutputFormat.TABLE:
            return self._to_table(data)
        
        if format == OutputFormat.MARKDOWN:
            return self._to_markdown(data)
        
        if format == OutputFormat.SUMMARY:
            return self._to_summary(data)
        
        # TEXT format
        return self._to_text(data)
    
    def _to_text(self, data: Any) -> str:
        """Convert data to text format."""
        if isinstance(data, list):
            if len(data) == 0:
                return "No results"
            
            lines = []
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    lines.append(f"{i + 1}. {json.dumps(item)}")
                else:
                    lines.append(f"{i + 1}. {item}")
            
            return "\n".join(lines)
        
        if isinstance(data, dict):
            lines = []
            for key, value in data.items():
                lines.append(f"{key}: {value}")
            return "\n".join(lines)
        
        return str(data)
    
    def _to_table(self, data: Any) -> str:
        """Convert data to ASCII table format."""
        if not isinstance(data, list) or len(data) == 0:
            return self._to_text(data)
        
        if not isinstance(data[0], dict):
            return self._to_text(data)
        
        # Get all columns
        columns = list(data[0].keys())
        
        # Calculate column widths
        widths = {col: len(col) for col in columns}
        for row in data:
            for col in columns:
                val = str(row.get(col, ""))
                widths[col] = max(widths[col], len(val))
        
        # Build table
        lines = []
        
        # Header
        header = " | ".join(col.ljust(widths[col]) for col in columns)
        separator = "-+-".join("-" * widths[col] for col in columns)
        
        lines.append(header)
        lines.append(separator)
        
        # Rows
        for row in data:
            line = " | ".join(
                str(row.get(col, "")).ljust(widths[col])
                for col in columns
            )
            lines.append(line)
        
        return "\n".join(lines)
    
    def _to_markdown(self, data: Any) -> str:
        """Convert data to Markdown format."""
        if not isinstance(data, list) or len(data) == 0:
            return f"```\n{self._to_text(data)}\n```"
        
        if not isinstance(data[0], dict):
            lines = ["```"]
            for item in data:
                lines.append(f"- {item}")
            lines.append("```")
            return "\n".join(lines)
        
        # Get columns
        columns = list(data[0].keys())
        
        # Build markdown table
        lines = []
        
        # Header
        lines.append("| " + " | ".join(columns) + " |")
        lines.append("| " + " | ".join("---" for _ in columns) + " |")
        
        # Rows
        for row in data:
            values = [str(row.get(col, "")) for col in columns]
            lines.append("| " + " | ".join(values) + " |")
        
        return "\n".join(lines)
    
    def _to_summary(self, data: Any) -> str:
        """Convert data to summary format."""
        if data is None:
            return "No data"
        
        if isinstance(data, list):
            if len(data) == 0:
                return "Empty result set"
            
            summary = f"Result set with {len(data)} items"
            
            if isinstance(data[0], dict):
                # Numeric aggregation
                numeric_cols = [
                    k for k, v in data[0].items()
                    if isinstance(v, (int, float))
                ]
                
                if numeric_cols:
                    summary += "\n\nNumeric summaries:"
                    for col in numeric_cols[:5]:
                        values = [row.get(col, 0) for row in data]
                        summary += f"\n  {col}: min={min(values)}, max={max(values)}, avg={sum(values)/len(values):.2f}"
            
            return summary
        
        if isinstance(data, dict):
            return f"Result with {len(data)} fields: {', '.join(data.keys())}"
        
        return f"Result: {str(data)[:200]}"
    
    def to_llm_context(
        self,
        aggregated: AggregatedResult,
        max_tokens: int = 1000,
    ) -> str:
        """
        Prepare aggregated result for LLM context.
        
        Useful for follow-up questions or explanations.
        """
        lines = []
        
        lines.append("Execution Result:")
        lines.append(f"- Status: {'Success' if aggregated.success else 'Failed'}")
        lines.append(f"- Steps executed: {aggregated.step_count}")
        lines.append(f"- Duration: {aggregated.total_duration_ms:.1f}ms")
        
        if aggregated.data is not None:
            lines.append("\nResult Data:")
            
            # Serialize and truncate
            if isinstance(aggregated.data, str):
                data_str = aggregated.data
            else:
                data_str = json.dumps(aggregated.data, indent=2)
            
            # Rough token estimation (4 chars per token)
            max_chars = max_tokens * 4
            
            if len(data_str) > max_chars:
                data_str = data_str[:max_chars] + "\n... (truncated)"
            
            lines.append(data_str)
        
        return "\n".join(lines)


__all__ = [
    "ResultAggregator",
    "AggregatedResult",
    "OutputFormat",
]
