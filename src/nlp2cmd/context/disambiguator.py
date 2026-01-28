"""
Context-aware command disambiguation using history.

When queries are ambiguous, uses recent command history to suggest options
and asks the user which command they mean.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from difflib import SequenceMatcher

from rich.console import Console
from rich.table import Table


@dataclass
class DisambiguationResult:
    """Result of disambiguation process."""
    selected_query: str
    selected_command: Optional[str] = None
    from_history: bool = False
    user_input: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class CommandDisambiguator:
    """
    Disambiguates commands using history context.
    
    When a query is ambiguous or similar to previous commands,
    asks the user which one they mean.
    """
    
    def __init__(self, console: Optional[Console] = None):
        self.console = console or Console()
        self._history = None
        
        try:
            from nlp2cmd.history.tracker import get_global_history
            self._history = get_global_history()
        except Exception:
            pass
    
    def find_similar_queries(
        self,
        query: str,
        limit: int = 5,
        threshold: float = 0.4,
    ) -> list[tuple[str, str, float]]:
        """
        Find similar queries from history.
        
        Args:
            query: Current query
            limit: Maximum results
            threshold: Minimum similarity (0-1)
        
        Returns:
            List of (query, command, similarity) tuples
        """
        if not self._history:
            return []
        
        recent = self._history.get_recent(50)
        
        # Calculate similarity
        results = []
        seen_queries = set()
        
        for record in reversed(recent):
            if record.query in seen_queries:
                continue
            
            similarity = self._calculate_similarity(query, record.query)
            
            if similarity >= threshold:
                results.append((record.query, record.command, similarity))
                seen_queries.add(record.query)
        
        # Sort by similarity
        results.sort(key=lambda x: x[2], reverse=True)
        
        return results[:limit]
    
    def _calculate_similarity(self, s1: str, s2: str) -> float:
        """Calculate similarity between two strings."""
        s1_lower = s1.lower().strip()
        s2_lower = s2.lower().strip()
        
        # Exact match
        if s1_lower == s2_lower:
            return 1.0
        
        # Check if one contains the other
        if s1_lower in s2_lower or s2_lower in s1_lower:
            return 0.8
        
        # Use SequenceMatcher for fuzzy matching
        return SequenceMatcher(None, s1_lower, s2_lower).ratio()
    
    def disambiguate(
        self,
        query: str,
        auto_select: bool = False,
    ) -> DisambiguationResult:
        """
        Disambiguate a query using history context.
        
        Args:
            query: Current query
            auto_select: If True, automatically select best match
        
        Returns:
            DisambiguationResult with selected query/command
        """
        similar = self.find_similar_queries(query)
        
        if not similar:
            return DisambiguationResult(selected_query=query)
        
        # Do not auto-replace the user's query based on fuzzy similarity.
        # Only auto-select when explicitly requested by the caller.
        best_match = similar[0]
        if auto_select and best_match[2] >= 0.95:
            return DisambiguationResult(
                selected_query=best_match[0],
                selected_command=best_match[1],
                from_history=True,
            )
        
        if auto_select:
            return DisambiguationResult(selected_query=query)
        
        from nlp2cmd.cli.markdown_output import print_yaml_block

        options: list[dict[str, Any]] = []
        for i, (prev_query, prev_cmd, sim) in enumerate(similar, 1):
            cmd_display = prev_cmd[:80] + "..." if len(prev_cmd) > 80 else prev_cmd
            options.append(
                {
                    "option": i,
                    "query": prev_query,
                    "command_preview": cmd_display,
                    "similarity": round(float(sim), 4),
                }
            )

        payload: dict[str, Any] = {
            "status": "found_similar_previous_commands",
            "current_query": query,
            "options": options,
            "selection": {
                "default": 0,
                "0": "use_current_query",
                "range": f"1-{len(similar)}",
                "range_meaning": "use_previous_command",
            },
        }

        print_yaml_block(payload, console=self.console)
        
        response = self.console.input("\n[bold]Select option [0]: [/bold]").strip()
        
        if not response or response == "0":
            return DisambiguationResult(
                selected_query=query,
                user_input=response,
            )
        
        try:
            idx = int(response) - 1
            if 0 <= idx < len(similar):
                selected = similar[idx]
                return DisambiguationResult(
                    selected_query=selected[0],
                    selected_command=selected[1],
                    from_history=True,
                    user_input=response,
                )
        except ValueError:
            pass
        
        # Invalid input - use original query
        return DisambiguationResult(
            selected_query=query,
            user_input=response,
        )
    
    def get_context_suggestions(
        self,
        current_url: Optional[str] = None,
        current_domain: Optional[str] = None,
    ) -> list[str]:
        """
        Get suggestions based on context (URL, domain, etc.).
        
        Returns list of suggested actions based on history for this context.
        """
        if not self._history:
            return []
        
        recent = self._history.get_recent(100)
        suggestions = []
        
        if current_domain:
            # Find actions previously done on this domain
            domain_records = [
                r for r in recent
                if current_domain in r.query.lower() or current_domain in r.command.lower()
            ]
            
            for record in domain_records[:3]:
                if record.success:
                    suggestions.append(f"Repeat: {record.query}")
        
        return suggestions
