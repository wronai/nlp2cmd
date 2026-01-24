"""
Semantic Objects Module

Virtual objects created based on semantic analysis.
Provides intelligent object creation from natural language.
"""

import re
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass

from .virtual_objects import VirtualObject, ObjectType, VirtualObjectManager
from ..generation.enhanced_context import get_enhanced_detector


@dataclass
class SemanticPattern:
    """Pattern for semantic object creation."""
    
    pattern: str
    object_type: ObjectType
    property_mappings: Dict[str, str]
    confidence_threshold: float = 0.7


class SemanticObjectFactory:
    """Factory for creating virtual objects from semantic analysis."""
    
    def __init__(self):
        self.patterns = self._initialize_patterns()
        self.enhanced_detector = get_enhanced_detector()
        self.object_manager = VirtualObjectManager()
    
    def _initialize_patterns(self) -> List[SemanticPattern]:
        """Initialize semantic patterns for object creation."""
        patterns = [
            # User-related patterns
            SemanticPattern(
                pattern=r"(?:użytkownik|user|użytkownika|usera|userów|użytkowników)\s+(.+)",
                object_type=ObjectType.USER,
                property_mappings={'username': 'group(1)'}
            ),
            SemanticPattern(
                pattern=r"(?:current|aktualny|bieżący)\s+(?:użytkownik|user)",
                object_type=ObjectType.USER,
                property_mappings={'is_current_user': True}
            ),
            
            # File-related patterns
            SemanticPattern(
                pattern=r"(?:plik|file|pliki|files)\s+(?:użytkownika|usera|user)",
                object_type=ObjectType.FILE,
                property_mappings={'user_context': True}
            ),
            SemanticPattern(
                pattern=r"(?:plik|file)\s+(.+)",
                object_type=ObjectType.FILE,
                property_mappings={'filename': 'group(1)'}
            ),
            SemanticPattern(
                pattern=r"(?:pliki|files)\s+(?:w|in)\s+(.+)",
                object_type=ObjectType.FILE,
                property_mappings={'location': 'group(1)'}
            ),
            
            # Directory-related patterns
            SemanticPattern(
                pattern=r"(?:folder|directory|katalog|katalogu|folderze)\s+(?:użytkownika|usera|user)",
                object_type=ObjectType.DIRECTORY,
                property_mappings={'user_context': True}
            ),
            SemanticPattern(
                pattern=r"(?:folder|directory|katalog)\s+(.+)",
                object_type=ObjectType.DIRECTORY,
                property_mappings={'dirname': 'group(1)'}
            ),
            
            # Process-related patterns
            SemanticPattern(
                pattern=r"(?:proces|process|procesy|processes)\s+(?:użytkownika|usera|user)",
                object_type=ObjectType.PROCESS,
                property_mappings={'user_context': True}
            ),
        ]
        
        return patterns
    
    def create_objects_from_query(self, query: str) -> List[VirtualObject]:
        """Create virtual objects from natural language query."""
        objects = []
        
        # Get semantic analysis
        match = self.enhanced_detector.get_best_match(query)
        if not match:
            return objects
        
        # Extract entities from enhanced context
        entities = match.entities
        
        # Create objects based on semantic patterns
        for pattern in self.patterns:
            pattern_match = re.search(pattern.pattern, query, re.IGNORECASE)
            if pattern_match:
                obj = self._create_object_from_pattern(pattern, pattern_match, entities, query)
                if obj:
                    objects.append(obj)
        
        # Create objects based on enhanced context entities
        context_objects = self._create_objects_from_entities(entities, query)
        objects.extend(context_objects)
        
        # Establish relationships between objects
        self._establish_relationships(objects, entities)
        
        return objects
    
    def _create_object_from_pattern(self, 
                                   pattern: SemanticPattern,
                                   match: re.Match,
                                   entities: Dict[str, Any],
                                   query: str) -> Optional[VirtualObject]:
        """Create object from semantic pattern match."""
        try:
            # Generate object ID
            obj_id = f"{pattern.object_type.value}_{hash(query)}"
            
            # Extract properties from pattern match
            properties = {}
            for prop_key, mapping in pattern.property_mappings.items():
                if mapping.startswith('group('):
                    group_num = int(mapping.strip('group()'))
                    properties[prop_key] = match.group(group_num)
                else:
                    properties[prop_key] = mapping
            
            # Add semantic context
            properties['semantic_confidence'] = match.end() / len(query)
            properties['source_pattern'] = pattern.pattern
            
            # Determine object name and path
            name, path = self._extract_name_and_path(pattern.object_type, properties, entities)
            
            # Create virtual object
            obj = self.object_manager.create_object(
                obj_id=obj_id,
                obj_type=pattern.object_type,
                name=name,
                path=path,
                properties=properties,
                metadata={'source': 'semantic_pattern', 'query': query}
            )
            
            return obj
            
        except Exception as e:
            print(f"Error creating object from pattern: {e}")
            return None
    
    def _create_objects_from_entities(self, entities: Dict[str, Any], query: str) -> List[VirtualObject]:
        """Create objects from enhanced context entities."""
        objects = []
        
        # Create user object if user entity is present
        if 'user' in entities:
            user_obj = self._create_user_object(entities, query)
            if user_obj:
                objects.append(user_obj)
        
        # Create file objects if file-related entities are present
        if any(keyword in query.lower() for keyword in ['plik', 'file', 'pliki', 'files']):
            file_objs = self._create_file_objects(entities, query)
            objects.extend(file_objs)
        
        # Create directory objects if directory-related entities are present
        if any(keyword in query.lower() for keyword in ['folder', 'directory', 'katalog']):
            dir_objs = self._create_directory_objects(entities, query)
            objects.extend(dir_objs)
        
        return objects
    
    def _create_user_object(self, entities: Dict[str, Any], query: str) -> Optional[VirtualObject]:
        """Create user object from entities."""
        user_value = entities.get('user', '')
        
        if user_value == 'current':
            # Create current user object
            import os
            username = os.environ.get('USER', os.environ.get('USERNAME', 'user'))
            return self.object_manager.create_user_object(username, is_current=True)
        else:
            # Create specific user object
            return self.object_manager.create_user_object(user_value, is_current=False)
    
    def _create_file_objects(self, entities: Dict[str, Any], query: str) -> List[VirtualObject]:
        """Create file objects from entities."""
        objects = []
        
        # Determine file location based on context
        if 'user' in entities:
            # User files - use home directory
            import os
            home_dir = Path(os.path.expanduser('~'))
            file_path = home_dir / '*'
            
            file_obj = self.object_manager.create_file_object(file_path, 'user_files')
            file_obj.set_property('user_context', True)
            file_obj.set_property('pattern', '*')
            objects.append(file_obj)
        
        return objects
    
    def _create_directory_objects(self, entities: Dict[str, Any], query: str) -> List[VirtualObject]:
        """Create directory objects from entities."""
        objects = []
        
        # Determine directory location based on context
        if 'user' in entities:
            # User directory - use home directory
            import os
            home_dir = Path(os.path.expanduser('~'))
            
            dir_obj = self.object_manager.create_directory_object(home_dir, 'user_home')
            dir_obj.set_property('user_context', True)
            objects.append(dir_obj)
        
        return objects
    
    def _extract_name_and_path(self, 
                              obj_type: ObjectType,
                              properties: Dict[str, Any],
                              entities: Dict[str, Any]) -> Tuple[str, Optional[Path]]:
        """Extract name and path for object."""
        if obj_type == ObjectType.USER:
            username = properties.get('username', 'user')
            return username, None
        
        elif obj_type == ObjectType.FILE:
            filename = properties.get('filename', '*')
            
            if properties.get('user_context') is True:
                import os
                home_dir = Path(os.path.expanduser('~'))
                path = home_dir / filename
                return f"user_{filename}", path
            else:
                location = properties.get('location', '.')
                path = Path(location) / filename
                return filename, path
        
        elif obj_type == ObjectType.DIRECTORY:
            dirname = properties.get('dirname', '.')
            
            if properties.get('user_context') is True:
                import os
                home_dir = Path(os.path.expanduser('~'))
                path = home_dir
                return "user_home", path
            else:
                path = Path(dirname)
                return dirname, path
        
        else:
            return obj_type.value, None
    
    def _establish_relationships(self, objects: List[VirtualObject], entities: Dict[str, Any]):
        """Establish relationships between created objects."""
        # Find user object
        user_obj = None
        for obj in objects:
            if obj.type == ObjectType.USER:
                user_obj = obj
                break
        
        if not user_obj:
            return
        
        # Establish relationships with user
        for obj in objects:
            if obj != user_obj and obj.get_property('user_context'):
                # User owns/has access to this object
                obj.add_relationship('owner', user_obj.id)
                user_obj.add_relationship('owns', obj.id)
    
    def get_conceptual_context(self, query: str) -> Dict[str, Any]:
        """Get conceptual context for query."""
        objects = self.create_objects_from_query(query)
        
        context = {
            'query': query,
            'objects': [obj.to_dict() for obj in objects],
            'user_context': 'user' in self.enhanced_detector.get_best_match(query).entities,
            'semantic_intent': None,
            'environment_variables': {}
        }
        
        # Add semantic intent
        match = self.enhanced_detector.get_best_match(query)
        if match:
            context['semantic_intent'] = {
                'domain': match.domain,
                'intent': match.intent,
                'confidence': match.combined_score
            }
        
        # Add relevant environment variables
        if context['user_context']:
            import os
            context['environment_variables'] = {
                'HOME': os.environ.get('HOME'),
                'USER': os.environ.get('USER'),
                'PWD': os.environ.get('PWD')
            }
        
        return context
