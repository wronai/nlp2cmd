#!/usr/bin/env python3
"""Per-command schema storage system."""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from nlp2cmd.schema_extraction import ExtractedSchema, CommandSchema


class PerCommandSchemaStore:
    """Stores each command schema in its own file."""
    
    def __init__(self, base_dir: str = "./command_schemas"):
        """Initialize the schema store.
        
        Args:
            base_dir: Base directory for storing command schemas
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(exist_ok=True)
        
        # Create subdirectories
        self.commands_dir = self.base_dir / "commands"
        self.categories_dir = self.base_dir / "categories"
        self.index_file = self.base_dir / "index.json"
        
        self.commands_dir.mkdir(exist_ok=True)
        self.categories_dir.mkdir(exist_ok=True)
        
        # Load index
        self.index = self._load_index()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load the command index."""
        if self.index_file.exists():
            try:
                with open(self.index_file) as f:
                    return json.load(f)
            except:
                pass
        
        return {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat(),
            "commands": {},
            "categories": {},
            "stats": {
                "total_commands": 0,
                "total_categories": 0
            }
        }
    
    def _save_index(self):
        """Save the command index."""
        self.index["last_updated"] = datetime.now().isoformat()
        self.index["stats"]["total_commands"] = len(self.index["commands"])
        self.index["stats"]["total_categories"] = len(self.index["categories"])
        
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _get_command_path(self, command: str) -> Path:
        """Get the file path for a command schema."""
        # Sanitize command name
        safe_name = "".join(c for c in command if c.isalnum() or c in ('-', '_')).rstrip()
        return self.commands_dir / f"{safe_name}.json"
    
    def _get_category_path(self, category: str) -> Path:
        """Get the file path for a category index."""
        return self.categories_dir / f"{category}.json"
    
    def store_schema(self, schema: 'ExtractedSchema') -> bool:
        """Store a command schema.
        
        Args:
            schema: The schema to store
            
        Returns:
            True if successful
        """
        try:
            # Late import to avoid circular dependency
            from nlp2cmd.schema_extraction import CommandSchema
            
            if not schema.commands:
                return False
            
            # Store each command in the schema
            for cmd_schema in schema.commands:
                command = cmd_schema.name
                file_path = self._get_command_path(command)
                
                # Prepare schema data
                schema_data = {
                    "command": command,
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
                    "metadata": cmd_schema.metadata,
                    "template": cmd_schema.template,
                    "stored_at": datetime.now().isoformat(),
                    "version": "1.0"
                }
                
                # Save to file
                with open(file_path, 'w') as f:
                    json.dump(schema_data, f, indent=2)
                
                # Update index
                self.index["commands"][command] = {
                    "file": str(file_path.relative_to(self.base_dir)),
                    "category": cmd_schema.category,
                    "source_type": cmd_schema.source_type,
                    "last_updated": datetime.now().isoformat(),
                    "examples_count": len(cmd_schema.examples),
                    "has_template": bool(cmd_schema.template)
                }
                
                # Update category index
                if cmd_schema.category not in self.index["categories"]:
                    self.index["categories"][cmd_schema.category] = []
                if command not in self.index["categories"][cmd_schema.category]:
                    self.index["categories"][cmd_schema.category].append(command)
            
            # Save index
            self._save_index()
            return True
            
        except Exception as e:
            print(f"Failed to store schema: {e}")
            return False
    
    def load_schema(self, command: str) -> Optional['ExtractedSchema']:
        """Load a command schema.
        
        Args:
            command: The command name
            
        Returns:
            The schema if found
        """
        # Late import to avoid circular dependency
        from nlp2cmd.schema_extraction import ExtractedSchema, CommandSchema
        
        file_path = self._get_command_path(command)
        
        if not file_path.exists():
            return None
        
        try:
            with open(file_path) as f:
                data = json.load(f)
            
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
                source=command,
                source_type="file_store",
                commands=[cmd_schema],
                metadata={"stored_at": data.get("stored_at")}
            )
            
        except Exception as e:
            print(f"Failed to load schema for {command}: {e}")
            return None
    
    def list_commands(self, category: Optional[str] = None) -> List[str]:
        """List all commands, optionally filtered by category.
        
        Args:
            category: Filter by category
            
        Returns:
            List of command names
        """
        if category:
            return self.index["categories"].get(category, [])
        return list(self.index["commands"].keys())
    
    def list_categories(self) -> List[str]:
        """List all categories."""
        return list(self.index["categories"].keys())
    
    def get_stats(self) -> Dict[str, Any]:
        """Get storage statistics."""
        stats = self.index["stats"].copy()
        stats["base_dir"] = str(self.base_dir)
        stats["index_file"] = str(self.index_file)
        
        # Category breakdown
        category_stats = {}
        for category, commands in self.index["categories"].items():
            category_stats[category] = {
                "count": len(commands),
                "commands": commands
            }
        stats["categories"] = category_stats
        
        return stats
    
    def delete_schema(self, command: str) -> bool:
        """Delete a command schema.
        
        Args:
            command: The command name
            
        Returns:
            True if deleted
        """
        file_path = self._get_command_path(command)
        
        if file_path.exists():
            file_path.unlink()
            
            # Update index
            if command in self.index["commands"]:
                category = self.index["commands"][command]["category"]
                del self.index["commands"][command]
                
                # Remove from category
                if category in self.index["categories"]:
                    if command in self.index["categories"][category]:
                        self.index["categories"][category].remove(command)
                    
                    # Remove empty category
                    if not self.index["categories"][category]:
                        del self.index["categories"][category]
            
            self._save_index()
            return True
        
        return False
    
    def backup(self, backup_path: str) -> bool:
        """Create a backup of all schemas.
        
        Args:
            backup_path: Path for backup file
            
        Returns:
            True if successful
        """
        try:
            import shutil
            backup_path = Path(backup_path)
            
            if backup_path.suffix == '.zip':
                # Create zip archive
                shutil.make_archive(str(backup_path.with_suffix('')), 'zip', self.base_dir)
            else:
                # Copy directory
                shutil.copytree(self.base_dir, backup_path, dirs_exist_ok=True)
            
            return True
        except Exception as e:
            print(f"Failed to create backup: {e}")
            return False
    
    def restore(self, backup_path: str) -> bool:
        """Restore schemas from backup.
        
        Args:
            backup_path: Path to backup file
            
        Returns:
            True if successful
        """
        try:
            import shutil
            backup_path = Path(backup_path)
            
            # Clear current store
            if self.base_dir.exists():
                shutil.rmtree(self.base_dir)
            self.base_dir.mkdir(exist_ok=True)
            
            if backup_path.suffix == '.zip':
                # Extract from zip
                import zipfile
                with zipfile.ZipFile(backup_path, 'r') as zip_ref:
                    zip_ref.extractall(self.base_dir.parent)
            else:
                # Copy directory
                shutil.copytree(backup_path, self.base_dir, dirs_exist_ok=True)
            
            # Reload index
            self.index = self._load_index()
            return True
            
        except Exception as e:
            print(f"Failed to restore backup: {e}")
            return False


