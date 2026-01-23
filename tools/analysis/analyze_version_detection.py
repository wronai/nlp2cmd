#!/usr/bin/env python3
"""Analyze version detection standards and implementation."""

import subprocess
import re
from typing import Dict, List, Optional, Tuple


def analyze_version_standards():
    """Analyze common version detection standards."""
    
    print("=" * 60)
    print("VERSION DETECTION STANDARDS")
    print("=" * 60)
    
    standards = {
        "GNU Standards": {
            "description": "Most GNU/Linux tools follow --version flag",
            "flag": "--version",
            "format": "program_name (GNU coreutils) X.Y.Z",
            "examples": ["ls", "grep", "sed", "awk", "find"],
            "output_example": "ls (GNU coreutils) 8.32"
        },
        
        "BSD Standards": {
            "description": "BSD tools often use -v or --version",
            "flag": "-v or --version",
            "format": "program_name version X.Y",
            "examples": ["ps", "top", "netstat"],
            "output_example": "ps version 4.2.1"
        },
        
        "Container Tools": {
            "description": "Modern container tools have structured version output",
            "flag": "--version",
            "format": "Program version X.Y.Z, build HASH",
            "examples": ["docker", "podman", "kubectl"],
            "output_example": "Docker version 29.1.5, build 0e6fee6"
        },
        
        "Programming Languages": {
            "description": "Language runtimes show version info",
            "flag": "--version or -V",
            "format": "Language X.Y.Z",
            "examples": ["python", "node", "ruby", "perl"],
            "output_example": "Python 3.13.7"
        },
        
        "Version Control": {
            "description": "VCS tools have detailed version info",
            "flag": "--version",
            "format": "git version X.Y.Z",
            "examples": ["git", "svn", "hg"],
            "output_example": "git version 2.51.0"
        },
        
        "Package Managers": {
            "description": "Package managers show version",
            "flag": "--version",
            "format": "X.Y.Z",
            "examples": ["npm", "pip", "apt", "yum"],
            "output_example": "npm 10.8.2"
        },
        
        "Cloud Tools": {
            "description": "Cloud CLI tools have version commands",
            "flag": "version",
            "format": "aws-cli/2.15.24",
            "examples": ["aws", "gcloud", "az"],
            "output_example": "aws-cli/2.15.24 Python/3.11.6"
        }
    }
    
    for category, info in standards.items():
        print(f"\n{category}:")
        print(f"  Description: {info['description']}")
        print(f"  Flag: {info['flag']}")
        print(f"  Format: {info['format']}")
        print(f"  Examples: {', '.join(info['examples'])}")
        print(f"  Output: {info['output_example']}")


def test_version_detection_patterns():
    """Test various version detection patterns."""
    
    print("\n" + "=" * 60)
    print("VERSION DETECTION PATTERNS")
    print("=" * 60)
    
    patterns = {
        # Semantic Versioning
        "semver": r"\d+\.\d+\.\d+(?:-[a-zA-Z0-9-]+)?",
        
        # Docker style
        "docker": r"Docker version (\d+\.\d+\.\d+)",
        
        # Git style
        "git": r"git version (\d+\.\d+\.\d+)",
        
        # Python style
        "python": r"Python (\d+\.\d+\.\d+)",
        
        # Node style
        "node": r"v(\d+\.\d+\.\d+)",
        
        # AWS CLI style
        "aws": r"aws-cli/(\d+\.\d+\.\d+)",
        
        # Generic version
        "generic": r"version (\d+\.\d+(?:\.\d+)?)",
        
        # Build hash
        "build": r"build ([a-f0-9]{7,})",
        
        # Kernel version
        "kernel": r"Linux (\d+\.\d+\.\d+)",
    }
    
    test_outputs = {
        "docker": "Docker version 29.1.5, build 0e6fee6",
        "git": "git version 2.51.0",
        "python": "Python 3.13.7 (main, Dec 15 2024, 18:25:27)",
        "node": "v21.5.0",
        "aws": "aws-cli/2.15.24 Python/3.11.6 Linux/5.15.0",
        "ls": "ls (GNU coreutils) 8.32",
        "kubectl": "Client Version: v1.28.2",
        "curl": "curl 7.81.0 (x86_64-pc-linux-gnu)",
    }
    
    for tool, output in test_outputs.items():
        print(f"\n{tool}:")
        print(f"  Output: {output}")
        print(f"  Matches:")
        
        for pattern_name, pattern in patterns.items():
            match = re.search(pattern, output)
            if match:
                version = match.group(1) if match.groups() else match.group(0)
                print(f"    ✓ {pattern_name}: {version}")


