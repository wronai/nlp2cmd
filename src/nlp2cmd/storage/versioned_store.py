#!/usr/bin/env python3
"""Version-aware schema storage system for handling multiple command versions."""

import json
import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime

from .per_command_store import PerCommandSchemaStore


class VersionedSchemaStore(PerCommandSchemaStore):
    """Extended schema store that supports versioning."""
    
    def __init__(self, base_dir: str = "./versioned_schemas"):
        """Initialize the versioned schema store."""
        super().__init__(base_dir)
        
        # Create version directories
        self.versions_dir = self.base_dir / "versions"
        self.versions_dir.mkdir(exist_ok=True)
        
        # Track active versions
        self.active_versions = self._load_active_versions()
    
    def _load_active_versions(self) -> Dict[str, str]:
        """Load active versions for commands."""
        active_file = self.base_dir / "active_versions.json"
        if active_file.exists():
            with open(active_file) as f:
                return json.load(f)
        return {}
    
    def _save_active_versions(self):
        """Save active versions."""
        active_file = self.base_dir / "active_versions.json"
        with open(active_file, 'w') as f:
            json.dump(self.active_versions, f, indent=2)
    
    def _get_version_path(self, command: str, version: str) -> Path:
        """Get the file path for a specific version of a command."""
        safe_name = "".join(c for c in command if c.isalnum() or c in ('-', '_')).rstrip()
        return self.versions_dir / safe_name / f"{version}.json"
    
    def store_schema_version(self, schema, version: str, make_active: bool = True) -> bool:
        """Store a specific version of a schema.
        
        Args:
            schema: The schema to store
            version: Version string (e.g., "1.0.0", "2.1.3")
            make_active: Whether to make this the active version
            
        Returns:
            True if successful
        """
        try:
            if not schema.commands:
                return False
            
            # Validate version
            if not self._is_valid_version(version):
                print(f"Invalid version format: {version}")
                return False
            
            # Store each command in the schema
            for cmd_schema in schema.commands:
                command = cmd_schema.name
                version_dir = self.versions_dir / command
                version_dir.mkdir(exist_ok=True)
                
                file_path = self._get_version_path(command, version)
                
                # Prepare schema data with version info
                schema_data = {
                    "command": command,
                    "version": version,
                    "description": cmd_schema.description,
                    "category": cmd_schema.category,
                    "parameters": [
                        {
                            "name": p.name,
                            "type": p.type,
                            "description": p.description,
                            "required": p.required,
                            "default": p.default,
                            "choices": p.choices,
                            "pattern": p.pattern,
                            "location": p.location
                        }
                        for p in cmd_schema.parameters
                    ],
                    "examples": cmd_schema.examples,
                    "patterns": cmd_schema.patterns,
                    "source_type": cmd_schema.source_type,
                    "metadata": {
                        **cmd_schema.metadata,
                        "version": version,
                        "stored_at": datetime.now().isoformat()
                    },
                    "template": cmd_schema.template,
                }
                
                # Save versioned schema
                with open(file_path, 'w') as f:
                    json.dump(schema_data, f, indent=2)
                
                # Update active version if requested
                if make_active:
                    self.active_versions[command] = version
                    # Also update the main schema file
                    super().store_schema(schema)
            
            # Save active versions
            self._save_active_versions()
            return True
            
        except Exception as e:
            print(f"Failed to store schema version: {e}")
            return False
    
    def load_schema_version(self, command: str, version: str = None):
        """Load a specific version of a schema.
        
        Args:
            command: The command name
            version: Version to load (if None, loads active version)
            
        Returns:
            The schema if found
        """
        if version is None:
            version = self.active_versions.get(command)
            if not version:
                # Fallback to non-versioned schema
                return super().load_schema(command)
        
        file_path = self._get_version_path(command, version)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path) as f:
                data = json.load(f)
            
            # Late import to avoid circular dependency
            from nlp2cmd.schema_extraction import ExtractedSchema, CommandSchema
            
            # Reconstruct CommandSchema
            cmd_schema = CommandSchema(
                name=data["command"],
                description=data["description"],
                category=data["category"],
                parameters=[
                    # Reconstruct parameters...
                ],
                examples=data["examples"],
                patterns=data["patterns"],
                source_type=data["source_type"],
                metadata=data["metadata"],
                template=data["template"]
            )
            
            return ExtractedSchema(
                source=f"{command}@{version}",
                source_type="versioned",
                commands=[cmd_schema],
                metadata={"version": version, "stored_at": data.get("stored_at")}
            )
            
        except Exception as e:
            print(f"Failed to load schema version for {command}@{version}: {e}")
            return None
    
    def list_versions(self, command: str) -> List[str]:
        """List all available versions for a command.
        
        Args:
            command: The command name
            
        Returns:
            List of version strings
        """
        version_dir = self.versions_dir / command
        if not version_dir.exists():
            return []
        
        versions = []
        for file in version_dir.glob("*.json"):
            versions.append(file.stem)
        
        # Sort versions using simple version parsing
        try:
            versions.sort(key=lambda v: [int(x) for x in re.findall(r'\d+', v)])
        except:
            versions.sort()
        
        return versions
    
    def get_active_version(self, command: str) -> Optional[str]:
        """Get the active version for a command."""
        return self.active_versions.get(command)
    
    def set_active_version(self, command: str, version: str) -> bool:
        """Set the active version for a command.
        
        Args:
            command: The command name
            version: Version to set as active
            
        Returns:
            True if successful
        """
        version_path = self._get_version_path(command, version)
        if not version_path.exists():
            return False
        
        self.active_versions[command] = version
        self._save_active_versions()
        
        # Update the main schema file
        schema = self.load_schema_version(command, version)
        if schema:
            super().store_schema(schema)
        
        return True
    
    def compare_versions(self, command: str, version1: str, version2: str) -> Dict[str, Any]:
        """Compare two versions of a command schema.
        
        Args:
            command: The command name
            version1: First version
            version2: Second version
            
        Returns:
            Comparison result
        """
        schema1 = self.load_schema_version(command, version1)
        schema2 = self.load_schema_version(command, version2)
        
        if not schema1 or not schema2:
            return {"error": "One or both versions not found"}
        
        cmd1 = schema1.commands[0]
        cmd2 = schema2.commands[0]
        
        comparison = {
            "command": command,
            "versions": [version1, version2],
            "changes": {
                "description": cmd1.description != cmd2.description,
                "template": cmd1.template != cmd2.template,
                "parameters": len(cmd1.parameters) != len(cmd2.parameters),
                "examples": len(cmd1.examples) != len(cmd2.examples)
            }
        }
        
        # Detailed parameter changes
        if cmd1.parameters or cmd2.parameters:
            param_changes = []
            for p1 in cmd1.parameters:
                p2 = next((p for p in cmd2.parameters if p.name == p1.name), None)
                if not p2:
                    param_changes.append(f"Removed parameter: {p1.name}")
                elif p1.required != p2.required:
                    param_changes.append(f"Changed required for {p1.name}: {p1.required} -> {p2.required}")
            
            for p2 in cmd2.parameters:
                p1 = next((p for p in cmd1.parameters if p.name == p2.name), None)
                if not p1:
                    param_changes.append(f"Added parameter: {p2.name}")
            
            comparison["parameter_changes"] = param_changes
        
        return comparison
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version string is valid."""
        # Accept formats like: "1.0.0", "v1.0", "2.1", "1.0.0-beta"
        return bool(re.match(r'^v?\d+(\.\d+)*([a-zA-Z0-9-]*)?$', version))
    
    def get_version_stats(self) -> Dict[str, Any]:
        """Get statistics about versions."""
        stats = {
            "total_commands": len(self.active_versions),
            "versioned_commands": 0,
            "total_versions": 0,
            "versions_per_command": {}
        }
        
        for command in self.active_versions:
            versions = self.list_versions(command)
            if versions:
                stats["versioned_commands"] += 1
                stats["total_versions"] += len(versions)
                stats["versions_per_command"][command] = len(versions)
        
        return stats


def demonstrate_version_management():
    """Demonstrate version management for command schemas."""
    
    print("=" * 60)
    print("Version Management Demo")
    print("=" * 60)
    
    # Initialize versioned store
    store = VersionedSchemaStore("./versioned_schemas_demo")
    
    # Simulate different versions of a command
    from nlp2cmd.schema_extraction import ExtractedSchema, CommandSchema
    
    # Version 1.0 - Basic find command
    find_v1 = ExtractedSchema(
        source="find",
        source_type="test",
        commands=[
            CommandSchema(
                name="find",
                description="Search for files",
                category="file",
                parameters=[],
                examples=["find . -name '*.py'"],
                patterns=["find"],
                source_type="test",
                metadata={},
                template="find {path} -name '{pattern}'"
            )
        ],
        metadata={}
    )
    
    # Version 2.0 - Enhanced find with more options
    find_v2 = ExtractedSchema(
        source="find",
        source_type="test",
        commands=[
            CommandSchema(
                name="find",
                description="Search for files with advanced options",
                category="file",
                parameters=[],
                examples=[
                    "find . -name '*.py'",
                    "find /home -type f -size +100M",
                    "find . -mtime -7 -name '*.log'"
                ],
                patterns=["find"],
                source_type="test",
                metadata={"version": "2.0"},
                template="find {path} -{options} -name '{pattern}'"
            )
        ],
        metadata={}
    )
    
    # Store versions
    print("\nStoring command versions...")
    store.store_schema_version(find_v1, "1.0.0", make_active=True)
    store.store_schema_version(find_v2, "2.0.0", make_active=False)
    
    # List versions
    print("\nAvailable versions for 'find':")
    versions = store.list_versions("find")
    for v in versions:
        active = "(active)" if v == store.get_active_version("find") else ""
        print(f"  - v{v} {active}")
    
    # Load different versions
    print("\nLoading different versions:")
    v1_schema = store.load_schema_version("find", "1.0.0")
    v2_schema = store.load_schema_version("find", "2.0.0")
    
    print(f"\nVersion 1.0:")
    print(f"  Description: {v1_schema.commands[0].description}")
    print(f"  Template: {v1_schema.commands[0].template}")
    print(f"  Examples: {len(v1_schema.commands[0].examples)}")
    
    print(f"\nVersion 2.0:")
    print(f"  Description: {v2_schema.commands[0].description}")
    print(f"  Template: {v2_schema.commands[0].template}")
    print(f"  Examples: {len(v2_schema.commands[0].examples)}")
    
    # Compare versions
    print("\nComparing versions:")
    comparison = store.compare_versions("find", "1.0.0", "2.0.0")
    print(f"  Description changed: {comparison['changes']['description']}")
    print(f"  Template changed: {comparison['changes']['template']}")
    print(f"  Examples changed: {comparison['changes']['examples']}")
    
    # Switch active version
    print("\nSwitching active version to 2.0.0...")
    store.set_active_version("find", "2.0.0")
    print(f"Active version: {store.get_active_version('find')}")
    
    # Load active version (default)
    print("\nLoading active version (no version specified):")
    active_schema = store.load_schema_version("find")
    print(f"  Loaded version: {active_schema.metadata.get('version')}")
    
    # Stats
    print("\nVersion statistics:")
    stats = store.get_version_stats()
    print(f"  Total commands: {stats['total_commands']}")
    print(f"  Commands with versions: {stats['versioned_commands']}")
    print(f"  Total versions stored: {stats['total_versions']}")
    
    # Clean up
    import shutil
    if Path("./versioned_schemas_demo").exists():
        shutil.rmtree("./versioned_schemas_demo")
    
    print("\n✅ Version management demo completed!")


if __name__ == "__main__":
    demonstrate_version_management()
