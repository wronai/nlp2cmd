"""
NLP2CMD Concepts Module

Virtual objects created based on semantics for script execution environments.
Provides dependency-aware command generation with environment objects.
"""

from .environment import EnvironmentObject, EnvironmentContext
from .virtual_objects import VirtualObject, VirtualObjectManager, ObjectType
from .semantic_objects import SemanticPattern, SemanticObjectFactory
from .dependency_resolver import DependencyResolver, DependencyType
from .conceptual_commands import ConceptualCommandGenerator

__all__ = [
    'EnvironmentObject',
    'EnvironmentContext', 
    'VirtualObject',
    'VirtualObjectManager',
    'ObjectType',
    'SemanticPattern',
    'SemanticObjectFactory',
    'DependencyResolver',
    'DependencyType',
    'ConceptualCommandGenerator',
]
