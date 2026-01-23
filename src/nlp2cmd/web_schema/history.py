"""
Interaction history tracking and learning.

Opcja C: Uczenie się z interakcji - zapisywane w historii poprzednich akcji.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class InteractionRecord:
    """Record of a single browser interaction."""
    timestamp: str
    url: str
    domain: str
    action_type: str  # goto, type, click, press
    selector: Optional[str] = None
    text: Optional[str] = None
    success: bool = True
    error: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "url": self.url,
            "domain": self.domain,
            "action_type": self.action_type,
            "selector": self.selector,
            "text": self.text,
            "success": self.success,
            "error": self.error,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InteractionRecord:
        return cls(
            timestamp=data["timestamp"],
            url=data["url"],
            domain=data["domain"],
            action_type=data["action_type"],
            selector=data.get("selector"),
            text=data.get("text"),
            success=data.get("success", True),
            error=data.get("error"),
            metadata=data.get("metadata", {}),
        )


class InteractionHistory:
    """
    Tracks and learns from browser interactions.
    
    Features:
    - Records all browser actions
    - Learns which selectors work for each domain
    - Suggests selectors based on past success
    - Builds domain-specific knowledge
    """
    
    def __init__(self, history_file: Optional[Path] = None):
        if history_file is None:
            history_file = Path.home() / ".nlp2cmd" / "browser_history.json"
        
        self.history_file = Path(history_file)
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        
        self.records: list[InteractionRecord] = []
        self._load()
    
    def _load(self):
        """Load history from file."""
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.records = [InteractionRecord.from_dict(r) for r in data.get("records", [])]
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
                    },
                    f,
                    indent=2,
                    ensure_ascii=False,
                )
        except Exception as e:
            print(f"Warning: Could not save interaction history: {e}")
    
    def record(
        self,
        url: str,
        domain: str,
        action_type: str,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        success: bool = True,
        error: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
    ):
        """Record a browser interaction."""
        record = InteractionRecord(
            timestamp=datetime.now().isoformat(),
            url=url,
            domain=domain,
            action_type=action_type,
            selector=selector,
            text=text,
            success=success,
            error=error,
            metadata=metadata or {},
        )
        
        self.records.append(record)
        self._save()
    
    def get_successful_selectors(
        self,
        domain: str,
        action_type: str,
        limit: int = 10,
    ) -> list[str]:
        """
        Get selectors that worked for a domain and action type.
        
        Args:
            domain: Domain to filter by
            action_type: Action type (type, click, etc.)
            limit: Maximum number of selectors to return
        
        Returns:
            List of successful selectors, ordered by frequency
        """
        # Filter successful records for this domain and action
        relevant = [
            r for r in self.records
            if r.domain == domain
            and r.action_type == action_type
            and r.success
            and r.selector
        ]
        
        # Count selector frequency
        selector_counts: dict[str, int] = {}
        for record in relevant:
            if record.selector:
                selector_counts[record.selector] = selector_counts.get(record.selector, 0) + 1
        
        # Sort by frequency
        sorted_selectors = sorted(
            selector_counts.items(),
            key=lambda x: x[1],
            reverse=True,
        )
        
        return [sel for sel, _ in sorted_selectors[:limit]]
    
    def get_domain_stats(self, domain: str) -> dict[str, Any]:
        """Get statistics for a domain."""
        domain_records = [r for r in self.records if r.domain == domain]
        
        if not domain_records:
            return {
                "total_interactions": 0,
                "success_rate": 0.0,
                "action_types": {},
            }
        
        successful = sum(1 for r in domain_records if r.success)
        
        # Count action types
        action_counts: dict[str, int] = {}
        for record in domain_records:
            action_counts[record.action_type] = action_counts.get(record.action_type, 0) + 1
        
        return {
            "total_interactions": len(domain_records),
            "success_rate": successful / len(domain_records),
            "successful_interactions": successful,
            "failed_interactions": len(domain_records) - successful,
            "action_types": action_counts,
            "first_interaction": domain_records[0].timestamp,
            "last_interaction": domain_records[-1].timestamp,
        }
    
    def suggest_selector(
        self,
        domain: str,
        action_type: str,
        context: Optional[dict[str, Any]] = None,
    ) -> Optional[str]:
        """
        Suggest a selector based on past successful interactions.
        
        Args:
            domain: Domain to suggest for
            action_type: Action type (type, click, etc.)
            context: Optional context (e.g., field name, button text)
        
        Returns:
            Suggested selector or None
        """
        selectors = self.get_successful_selectors(domain, action_type, limit=1)
        return selectors[0] if selectors else None
    
    def learn_from_success(
        self,
        domain: str,
        action_type: str,
        selector: str,
    ):
        """
        Learn from a successful interaction.
        
        This is called when an action succeeds, reinforcing the selector.
        """
        self.record(
            url=f"https://{domain}",
            domain=domain,
            action_type=action_type,
            selector=selector,
            success=True,
        )
    
    def learn_from_failure(
        self,
        domain: str,
        action_type: str,
        selector: str,
        error: str,
    ):
        """
        Learn from a failed interaction.
        
        This is called when an action fails, marking the selector as unreliable.
        """
        self.record(
            url=f"https://{domain}",
            domain=domain,
            action_type=action_type,
            selector=selector,
            success=False,
            error=error,
        )
    
    def get_recent_interactions(self, limit: int = 20) -> list[InteractionRecord]:
        """Get recent interactions."""
        return self.records[-limit:]
    
    def clear_domain(self, domain: str):
        """Clear history for a specific domain."""
        self.records = [r for r in self.records if r.domain != domain]
        self._save()
    
    def clear_all(self):
        """Clear all history."""
        self.records = []
        self._save()
    
    def export_domain_schema(self, domain: str, output_dir: Path) -> Optional[Path]:
        """
        Export learned schema for a domain based on interaction history.
        
        Args:
            domain: Domain to export
            output_dir: Output directory
        
        Returns:
            Path to exported schema file
        """
        domain_records = [r for r in self.records if r.domain == domain and r.success]
        
        if not domain_records:
            return None
        
        # Build schema from successful interactions
        actions = []
        
        # Group by action type
        action_groups: dict[str, list[InteractionRecord]] = {}
        for record in domain_records:
            if record.action_type not in action_groups:
                action_groups[record.action_type] = []
            action_groups[record.action_type].append(record)
        
        # Generate actions
        for action_type, records in action_groups.items():
            # Get most common selector
            selector_counts: dict[str, int] = {}
            for r in records:
                if r.selector:
                    selector_counts[r.selector] = selector_counts.get(r.selector, 0) + 1
            
            if selector_counts:
                best_selector = max(selector_counts.items(), key=lambda x: x[1])[0]
                
                action_id = f"{action_type}_{domain.replace('.', '_')}"
                actions.append({
                    "id": action_id,
                    "name": f"{action_type.title()} on {domain}",
                    "description": f"Learned from {len(records)} successful interactions",
                    "parameters": [
                        {"name": "text", "type": "string", "required": action_type == "type"}
                    ] if action_type == "type" else [],
                    "metadata": {
                        "selector": best_selector,
                        "action_type": action_type,
                        "success_count": selector_counts[best_selector],
                        "learned": True,
                    },
                })
        
        # Create schema
        schema = {
            "app_name": domain,
            "app_version": "learned",
            "description": f"Learned schema from {len(domain_records)} interactions",
            "actions": actions,
            "metadata": {
                "learned_from_history": True,
                "total_interactions": len(domain_records),
                "stats": self.get_domain_stats(domain),
            },
        }
        
        # Save
        output_dir.mkdir(parents=True, exist_ok=True)
        import re
        safe_domain = re.sub(r'[^\w\-.]', '_', domain)
        output_file = output_dir / f"{safe_domain}_learned.json"
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(schema, f, indent=2, ensure_ascii=False)
        
        return output_file
