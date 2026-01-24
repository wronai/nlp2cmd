"""
Dependency Resolver Module

Resolves dependencies for command execution in script environments.
Provides intelligent dependency checking and resolution.
"""

import os
import subprocess
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

from .environment import EnvironmentContext, EnvironmentObject
from .virtual_objects import VirtualObject, ObjectType


class DependencyType(Enum):
    """Types of dependencies."""
    TOOL = "tool"
    FILE = "file"
    DIRECTORY = "directory"
    PERMISSION = "permission"
    ENVIRONMENT = "environment"
    SERVICE = "service"
    NETWORK = "network"


@dataclass
class Dependency:
    """Dependency requirement."""
    
    name: str
    type: DependencyType
    required: bool = True
    version: Optional[str] = None
    alternatives: List[str] = None
    check_command: Optional[str] = None
    description: str = ""
    
    def __post_init__(self):
        if self.alternatives is None:
            self.alternatives = []


@dataclass
class DependencyResult:
    """Result of dependency check."""
    
    dependency: Dependency
    satisfied: bool
    available_version: Optional[str] = None
    error_message: str = ""
    suggestions: List[str] = None
    
    def __post_init__(self):
        if self.suggestions is None:
            self.suggestions = []


class DependencyResolver:
    """Resolver for command dependencies."""
    
    def __init__(self, environment: Optional[EnvironmentContext] = None):
        self.environment = environment or EnvironmentContext()
        self.dependency_cache: Dict[str, DependencyResult] = {}
    
    def resolve_command_dependencies(self, command: str, context: Dict[str, Any]) -> List[DependencyResult]:
        """Resolve dependencies for a command."""
        dependencies = self._extract_dependencies(command, context)
        results = []
        
        for dep in dependencies:
            result = self._check_dependency(dep)
            results.append(result)
        
        return results
    
    def _extract_dependencies(self, command: str, context: Dict[str, Any]) -> List[Dependency]:
        """Extract dependencies from command and context."""
        dependencies = []
        
        # Tool dependencies
        tool_deps = self._extract_tool_dependencies(command)
        dependencies.extend(tool_deps)
        
        # File/directory dependencies
        file_deps = self._extract_file_dependencies(command, context)
        dependencies.extend(file_deps)
        
        # Environment dependencies
        env_deps = self._extract_environment_dependencies(command, context)
        dependencies.extend(env_deps)
        
        # Permission dependencies
        perm_deps = self._extract_permission_dependencies(command)
        dependencies.extend(perm_deps)
        
        return dependencies
    
    def _extract_tool_dependencies(self, command: str) -> List[Dependency]:
        """Extract tool dependencies from command."""
        dependencies = []
        
        # Common tools and their commands
        tool_commands = {
            'git': ['git'],
            'docker': ['docker'],
            'docker-compose': ['docker-compose', 'docker compose'],
            'kubectl': ['kubectl'],
            'python': ['python', 'python3'],
            'pip': ['pip', 'pip3'],
            'node': ['node'],
            'npm': ['npm'],
            'make': ['make'],
            'gcc': ['gcc'],
            'java': ['java'],
            'mvn': ['mvn', 'maven'],
            'gradle': ['gradle'],
            'ansible': ['ansible'],
            'terraform': ['terraform'],
            'aws': ['aws'],
            'az': ['az'],
            'gcloud': ['gcloud']
        }
        
        for tool, commands in tool_commands.items():
            if any(cmd in command for cmd in commands):
                alternatives = [cmd for cmd in commands if cmd != commands[0]]
                dep = Dependency(
                    name=tool,
                    type=DependencyType.TOOL,
                    required=True,
                    alternatives=alternatives,
                    check_command=commands[0],
                    description=f"{tool} command line tool"
                )
                dependencies.append(dep)
        
        return dependencies
    
    def _extract_file_dependencies(self, command: str, context: Dict[str, Any]) -> List[Dependency]:
        """Extract file dependencies from command and context."""
        dependencies = []
        
        # Extract file paths from command
        import re
        
        # Pattern for file paths
        file_patterns = [
            r'\b(?:~?/[^\s]+)',  # Unix paths
            r'\b\w+\.\w+\b',    # filenames with extensions
            r'\b(?:\w+/)+\w+\b'  # relative paths
        ]
        
        for pattern in file_patterns:
            matches = re.findall(pattern, command)
            for match in matches:
                path = Path(match)
                
                if path.exists():
                    continue  # File exists, no dependency issue
                
                dep = Dependency(
                    name=str(path),
                    type=DependencyType.FILE,
                    required=True,
                    description=f"File {path} must exist"
                )
                dependencies.append(dep)
        
        # Context-based file dependencies
        if context.get('user_context'):
            # User directory must be accessible
            home_dir = Path.home()
            if not home_dir.exists():
                dep = Dependency(
                    name=str(home_dir),
                    type=DependencyType.DIRECTORY,
                    required=True,
                    description="User home directory must exist"
                )
                dependencies.append(dep)
        
        return dependencies
    
    def _extract_environment_dependencies(self, command: str, context: Dict[str, Any]) -> List[Dependency]:
        """Extract environment dependencies from command and context."""
        dependencies = []
        
        # Common environment variables
        env_vars = ['HOME', 'USER', 'PATH', 'PWD', 'SHELL']
        
        for var in env_vars:
            if var in command or var.lower() in command.lower():
                if var not in os.environ:
                    dep = Dependency(
                        name=var,
                        type=DependencyType.ENVIRONMENT,
                        required=True,
                        description=f"Environment variable {var} must be set"
                    )
                    dependencies.append(dep)
        
        # Context-based environment dependencies
        if context.get('user_context'):
            required_vars = ['HOME', 'USER']
            for var in required_vars:
                if var not in os.environ:
                    dep = Dependency(
                        name=var,
                        type=DependencyType.ENVIRONMENT,
                        required=True,
                        description=f"User context requires {var} environment variable"
                    )
                    dependencies.append(dep)
        
        return dependencies
    
    def _extract_permission_dependencies(self, command: str) -> List[Dependency]:
        """Extract permission dependencies from command."""
        dependencies = []
        
        # Commands that require specific permissions
        permission_commands = {
            'sudo': 'sudo access',
            'chmod': 'file modification permissions',
            'chown': 'file ownership permissions',
            'mount': 'system mounting permissions',
            'systemctl': 'system service management',
            'service': 'system service management',
            'iptables': 'network firewall configuration',
            'docker': 'docker daemon access'
        }
        
        for cmd, permission in permission_commands.items():
            if cmd in command:
                dep = Dependency(
                    name=permission,
                    type=DependencyType.PERMISSION,
                    required=True,
                    description=f"Command requires {permission}"
                )
                dependencies.append(dep)
        
        return dependencies
    
    def _check_dependency(self, dependency: Dependency) -> DependencyResult:
        """Check if dependency is satisfied."""
        cache_key = f"{dependency.type}:{dependency.name}"
        
        if cache_key in self.dependency_cache:
            return self.dependency_cache[cache_key]
        
        result = self._perform_dependency_check(dependency)
        self.dependency_cache[cache_key] = result
        
        return result
    
    def _perform_dependency_check(self, dependency: Dependency) -> DependencyResult:
        """Perform actual dependency check."""
        if dependency.type == DependencyType.TOOL:
            return self._check_tool_dependency(dependency)
        elif dependency.type == DependencyType.FILE:
            return self._check_file_dependency(dependency)
        elif dependency.type == DependencyType.DIRECTORY:
            return self._check_directory_dependency(dependency)
        elif dependency.type == DependencyType.ENVIRONMENT:
            return self._check_environment_dependency(dependency)
        elif dependency.type == DependencyType.PERMISSION:
            return self._check_permission_dependency(dependency)
        else:
            return DependencyResult(
                dependency=dependency,
                satisfied=False,
                error_message=f"Unknown dependency type: {dependency.type}"
            )
    
    def _check_tool_dependency(self, dependency: Dependency) -> DependencyResult:
        """Check tool dependency."""
        try:
            # Check primary command
            result = subprocess.run(
                ['which', dependency.check_command],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return DependencyResult(
                    dependency=dependency,
                    satisfied=True,
                    available_version=self._get_tool_version(dependency.check_command)
                )
            
            # Check alternatives
            for alt in dependency.alternatives:
                result = subprocess.run(
                    ['which', alt],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    return DependencyResult(
                        dependency=dependency,
                        satisfied=True,
                        available_version=self._get_tool_version(alt),
                        suggestions=[f"Using alternative: {alt}"]
                    )
            
            return DependencyResult(
                dependency=dependency,
                satisfied=False,
                error_message=f"Tool {dependency.name} not found",
                suggestions=[f"Install {dependency.name}"] + dependency.alternatives
            )
            
        except Exception as e:
            return DependencyResult(
                dependency=dependency,
                satisfied=False,
                error_message=f"Error checking tool: {e}"
            )
    
    def _check_file_dependency(self, dependency: Dependency) -> DependencyResult:
        """Check file dependency."""
        file_path = Path(dependency.name)
        
        if file_path.exists():
            return DependencyResult(
                dependency=dependency,
                satisfied=True
            )
        
        return DependencyResult(
            dependency=dependency,
            satisfied=False,
            error_message=f"File {file_path} does not exist",
            suggestions=[f"Create file: {file_path}"]
        )
    
    def _check_directory_dependency(self, dependency: Dependency) -> DependencyResult:
        """Check directory dependency."""
        dir_path = Path(dependency.name)
        
        if dir_path.exists() and dir_path.is_dir():
            return DependencyResult(
                dependency=dependency,
                satisfied=True
            )
        
        return DependencyResult(
            dependency=dependency,
            satisfied=False,
            error_message=f"Directory {dir_path} does not exist",
            suggestions=[f"Create directory: {dir_path}"]
        )
    
    def _check_environment_dependency(self, dependency: Dependency) -> DependencyResult:
        """Check environment dependency."""
        if dependency.name in os.environ:
            return DependencyResult(
                dependency=dependency,
                satisfied=True,
                available_version=os.environ[dependency.name]
            )
        
        return DependencyResult(
            dependency=dependency,
            satisfied=False,
            error_message=f"Environment variable {dependency.name} not set",
            suggestions=[f"Set environment variable: export {dependency.name}=value"]
        )
    
    def _check_permission_dependency(self, dependency: Dependency) -> DependencyResult:
        """Check permission dependency."""
        # Simple check - try to run a command that requires the permission
        try:
            if 'sudo' in dependency.name:
                # Try sudo with non-interactive flag
                result = subprocess.run(
                    ['sudo', '-n', 'true'],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                
                if result.returncode == 0:
                    return DependencyResult(
                        dependency=dependency,
                        satisfied=True
                    )
                else:
                    return DependencyResult(
                        dependency=dependency,
                        satisfied=False,
                        error_message="Sudo access not available",
                        suggestions=["Configure sudo access or run without sudo"]
                    )
            
            # For other permissions, assume they're available
            return DependencyResult(
                dependency=dependency,
                satisfied=True
            )
            
        except Exception as e:
            return DependencyResult(
                dependency=dependency,
                satisfied=False,
                error_message=f"Error checking permission: {e}"
            )
    
    def _get_tool_version(self, tool: str) -> Optional[str]:
        """Get version of a tool."""
        try:
            result = subprocess.run(
                [tool, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if result.returncode == 0:
                return result.stdout.strip().split('\n')[0]
            
        except Exception:
            pass
        
        return None
    
    def get_dependency_summary(self, results: List[DependencyResult]) -> Dict[str, Any]:
        """Get summary of dependency results."""
        satisfied = [r for r in results if r.satisfied]
        unsatisfied = [r for r in results if not r.satisfied]
        
        return {
            'total': len(results),
            'satisfied': len(satisfied),
            'unsatisfied': len(unsatisfied),
            'can_proceed': len(unsatisfied) == 0 or all(not r.dependency.required for r in unsatisfied),
            'critical_issues': [r for r in unsatisfied if r.dependency.required],
            'optional_issues': [r for r in unsatisfied if not r.dependency.required],
            'suggestions': list(set([s for r in results for s in r.suggestions]))
        }
