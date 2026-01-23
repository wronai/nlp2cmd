#!/usr/bin/env python3
"""Update schemas for all commands listed in cmd.txt."""

import csv
from pathlib import Path
from typing import List, Set

from intelligent_schema_generator import IntelligentSchemaExtractor


def load_commands_from_files() -> List[str]:
    """Load unique commands from cmd.csv and cmd.txt."""
    commands = set()
    
    # Load from cmd.csv
    if Path('./cmd.csv').exists():
        print("Loading commands from cmd.csv...")
        with open('./cmd.csv') as f:
            reader = csv.reader(f)
            next(reader)  # Skip header
            for row in reader:
                if row[1] and not row[1].startswith('#'):
                    # Extract base command
                    parts = row[1].split()
                    if parts:
                        cmd = parts[0]
                        # Clean up command name
                        cmd = cmd.strip('<>{}[]')
                        if cmd and cmd not in ['echo', '#']:
                            commands.add(cmd)
    
    # Load from cmd.txt
    if Path('./cmd.txt').exists():
        print("Loading commands from cmd.txt...")
        with open('./cmd.txt') as f:
            for line in f:
                cmd = line.strip()
                if cmd and not cmd.startswith('#'):
                    commands.add(cmd)
    
    return sorted(commands)


def update_all_schemas(force_update: bool = True) -> None:
    """Update schemas for all commands."""
    
    # Load commands
    commands = load_commands_from_files()
    
    if not commands:
        print("No commands found. Creating default list...")
        commands = [
            'find', 'grep', 'sed', 'awk', 'ls', 'mkdir', 'rm', 'cp', 'mv',
            'ps', 'top', 'kill', 'docker', 'kubectl', 'git', 'curl', 'wget',
            'tar', 'zip', 'ssh', 'python3', 'npm', 'gcc', 'make', 'df', 'du',
            'free', 'uname', 'whoami', 'chmod', 'chown', 'cat', 'less', 'head',
            'tail', 'sort', 'uniq', 'wc', 'tr', 'cut', 'xargs', 'which'
        ]
    
    print(f"\nFound {len(commands)} unique commands to update:")
    print(", ".join(commands[:10]) + ("..." if len(commands) > 10 else ""))
    
    # Initialize extractor
    print("\nInitializing intelligent schema extractor...")
    extractor = IntelligentSchemaExtractor()
    
    # Update schemas
    print(f"\nUpdating schemas (force_update={force_update})...\n")
    
    results = extractor.batch_generate(commands, force_update=force_update)
    
    # Summary
    successful = sum(results.values())
    failed = len(results) - successful
    
    print(f"\n{'='*60}")
    print(f"UPDATE SUMMARY")
    print(f"{'='*60}")
    print(f"Total commands: {len(commands)}")
    print(f"✅ Successfully updated: {successful}")
    print(f"❌ Failed: {failed}")
    print(f"📁 Schemas saved to: ./command_schemas/")
    
    # Show failed commands
    if failed > 0:
        print("\nFailed commands:")
        for cmd, success in results.items():
            if not success:
                print(f"  - {cmd}")
    
    # Category statistics
    print("\nSchemas by category:")
    print("-" * 40)
    
    categories = {}
    for command, success in results.items():
        if success:
            schema = extractor.registry.schemas.get(command)
            if schema and schema.commands:
                cat = schema.commands[0].category
                categories[cat] = categories.get(cat, 0) + 1
    
    for category, count in sorted(categories.items()):
        print(f"  {category:15}: {count:3} commands")
    
    # Export all schemas
    export_file = './all_schemas.json'
    extractor.registry.save_cache(export_file)
    print(f"\n💾 All schemas exported to: {export_file}")
    
    # Generate command list file
    with open('./generated_commands.txt', 'w') as f:
        for cmd in sorted(commands):
            f.write(f"{cmd}\n")
    print(f"📝 Command list saved to: ./generated_commands.txt")
    
    # Show sample schemas
    print("\n" + "="*60)
    print("SAMPLE SCHEMAS")
    print("="*60)
    
    sample_commands = ['find', 'docker', 'git', 'python3']
    
    for cmd in sample_commands:
        if cmd in extractor.registry.schemas:
            schema = extractor.registry.schemas[cmd]
            if schema.commands:
                cmd_schema = schema.commands[0]
                print(f"\n{cmd.upper()}:")
                print(f"  Category: {cmd_schema.category}")
                print(f"  Description: {cmd_schema.description}")
                print(f"  Template: {cmd_schema.template}")
                print(f"  Parameters: {len(cmd_schema.parameters)}")
                print(f"  Examples: {len(cmd_schema.examples)}")


def main():
    """Main function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Update command schemas")
    parser.add_argument(
        "--force", 
        action="store_true",
        help="Force update existing schemas"
    )
    parser.add_argument(
        "--list", 
        action="store_true",
        help="Only list commands that would be updated"
    )
    
    args = parser.parse_args()
    
    if args.list:
        commands = load_commands_from_files()
        print(f"Commands to update ({len(commands)}):")
        for cmd in commands:
            print(f"  {cmd}")
        return
    
    update_all_schemas(force_update=args.force)


if __name__ == "__main__":
    main()