def test_per_command_store():
    """Test the per-command schema store."""
    print("Testing Per-Command Schema Store")
    print("=" * 60)
    
    # Initialize store
    store = PerCommandSchemaStore("./test_command_schemas")
    
    # Create test schema
    from nlp2cmd.schema_extraction import CommandSchema
    
    test_schema = ExtractedSchema(
        source="find",
        source_type="test",
        commands=[
            CommandSchema(
                name="find",
                description="Search for files",
                category="file",
                parameters=[],
                examples=["find . -name '*.py'", "find /home -type f"],
                patterns=["find"],
                source_type="test",
                metadata={},
                template="find {path} -name '{pattern}'"
            )
        ],
        metadata={}
    )
    
    # Store schema
    print("\nStoring schema...")
    success = store.store_schema(test_schema)
    print(f"Success: {success}")
    
    # List commands
    print("\nCommands in store:")
    commands = store.list_commands()
    for cmd in commands:
        print(f"  - {cmd}")
    
    # Load schema
    print("\nLoading schema...")
    loaded = store.load_schema("find")
    if loaded:
        print(f"Loaded: {loaded.commands[0].description}")
    
    # Get stats
    print("\nStore stats:")
    stats = store.get_stats()
    print(f"  Total commands: {stats['total_commands']}")
    print(f"  Categories: {list(stats['categories'].keys())}")
    
    # Test backup
    print("\nTesting backup...")
    backup_success = store.backup("./test_backup.zip")
    print(f"Backup success: {backup_success}")
    
    # Clean up
    import shutil
    if Path("./test_command_schemas").exists():
        shutil.rmtree("./test_command_schemas")
    if Path("./test_backup.zip").exists():
        Path("./test_backup.zip").unlink()


if __name__ == "__main__":
    test_per_command_store()
