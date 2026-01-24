"""
NLP2CMD Concepts Module

Virtual objects created based on semantics for script execution environments.
Provides dependency-aware command generation with environment objects.
"""

from .environment import EnvironmentObject, EnvironmentContext
from .virtual_objects import VirtualObject, VirtualObjectManager
from .semantic_objects import SemanticObject, SemanticObjectFactory
from .dependency_resolver import DependencyResolver
from .conceptual_commands import ConceptualCommandGenerator

__all__ = [
    'EnvironmentObject',
    'EnvironmentContext', 
    'VirtualObject',
    'VirtualObjectManager',
    'SemanticObject',
    'SemanticObjectFactory',
    'DependencyResolver',
    'ConceptualCommandGenerator',
]
