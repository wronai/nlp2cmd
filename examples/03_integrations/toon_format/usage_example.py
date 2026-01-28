"""
Example usage of the unified TOON format system
Demonstrates how to access and use consolidated project data
"""

import sys
from pathlib import Path

# Add src to path for imports
_repo_root = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(_repo_root / "src"))

from nlp2cmd.core.toon_integration import get_data_manager
from nlp2cmd.parsing.toon_parser import get_parser


def main():
    """Demonstrate TOON usage"""
    print("=== TOON Unified Format Usage Example ===\n")
    
    toon_path = _repo_root / "project.unified.toon"
    if not toon_path.exists():
        print(f"TOON file not found: {toon_path}")
        return

    # Get data manager
    manager = get_data_manager(str(toon_path))
    
    # 1. Project Metadata
    print("1. Project Metadata:")
    metadata = manager.get_project_metadata()
    print(f"   Project: {metadata.get('project')}")
    print(f"   Version: {metadata.get('version')}")
    print(f"   Format: {metadata.get('format')}")
    print()
    
    # 2. Configuration
    print("2. Configuration:")
    llm_config = manager.get_llm_config()
    print(f"   LLM Provider: {llm_config.get('provider')}")
    print(f"   LLM Model: {llm_config.get('model')}")
    print(f"   Temperature: {llm_config.get('temperature')}")
    print()
    
    # 3. Commands by Category
    print("3. Commands by Category:")
    
    # Shell commands
    shell_commands = manager.get_shell_commands()
    print(f"   Shell Commands: {len(shell_commands)} available")
    if 'git' in shell_commands:
        git_cmd = shell_commands['git']
        print(f"   - git: {git_cmd.get('description', '')[:50]}...")
    
    # Browser commands
    browser_commands = manager.get_browser_commands()
    print(f"   Browser Commands: {len(browser_commands)} available")
    if 'click' in browser_commands:
        click_cmd = browser_commands['click']
        print(f"   - click: {click_cmd.get('description', '')}")
    print()
    
    # 4. Search Commands
    print("4. Search Commands:")
    search_results = manager.search_commands("docker")
    print(f"   Found {len(search_results)} matches for 'docker':")
    for result in search_results[:3]:
        print(f"   - {result['path']}")
    print()
    
    # 5. Templates
    print("5. Templates:")
    command_templates = manager.get_command_templates()
    print("   Command Templates:")
    for name, template in command_templates.items():
        print(f"   - {name}: {template}")
    print()
    
    # 6. Mappings
    print("6. Mappings:")
    language_patterns = manager.get_language_patterns('english')
    print("   English Patterns:")
    for action, pattern in language_patterns.items():
        print(f"   - {action}: {pattern}")
    print()
    
    # 7. Statistics
    print("7. Statistics:")
    stats = manager.get_statistics()
    for key, value in stats.items():
        print(f"   {key}: {value}")
    print()
    
    # 8. Direct Parser Access:
    print("8. Direct Parser Access:")
    parser = get_parser(str(toon_path))
    
    # Get specific command
    git_command = parser.get_commands('shell').get('git')
    if git_command:
        print(f"   Git command examples: {git_command.get('examples', [])}")
    
    # Get config value
    batch_size = parser.get_config('schema_generation.batch_size')
    print(f"   Batch size: {batch_size}")
    print()
    
    # 9. Export Data
    print("9. Export Data:")
    commands_json = manager.export_category('commands', 'json')
    print(f"   Commands exported as JSON: {len(commands_json)} characters")
    
    config_yaml = manager.export_category('config', 'yaml')
    print(f"   Config exported as YAML: {len(config_yaml)} characters")
    print()
    
    print("=== TOON Usage Complete ===")


if __name__ == "__main__":
    main()
