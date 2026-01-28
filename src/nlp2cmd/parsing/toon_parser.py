"""
TOON Parser - Token-Oriented Object Notation Parser
Handles parsing and access to unified TOON format with depth hierarchy
"""

import re
from typing import Dict, List, Any, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum


class ToonNodeType(Enum):
    """TOON node types"""
    OBJECT = "object"
    ARRAY = "array"
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    NULL = "null"


@dataclass
class ToonNode:
    """TOON node structure"""
    type: ToonNodeType
    value: Any
    children: Optional[Dict[str, 'ToonNode']] = None
    parent: Optional['ToonNode'] = None
    name: Optional[str] = None


class ToonParser:
    """Unified TOON format parser with hierarchical access"""
    
    def __init__(self, file_path: Optional[Union[str, Path]] = None):
        self.file_path = Path(file_path) if file_path else None
        self.root: Optional[ToonNode] = None
        self.categories: Dict[str, ToonNode] = {}
        
    def parse_file(self, file_path: Union[str, Path]) -> ToonNode:
        """Parse TOON file and return root node"""
        self.file_path = Path(file_path)
        with open(self.file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        return self.parse_content(content)
    
    def parse_content(self, content: str) -> ToonNode:
        """Parse TOON content string"""
        lines = content.strip().split('\n')
        self.root = self._parse_lines(lines)
        self._extract_categories()
        return self.root
    
    def _parse_lines(self, lines: List[str]) -> ToonNode:
        """Parse TOON lines with depth hierarchy"""
        root = ToonNode(ToonNodeType.OBJECT, {}, {})
        stack = [(root, -1)]
        current_section = None
        
        for line_num, line in enumerate(lines):
            raw_line = line
            stripped = raw_line.strip()
            if not stripped or stripped.startswith('#'):
                continue
                
            # Calculate depth
            depth = len(raw_line) - len(raw_line.lstrip())
            line = stripped

            # Handle closing brackets/braces
            if line in {']', '}'}:
                if len(stack) > 1:
                    stack.pop()
                continue
            
            # Handle sections
            if line.startswith('===') and line.endswith('==='):
                section_name = line.strip('=').strip().lower()
                current_section = section_name
                section_node = ToonNode(ToonNodeType.OBJECT, {}, {})
                root.children[section_name] = section_node
                stack.append((section_node, depth))
                continue

            # Multi-line container starts (top-level and nested)
            array_start = re.match(r'^(\w+)\[$', line)
            if array_start:
                name = array_start.group(1)
                node = ToonNode(ToonNodeType.ARRAY, [], {}, name=name)
                while stack and stack[-1][1] >= depth:
                    stack.pop()
                parent, _ = stack[-1]
                parent.children[name] = node
                node.parent = parent
                stack.append((node, depth))
                continue

            object_start = re.match(r'^(\w+)\{$', line)
            if object_start:
                name = object_start.group(1)
                node = ToonNode(ToonNodeType.OBJECT, {}, {}, name=name)
                while stack and stack[-1][1] >= depth:
                    stack.pop()
                parent, _ = stack[-1]
                parent.children[name] = node
                node.parent = parent
                stack.append((node, depth))
                continue

            kv_array_start = re.match(r'^(\w+)\s*:\s*\[$', line)
            if kv_array_start:
                name = kv_array_start.group(1)
                node = ToonNode(ToonNodeType.ARRAY, [], {}, name=name)
                while stack and stack[-1][1] >= depth:
                    stack.pop()
                parent, _ = stack[-1]
                parent.children[name] = node
                node.parent = parent
                stack.append((node, depth))
                continue

            kv_object_start = re.match(r'^(\w+)\s*:\s*\{$', line)
            if kv_object_start:
                name = kv_object_start.group(1)
                node = ToonNode(ToonNodeType.OBJECT, {}, {}, name=name)
                while stack and stack[-1][1] >= depth:
                    stack.pop()
                parent, _ = stack[-1]
                parent.children[name] = node
                node.parent = parent
                stack.append((node, depth))
                continue
            
            # Parse based on current context
            # NOTE: use regex-based container detection to avoid treating braces in string values
            # (e.g. templates like "{command} {options}") as object declarations.
            if re.match(r'^(\w+)\[.*\]$', line):
                # Array notation (single-line)
                node = self._parse_array_node(line, current_section)
            elif re.match(r'^(\w+)\{.*\}$', line):
                # Object notation (single-line)
                node = self._parse_object_node(line, current_section)
            elif ':' in line:
                # Key-value pair
                node = self._parse_key_value(line, current_section)
            else:
                # Bare values inside array containers
                parent, _ = stack[-1]
                if parent.type == ToonNodeType.ARRAY:
                    parent.value.append(self._parse_value(line))
                continue
            
            # Find parent at appropriate depth
            while stack and stack[-1][1] >= depth:
                stack.pop()
            
            if stack:
                parent, _ = stack[-1]
                if node.name:
                    parent.children[node.name] = node
                    node.parent = parent
                stack.append((node, depth))
        
        return root
    
    def _parse_array_node(self, line: str, section: str) -> ToonNode:
        """Parse array node notation: name[..."""
        match = re.match(r'(\w+)\[(.*)\]', line)
        if match:
            name, content = match.groups()
            return ToonNode(ToonNodeType.ARRAY, [], {}, name=name)
        return ToonNode(ToonNodeType.ARRAY, [], {})
    
    def _parse_object_node(self, line: str, section: str) -> ToonNode:
        """Parse object node notation: name{..."""
        match = re.match(r'(\w+)\{(.*)\}', line)
        if match:
            name, content = match.groups()
            return ToonNode(ToonNodeType.OBJECT, {}, {}, name=name)
        return ToonNode(ToonNodeType.OBJECT, {}, {})
    
    def _parse_key_value(self, line: str, section: str) -> ToonNode:
        """Parse key-value pair: key: value"""
        if ':' in line:
            key, value = line.split(':', 1)
            key = key.strip()
            value = value.strip()
            
            # Determine value type
            if value.startswith('[') and value.endswith(']'):
                # Array value
                array_content = value[1:-1].strip()
                if array_content:
                    items = [item.strip() for item in array_content.split(',')]
                    parsed_items = []
                    for item in items:
                        parsed_items.append(self._parse_value(item))
                    return ToonNode(ToonNodeType.ARRAY, parsed_items, {}, name=key)
                else:
                    return ToonNode(ToonNodeType.ARRAY, [], {}, name=key)
            elif value.startswith('{') and value.endswith('}'):
                # Object value
                return ToonNode(ToonNodeType.OBJECT, {}, {}, name=key)
            elif value.lower() in ['true', 'false']:
                # Boolean value
                return ToonNode(ToonNodeType.BOOLEAN, value.lower() == 'true', {}, name=key)
            elif value.isdigit() or re.match(r'^\d+\.\d+$', value):
                # Number value
                num_value = float(value) if '.' in value else int(value)
                return ToonNode(ToonNodeType.NUMBER, num_value, {}, name=key)
            else:
                # String value
                if value.startswith('"') and value.endswith('"'):
                    value = value[1:-1]
                return ToonNode(ToonNodeType.STRING, value, {}, name=key)
        
        return ToonNode(ToonNodeType.STRING, "", {})
    
    def _parse_value(self, value: str) -> Any:
        """Parse individual value"""
        value = value.strip()
        if value.startswith('"') and value.endswith('"'):
            return value[1:-1]
        elif value.lower() == 'true':
            return True
        elif value.lower() == 'false':
            return False
        elif value.isdigit():
            return int(value)
        elif re.match(r'^\d+\.\d+$', value):
            return float(value)
        else:
            return value
    
    def _extract_categories(self):
        """Extract main categories from root"""
        if self.root and self.root.children:
            self.categories = self.root.children
    
    def get_category(self, category_name: str) -> Optional[ToonNode]:
        """Get category node by name"""
        return self.categories.get(category_name)
    
    def get_commands(self, category: str = None) -> Dict[str, Any]:
        """Get commands from specific category or all commands"""
        commands_node = self.get_category('commands')
        if not commands_node:
            return {}
        
        if category:
            category_node = commands_node.children.get(category)
            if category_node:
                return self._node_to_dict(category_node)
            return {}
        else:
            return self._node_to_dict(commands_node)
    
    def get_config(self, key: str = None) -> Any:
        """Get configuration value or entire config"""
        config_node = self.get_category('config')
        if not config_node:
            return {} if not key else None
        
        if key:
            return self._get_nested_value(config_node, key)
        else:
            return self._node_to_dict(config_node)
    
    def get_schemas(self, schema_type: str = None) -> Dict[str, Any]:
        """Get schema definitions"""
        schemas_node = self.get_category('schema')
        if not schemas_node:
            return {}
        
        if schema_type:
            schema_node = schemas_node.children.get(schema_type)
            if schema_node:
                return self._node_to_dict(schema_node)
            return {}
        else:
            return self._node_to_dict(schemas_node)
    
    def get_templates(self, template_type: str = None) -> Dict[str, Any]:
        """Get templates"""
        templates_node = self.get_category('templates')
        if not templates_node:
            return {}
        
        if template_type:
            template_node = templates_node.children.get(template_type)
            if template_node:
                return self._node_to_dict(template_node)
            return {}
        else:
            return self._node_to_dict(templates_node)
    
    def get_mappings(self, mapping_type: str = None) -> Dict[str, Any]:
        """Get mappings"""
        mappings_node = self.get_category('mappings')
        if not mappings_node:
            return {}
        
        if mapping_type:
            mapping_node = mappings_node.children.get(mapping_type)
            if mapping_node:
                return self._node_to_dict(mapping_node)
            return {}
        else:
            return self._node_to_dict(mappings_node)
    
    def get_metadata(self, key: str = None) -> Any:
        """Get project metadata"""
        metadata_node = self.get_category('metadata')
        if not metadata_node:
            return {} if not key else None
        
        if key:
            return self._get_nested_value(metadata_node, key)
        else:
            return self._node_to_dict(metadata_node)
    
    def _get_nested_value(self, node: ToonNode, key_path: str) -> Any:
        """Get nested value using dot notation"""
        keys = key_path.split('.')
        current = node
        
        for key in keys:
            if current.children and key in current.children:
                current = current.children[key]
            else:
                return None
        
        if current.type == ToonNodeType.OBJECT:
            return self._node_to_dict(current)
        if current.type == ToonNodeType.ARRAY and current.children:
            return self._node_to_dict(current)
        return current.value
    
    def _node_to_dict(self, node: ToonNode) -> Dict[str, Any]:
        """Convert TOON node to dictionary"""
        if node.type == ToonNodeType.OBJECT and node.children:
            result = {}
            for key, child in node.children.items():
                if child.type == ToonNodeType.OBJECT and child.children:
                    result[key] = self._node_to_dict(child)
                elif child.type == ToonNodeType.ARRAY:
                    result[key] = self._node_to_dict(child) if child.children else child.value
                else:
                    result[key] = child.value
            return result
        elif node.type == ToonNodeType.ARRAY:
            if node.children:
                result = {}
                for key, child in node.children.items():
                    if child.type == ToonNodeType.OBJECT and child.children:
                        result[key] = self._node_to_dict(child)
                    elif child.type == ToonNodeType.ARRAY:
                        result[key] = self._node_to_dict(child) if child.children else child.value
                    else:
                        result[key] = child.value
                if node.value:
                    result["_items"] = node.value
                return result
            return node.value
        else:
            return node.value
    
    def search_commands(self, query: str, category: str = None) -> List[Dict[str, Any]]:
        """Search commands by query"""
        commands = self.get_commands(category)
        results = []
        
        def search_recursive(obj, path=""):
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_path = f"{path}.{key}" if path else key
                    if isinstance(value, dict):
                        search_recursive(value, new_path)
                    elif isinstance(value, str) and query.lower() in value.lower():
                        results.append({"path": new_path, "value": value})
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    if isinstance(item, str) and query.lower() in item.lower():
                        results.append({"path": f"{path}[{i}]", "value": item})
        
        search_recursive(commands)
        return results
    
    def validate_schema(self, data: Dict[str, Any], schema_name: str) -> bool:
        """Validate data against schema"""
        schema = self.get_schemas(schema_name)
        if not schema:
            return False
        
        # Basic validation - can be extended
        required_properties = schema.get('properties', {}).keys()
        return all(prop in data for prop in required_properties)


# Global parser instance
_parser_instance = None

def get_parser(file_path: Optional[str] = None) -> ToonParser:
    """Get or create parser instance"""
    global _parser_instance
    if _parser_instance is None or file_path:
        _parser_instance = ToonParser(file_path or "project.unified.toon")
        if Path(_parser_instance.file_path).exists():
            _parser_instance.parse_file(_parser_instance.file_path)
    return _parser_instance

def reload_parser(file_path: Optional[str] = None) -> ToonParser:
    """Reload parser with new file"""
    global _parser_instance
    _parser_instance = ToonParser(file_path or "project.unified.toon")
    _parser_instance.parse_file(_parser_instance.file_path)
    return _parser_instance
