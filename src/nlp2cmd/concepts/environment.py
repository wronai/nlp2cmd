"""
Environment Objects Module

Virtual objects representing script execution environments.
Provides context-aware command generation with environment variables.
"""

import os
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field


@dataclass
class EnvironmentObject:
    """Virtual object representing execution environment."""
    
    name: str
    path: Path
    variables: Dict[str, str] = field(default_factory=dict)
    dependencies: List[str] = field(default_factory=list)
    tools: List[str] = field(default_factory=list)
    config_files: List[Path] = field(default_factory=list)
    
    def __post_init__(self):
        """Initialize environment object with system context."""
        self._load_environment_variables()
        self._detect_tools()
        self._find_config_files()
    
    def _load_environment_variables(self):
        """Load relevant environment variables."""
        # User-related variables
        user_vars = ['HOME', 'USER', 'USERNAME', 'LOGNAME']
        for var in user_vars:
            if var in os.environ:
                self.variables[var] = os.environ[var]
        
        # Shell-related variables
        shell_vars = ['SHELL', 'PATH', 'PWD']
        for var in shell_vars:
            if var in os.environ:
                self.variables[var] = os.environ[var]
        
        # Project-related variables
        project_vars = ['PROJECT_ROOT', 'WORKSPACE', 'VIRTUAL_ENV']
        for var in project_vars:
            if var in os.environ:
                self.variables[var] = os.environ[var]
    
    def _detect_tools(self):
        """Detect available tools in environment."""
        common_tools = [
            'git', 'docker', 'docker-compose', 'kubectl', 
            'python', 'python3', 'node', 'npm', 'pip',
            'make', 'gcc', 'java', 'mvn', 'gradle',
            'ansible', 'terraform', 'aws', 'az', 'gcloud'
        ]
        
        for tool in common_tools:
            try:
                result = subprocess.run(['which', tool], 
                                      capture_output=True, 
                                      text=True, timeout=2)
                if result.returncode == 0:
                    self.tools.append(tool)
            except (subprocess.TimeoutExpired, FileNotFoundError):
                continue
    
    def _find_config_files(self):
        """Find configuration files in environment."""
        config_patterns = [
            '.gitignore', '.env', 'requirements.txt', 'package.json',
            'Dockerfile', 'docker-compose.yml', 'Makefile',
            'pyproject.toml', 'setup.py', 'Cargo.toml', 'pom.xml',
            '.bashrc', '.zshrc', '.profile', 'config.yaml'
        ]
        
        for pattern in config_patterns:
            files = list(self.path.rglob(pattern))
            self.config_files.extend(files)
    
    def get_user_home(self) -> Optional[Path]:
        """Get user home directory."""
        home_var = self.variables.get('HOME')
        if home_var:
            return Path(home_var)
        return None
    
    def get_current_user(self) -> Optional[str]:
        """Get current username."""
        return self.variables.get('USER') or self.variables.get('USERNAME')
    
    def get_working_directory(self) -> Path:
        """Get current working directory."""
        pwd_var = self.variables.get('PWD')
        if pwd_var:
            return Path(pwd_var)
        return Path.cwd()
    
    def has_tool(self, tool: str) -> bool:
        """Check if tool is available."""
        return tool in self.tools
    
    def get_config_file(self, name: str) -> Optional[Path]:
        """Get specific config file."""
        for config_file in self.config_files:
            if config_file.name == name:
                return config_file
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert environment object to dictionary."""
        return {
            'name': self.name,
            'path': str(self.path),
            'variables': self.variables,
            'dependencies': self.dependencies,
            'tools': self.tools,
            'config_files': [str(f) for f in self.config_files],
            'user_home': str(self.get_user_home()) if self.get_user_home() else None,
            'current_user': self.get_current_user(),
            'working_directory': str(self.get_working_directory())
        }


class EnvironmentContext:
    """Context manager for environment objects."""
    
    def __init__(self, base_path: Optional[Path] = None):
        self.base_path = base_path or Path.cwd()
        self.environment = EnvironmentObject(
            name="current",
            path=self.base_path
        )
    
    def __enter__(self) -> EnvironmentObject:
        """Enter environment context."""
        return self.environment
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit environment context."""
        pass
    
    def resolve_path(self, path_str: str, context: str = "current") -> Path:
        """Resolve path with environment context."""
        # Handle user directory references
        if path_str.startswith('~'):
            user_home = self.environment.get_user_home()
            if user_home:
                return user_home / path_str[1:]
        
        # Handle relative paths
        if not Path(path_str).is_absolute():
            if context == "user":
                user_home = self.environment.get_user_home()
                if user_home:
                    return user_home / path_str
            else:  # current directory
                return self.environment.get_working_directory() / path_str
        
        return Path(path_str)
    
    def get_environment_variables(self) -> Dict[str, str]:
        """Get relevant environment variables for command generation."""
        return self.environment.variables
    
    def check_dependencies(self, command: str) -> Dict[str, bool]:
        """Check if command dependencies are satisfied."""
        dependencies = {}
        
        # Check for required tools
        if 'git' in command:
            dependencies['git'] = self.environment.has_tool('git')
        if 'docker' in command:
            dependencies['docker'] = self.environment.has_tool('docker')
        if 'kubectl' in command:
            dependencies['kubectl'] = self.environment.has_tool('kubectl')
        if 'python' in command or 'pip' in command:
            dependencies['python'] = self.environment.has_tool('python')
        
        return dependencies
