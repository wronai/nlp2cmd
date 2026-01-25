"""
TOON Integration - Core integration layer for unified TOON format
Provides unified access to all project data through TOON parser
"""

from typing import Dict, List, Any, Optional, Union
from pathlib import Path
import logging

from ..parsing.toon_parser import get_parser, ToonParser

logger = logging.getLogger(__name__)


class ToonDataManager:
    """Unified data manager using TOON format"""
    
    def __init__(self, toon_file: Optional[str] = None):
        self.parser = get_parser(toon_file)
        self._ensure_loaded()
    
    def _ensure_loaded(self):
        """Ensure TOON data is loaded"""
        if not self.parser.root:
            default_path = Path("project.unified.toon")
            if default_path.exists():
                self.parser.parse_file(default_path)
            else:
                logger.warning(f"TOON file not found: {default_path}")
    
    # Command Management
    def get_all_commands(self) -> Dict[str, Any]:
        """Get all commands from all categories"""
        return self.parser.get_commands()
    
    def get_shell_commands(self) -> Dict[str, Any]:
        """Get shell commands"""
        return self.parser.get_commands('shell')
    
    def get_browser_commands(self) -> Dict[str, Any]:
        """Get browser commands"""
        return self.parser.get_commands('browser')
    
    def get_command_by_name(self, command_name: str, category: str = None) -> Optional[Dict[str, Any]]:
        """Get specific command by name"""
        commands = self.parser.get_commands(category)
        
        def search_recursive(obj, target):
            if isinstance(obj, dict):
                if target in obj:
                    return obj[target]
                for value in obj.values():
                    result = search_recursive(value, target)
                    if result:
                        return result
            return None
        
        return search_recursive(commands, command_name)
    
    def search_commands(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search commands by query"""
        return self.parser.search_commands(query, category)
    
    # Configuration Management
    def get_config(self, key: str = None) -> Any:
        """Get configuration"""
        return self.parser.get_config(key)
    
    def get_llm_config(self) -> Dict[str, Any]:
        """Get LLM configuration"""
        return self.parser.get_config('schema_generation.llm')
    
    def get_test_commands(self) -> List[str]:
        """Get test commands list"""
        config = self.parser.get_config('test_commands')
        return config if isinstance(config, list) else []
    
    # Schema Management
    def get_command_schema(self) -> Dict[str, Any]:
        """Get command schema definition"""
        return self.parser.get_schemas('command_schema')
    
    def get_browser_schema(self) -> Dict[str, Any]:
        """Get browser schema definition"""
        return self.parser.get_schemas('browser_schema')
    
    def validate_command_data(self, data: Dict[str, Any]) -> bool:
        """Validate command data against schema"""
        return self.parser.validate_schema(data, 'command_schema')
    
    # Template Management
    def get_command_templates(self) -> Dict[str, str]:
        """Get command generation templates"""
        return self.parser.get_templates('command_generation')
    
    def get_browser_templates(self) -> Dict[str, str]:
        """Get browser action templates"""
        return self.parser.get_templates('browser_actions')
    
    def get_error_templates(self) -> Dict[str, str]:
        """Get error handling templates"""
        return self.parser.get_templates('error_handling')
    
    # Mapping Management
    def get_category_mappings(self) -> Dict[str, str]:
        """Get category to type mappings"""
        return self.parser.get_mappings('category_to_type')
    
    def get_language_patterns(self, language: str = None) -> Dict[str, Any]:
        """Get language patterns"""
        patterns = self.parser.get_mappings('language_patterns')
        if language:
            return patterns.get(language, {})
        return patterns
    
    def get_command_aliases(self) -> Dict[str, str]:
        """Get command aliases"""
        return self.parser.get_mappings('command_aliases')
    
    # Metadata Management
    def get_project_metadata(self) -> Dict[str, Any]:
        """Get project metadata"""
        return self.parser.get_metadata()
    
    def get_project_version(self) -> str:
        """Get project version"""
        return self.parser.get_metadata('version') or "unknown"
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get project statistics"""
        return self.parser.get_metadata('statistics')
    
    # Utility Methods
    def reload_data(self, toon_file: Optional[str] = None) -> bool:
        """Reload TOON data from file"""
        try:
            from ..parsing.toon_parser import reload_parser
            self.parser = reload_parser(toon_file)
            return True
        except Exception as e:
            logger.error(f"Failed to reload TOON data: {e}")
            return False
    
    def export_category(self, category: str, format: str = 'dict') -> Union[Dict, str]:
        """Export category data in specified format"""
        data = None
        
        if category == 'commands':
            data = self.get_all_commands()
        elif category == 'config':
            data = self.parser.get_config()
        elif category == 'schema':
            data = self.parser.get_schemas()
        elif category == 'templates':
            data = self.parser.get_templates()
        elif category == 'mappings':
            data = self.parser.get_mappings()
        elif category == 'metadata':
            data = self.get_project_metadata()
        
        if format == 'json':
            import json
            return json.dumps(data, indent=2, ensure_ascii=False)
        elif format == 'yaml':
            import yaml
            return yaml.dump(data, default_flow_style=False, allow_unicode=True)
        else:
            return data
    
    def get_command_examples(self, command_name: str) -> List[str]:
        """Get examples for a specific command"""
        command = self.get_command_by_name(command_name)
        if command and 'examples' in command:
            return command['examples']
        return []
    
    def get_command_patterns(self, command_name: str) -> List[str]:
        """Get patterns for a specific command"""
        command = self.get_command_by_name(command_name)
        if command and 'patterns' in command:
            return command['patterns']
        return []
    
    def get_command_template(self, command_name: str) -> Optional[str]:
        """Get template for a specific command"""
        command = self.get_command_by_name(command_name)
        if command and 'template' in command:
            return command['template']
        return None


# Global data manager instance
_data_manager = None

def get_data_manager(toon_file: Optional[str] = None) -> ToonDataManager:
    """Get or create data manager instance"""
    global _data_manager
    if _data_manager is None or toon_file:
        _data_manager = ToonDataManager(toon_file)
    return _data_manager

def reload_data_manager(toon_file: Optional[str] = None) -> ToonDataManager:
    """Reload data manager with new file"""
    global _data_manager
    _data_manager = ToonDataManager(toon_file)
    return _data_manager


# Backward compatibility functions for existing code
def load_command_schemas() -> Dict[str, Any]:
    """Load command schemas (backward compatibility)"""
    manager = get_data_manager()
    return manager.get_all_commands()

def load_config() -> Dict[str, Any]:
    """Load configuration (backward compatibility)"""
    manager = get_data_manager()
    return manager.parser.get_config()

def get_project_info() -> Dict[str, Any]:
    """Get project information (backward compatibility)"""
    manager = get_data_manager()
    return manager.get_project_metadata()
