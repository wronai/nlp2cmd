"""
Virtual Objects Module

Virtual objects created based on semantics for script execution.
Provides object-oriented representation of system resources.
"""

from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum
import json


class ObjectType(Enum):
    """Types of virtual objects."""
    FILE = "file"
    DIRECTORY = "directory"
    USER = "user"
    PROCESS = "process"
    SERVICE = "service"
    CONTAINER = "container"
    NETWORK = "network"
    CONFIG = "config"
    TOOL = "tool"
    ENVIRONMENT = "environment"


@dataclass
class VirtualObject:
    """Virtual object representing system resource."""
    
    id: str
    type: ObjectType
    name: str
    path: Optional[Path] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    relationships: Dict[str, List[str]] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Initialize virtual object properties."""
        self._set_default_properties()
    
    def _set_default_properties(self):
        """Set default properties based on object type."""
        if self.type == ObjectType.FILE:
            self.properties.update({
                'exists': False,
                'size': 0,
                'extension': '',
                'content_type': '',
                'permissions': '',
                'created': None,
                'modified': None
            })
        elif self.type == ObjectType.DIRECTORY:
            self.properties.update({
                'exists': False,
                'size': 0,
                'file_count': 0,
                'subdirectory_count': 0,
                'permissions': '',
                'created': None,
                'modified': None
            })
        elif self.type == ObjectType.USER:
            self.properties.update({
                'home_directory': '',
                'shell': '',
                'uid': 0,
                'gid': 0,
                'groups': [],
                'is_current_user': False
            })
        elif self.type == ObjectType.PROCESS:
            self.properties.update({
                'pid': 0,
                'status': '',
                'cpu_usage': 0.0,
                'memory_usage': 0.0,
                'command': '',
                'start_time': None
            })
    
    def add_relationship(self, relation_type: str, target_id: str):
        """Add relationship to another object."""
        if relation_type not in self.relationships:
            self.relationships[relation_type] = []
        if target_id not in self.relationships[relation_type]:
            self.relationships[relation_type].append(target_id)
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """Get property value."""
        return self.properties.get(key, default)
    
    def set_property(self, key: str, value: Any):
        """Set property value."""
        self.properties[key] = value
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert virtual object to dictionary."""
        return {
            'id': self.id,
            'type': self.type.value,
            'name': self.name,
            'path': str(self.path) if self.path else None,
            'properties': self.properties,
            'relationships': self.relationships,
            'metadata': self.metadata
        }