def check_schema_version_support():
    """Check if schemas have version detection implemented."""
    
    print("\n" + "=" * 60)
    print("SCHEMA VERSION DETECTION SUPPORT")
    print("=" * 60)
    
    # Check migrated schemas
    import json
    from pathlib import Path
    
    schema_file = Path("./migrated_schemas/commands/docker.json")
    if schema_file.exists():
        with open(schema_file) as f:
            docker_schema = json.load(f)
        
        print("\nDocker Schema Structure:")
        print(f"  Command: {docker_schema.get('command')}")
        print(f"  Version: {docker_schema.get('version', 'Not specified')}")
        print(f"  Template: {docker_schema.get('template')}")
        print(f"  Metadata keys: {list(docker_schema.get('metadata', {}).keys())}")
        
        # Check if version is tracked
        if 'version' in docker_schema:
            print("  ✓ Version is tracked in schema")
        else:
            print("  ✗ Version not tracked in schema")
    
    # Check versioned store structure
    print("\nVersioned Store Structure:")
    versions_dir = Path("./migrated_schemas/versions")
    if versions_dir.exists():
        commands = [d.name for d in versions_dir.iterdir() if d.is_dir()]
        print(f"  Commands with versions: {len(commands)}")
        
        # Check docker versions
        docker_versions = versions_dir / "docker"
        if docker_versions.exists():
            versions = list(docker_versions.glob("*.json"))
            print(f"  Docker versions: {[v.stem for v in versions]}")
            
            # Check a version file
            if versions:
                with open(versions[0]) as f:
                    version_data = json.load(f)
                print(f"  Version file contains: {list(version_data.keys())}")


def demonstrate_version_detection_implementation():
    """Show how version detection is implemented."""
    
    print("\n" + "=" * 60)
    print("VERSION DETECTION IMPLEMENTATION")
    print("=" * 60)
    
    implementation = '''
# 1. Command Registry with Version Patterns
VERSION_PATTERNS = {
    'docker': {
        'command': ['docker', '--version'],
        'pattern': r'Docker version (\\d+\\.\\d+\\.\\d+)',
        'fallback': ['docker', 'version']
    },
    'kubectl': {
        'command': ['kubectl', 'version', '--client', '--short'],
        'pattern': r'Client Version: v?(\\d+\\.\\d+\\.\\d+)',
        'fallback': ['kubectl', 'version']
    },
    # ... more commands
}

# 2. Detection Function
def detect_version(command_name):
    config = VERSION_PATTERNS.get(command_name)
    if not config:
        return None
    
    try:
        # Run version command
        result = subprocess.run(config['command'], capture_output=True, text=True)
        if result.returncode == 0:
            # Extract version using regex
            match = re.search(config['pattern'], result.stdout + result.stderr)
            if match:
                return match.group(1)
    except:
        # Try fallback
        try:
            result = subprocess.run(config['fallback'], capture_output=True, text=True)
            # Extract from fallback...
        except:
            pass
    
    return None

# 3. Schema Selection Based on Version
def select_schema(command, detected_version):
    available_versions = list_schema_versions(command)
    
    # Find exact match
    if detected_version in available_versions:
        return detected_version
    
    # Find closest version
    return find_closest_version(detected_version, available_versions)

# 4. Command Adaptation
def adapt_command(command, version):
    if command == 'docker':
        major = int(version.split('.')[0])
        if major >= 2:
            return add_swarm_support(command)
    # ... more adaptations
'''
    
    print(implementation)


def best_practices():
    """Show best practices for version detection."""
    
    print("\n" + "=" * 60)
    print("BEST PRACTICES")
    print("=" * 60)
    
    practices = [
        "✅ Use multiple version flags (--version, -v, -V, version)",
        "✅ Cache version detection results",
        "✅ Handle different output formats",
        "✅ Provide fallback mechanisms",
        "✅ Support semantic versioning",
        "✅ Document version requirements",
        "✅ Test on multiple platforms",
        "✅ Handle build hashes and suffixes",
        "✅ Consider package manager versions",
        "✅ Validate version format"
    ]
    
    for practice in practices:
        print(f"  {practice}")
    
    print("\nCommon Challenges:")
    challenges = [
        "⚠️ Different output formats across platforms",
        "⚠️ Commands without --version flag",
        "⚠️ Custom builds with different versions",
        "⚠️ Network-dependent version checks",
        "⚠️ Permission issues running commands",
        "⚠️ Non-standard version formats"
    ]
    
    for challenge in challenges:
        print(f"  {challenge}")


def main():
    """Main analysis function."""
    analyze_version_standards()
    test_version_detection_patterns()
    check_schema_version_support()
    demonstrate_version_detection_implementation()
    best_practices()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
1. STANDARDS EXIST but vary by tool type:
   - GNU tools: --version with structured output
   - BSD tools: -v or --version
   - Container tools: --version with build info
   - Languages: --version or -V

2. CURRENT IMPLEMENTATION:
   - Basic pattern matching for common commands
   - Fallback mechanisms for unknown formats
   - Version caching for performance

3. SCHEMA SUPPORT:
   - Schemas store version in metadata
   - Versioned store tracks multiple versions
   - Not all schemas have version detection yet

4. IMPROVEMENTS NEEDED:
   - More comprehensive pattern library
   - Platform-specific handling
   - Better error handling
   - Automatic schema updates
    """)


if __name__ == "__main__":
    main()