class VirtualObjectManager:
    """Manager for virtual objects."""
    
    def __init__(self):
        self.objects: Dict[str, VirtualObject] = {}
        self.type_index: Dict[ObjectType, List[str]] = {}
        self.name_index: Dict[str, str] = {}
    
    def create_object(self, 
                      obj_id: str,
                      obj_type: ObjectType,
                      name: str,
                      path: Optional[Path] = None,
                      properties: Optional[Dict[str, Any]] = None,
                      metadata: Optional[Dict[str, Any]] = None) -> VirtualObject:
        """Create new virtual object."""
        obj = VirtualObject(
            id=obj_id,
            type=obj_type,
            name=name,
            path=path,
            properties=properties or {},
            metadata=metadata or {}
        )
        
        self.objects[obj_id] = obj
        
        # Update indexes
        if obj_type not in self.type_index:
            self.type_index[obj_type] = []
        self.type_index[obj_type].append(obj_id)
        
        self.name_index[name] = obj_id
        
        return obj
    
    def get_object(self, obj_id: str) -> Optional[VirtualObject]:
        """Get virtual object by ID."""
        return self.objects.get(obj_id)
    
    def get_object_by_name(self, name: str) -> Optional[VirtualObject]:
        """Get virtual object by name."""
        obj_id = self.name_index.get(name)
        return self.objects.get(obj_id) if obj_id else None
    
    def get_objects_by_type(self, obj_type: ObjectType) -> List[VirtualObject]:
        """Get all objects of specific type."""
        obj_ids = self.type_index.get(obj_type, [])
        return [self.objects[obj_id] for obj_id in obj_ids]
    
    def find_objects(self, 
                    obj_type: Optional[ObjectType] = None,
                    name_pattern: Optional[str] = None,
                    properties_filter: Optional[Dict[str, Any]] = None) -> List[VirtualObject]:
        """Find objects matching criteria."""
        results = []
        
        for obj in self.objects.values():
            # Filter by type
            if obj_type and obj.type != obj_type:
                continue
            
            # Filter by name pattern
            if name_pattern and name_pattern not in obj.name:
                continue
            
            # Filter by properties
            if properties_filter:
                match = True
                for key, value in properties_filter.items():
                    if obj.get_property(key) != value:
                        match = False
                        break
                if not match:
                    continue
            
            results.append(obj)
        
        return results
    
    def create_user_object(self, username: str, is_current: bool = False) -> VirtualObject:
        """Create user virtual object."""
        import os
        from pathlib import Path
        
        user_id = f"user_{username}"
        
        # Get user information
        home_dir = os.path.expanduser(f"~{username}" if not is_current else "~")
        shell = os.environ.get('SHELL', '')
        
        properties = {
            'home_directory': home_dir,
            'shell': shell,
            'is_current_user': is_current
        }
        
        metadata = {
            'created_by': 'system',
            'source': 'environment'
        }
        
        return self.create_object(
            obj_id=user_id,
            obj_type=ObjectType.USER,
            name=username,
            path=Path(home_dir),
            properties=properties,
            metadata=metadata
        )
    
    def create_file_object(self, file_path: Union[str, Path], name: Optional[str] = None) -> VirtualObject:
        """Create file virtual object."""
        file_path = Path(file_path)
        file_name = name or file_path.name
        file_id = f"file_{file_name}_{hash(str(file_path))}"
        
        properties = {
            'exists': file_path.exists(),
            'size': file_path.stat().st_size if file_path.exists() else 0,
            'extension': file_path.suffix,
            'is_absolute': file_path.is_absolute()
        }
        
        if file_path.exists():
            stat = file_path.stat()
            properties.update({
                'permissions': oct(stat.st_mode)[-3:],
                'created': stat.st_ctime,
                'modified': stat.st_mtime
            })
        
        metadata = {
            'created_by': 'system',
            'source': 'filesystem'
        }
        
        return self.create_object(
            obj_id=file_id,
            obj_type=ObjectType.FILE,
            name=file_name,
            path=file_path,
            properties=properties,
            metadata=metadata
        )
    
    def create_directory_object(self, dir_path: Union[str, Path], name: Optional[str] = None) -> VirtualObject:
        """Create directory virtual object."""
        dir_path = Path(dir_path)
        dir_name = name or dir_path.name
        dir_id = f"dir_{dir_name}_{hash(str(dir_path))}"
        
        properties = {
            'exists': dir_path.exists(),
            'is_absolute': dir_path.is_absolute()
        }
        
        if dir_path.exists() and dir_path.is_dir():
            properties.update({
                'file_count': len([f for f in dir_path.iterdir() if f.is_file()]),
                'subdirectory_count': len([d for d in dir_path.iterdir() if d.is_dir()])
            })
            
            stat = dir_path.stat()
            properties.update({
                'permissions': oct(stat.st_mode)[-3:],
                'created': stat.st_ctime,
                'modified': stat.st_mtime
            })
        
        metadata = {
            'created_by': 'system',
            'source': 'filesystem'
        }
        
        return self.create_object(
            obj_id=dir_id,
            obj_type=ObjectType.DIRECTORY,
            name=dir_name,
            path=dir_path,
            properties=properties,
            metadata=metadata
        )
    
    def establish_relationship(self, source_id: str, relation_type: str, target_id: str):
        """Establish relationship between objects."""
        source_obj = self.get_object(source_id)
        if source_obj:
            source_obj.add_relationship(relation_type, target_id)
    
    def get_related_objects(self, obj_id: str, relation_type: str) -> List[VirtualObject]:
        """Get objects related to given object."""
        obj = self.get_object(obj_id)
        if not obj:
            return []
        
        related_ids = obj.relationships.get(relation_type, [])
        return [self.objects[rel_id] for rel_id in related_ids if rel_id in self.objects]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert manager state to dictionary."""
        return {
            'objects': {obj_id: obj.to_dict() for obj_id, obj in self.objects.items()},
            'type_index': {t.value: ids for t, ids in self.type_index.items()},
            'name_index': self.name_index
        }
    
    def save_to_file(self, file_path: Union[str, Path]):
        """Save manager state to file."""
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, default=str)
    
    def load_from_file(self, file_path: Union[str, Path]):
        """Load manager state from file."""
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        # Clear current state
        self.objects.clear()
        self.type_index.clear()
        self.name_index.clear()
        
        # Load objects
        for obj_id, obj_data in data['objects'].items():
            obj = VirtualObject(
                id=obj_data['id'],
                type=ObjectType(obj_data['type']),
                name=obj_data['name'],
                path=Path(obj_data['path']) if obj_data['path'] else None,
                properties=obj_data['properties'],
                relationships=obj_data['relationships'],
                metadata=obj_data['metadata']
            )
            self.objects[obj_id] = obj
        
        # Rebuild indexes
        self.type_index = {ObjectType(t): ids for t, ids in data['type_index'].items()}
        self.name_index = data['name_index']
