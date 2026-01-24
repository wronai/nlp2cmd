"""
CLI commands for command history management.
"""

from __future__ import annotations

try:
    import click
except Exception:  # pragma: no cover
    class _ClickStub:
        def group(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def command(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def option(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def argument(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def Path(self, *args, **kwargs):
            return str
    click = _ClickStub()
from pathlib import Path
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except Exception:  # pragma: no cover
    class Console:
        def print(self, *args, **kwargs):
            try:
                builtins_print = __builtins__["print"] if isinstance(__builtins__, dict) else print
                builtins_print(*args)
            except Exception:
                return
    class Table:
        def __init__(self, *args, **kwargs):
            return
        def add_column(self, *args, **kwargs):
            return
        def add_row(self, *args, **kwargs):
            return
    class Panel:
        def __init__(self, *args, **kwargs):
            return

console = Console()


@click.group(name="history")
def history_group():
    """Command history and analytics."""
    pass


@history_group.command(name="show")
@click.option(
    "--dsl",
    help="Filter by DSL type"
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Number of recent commands to show"
)
@click.option(
    "--failed-only",
    is_flag=True,
    help="Show only failed commands"
)
def show_history(dsl: str | None, limit: int, failed_only: bool):
    """Show command execution history."""
    from nlp2cmd.history.tracker import get_global_history
    
    history = get_global_history()
    
    if failed_only:
        records = history.get_failed_commands(limit)
    elif dsl:
        records = history.get_by_dsl(dsl, limit)
    else:
        records = history.get_recent(limit)
    
    if not records:
        console.print("[yellow]No commands found in history[/yellow]")
        return
    
    table = Table(title=f"Command History ({len(records)} commands)")
    table.add_column("Time", style="dim")
    table.add_column("DSL", style="cyan")
    table.add_column("Query", style="yellow", max_width=40)
    table.add_column("Command", style="green", max_width=50)
    table.add_column("Status", style="bold")
    
    for record in records:
        status = "✓" if record.success else "✗"
        status_style = "green" if record.success else "red"
        
        # Truncate long strings
        query = record.query[:37] + "..." if len(record.query) > 40 else record.query
        command = record.command[:47] + "..." if len(record.command) > 50 else record.command
        
        table.add_row(
            record.timestamp.split('T')[1][:8],  # Time only
            record.dsl,
            query,
            command,
            f"[{status_style}]{status}[/{status_style}]"
        )
    
    console.print(table)


@history_group.command(name="stats")
@click.option(
    "--schema-usage",
    is_flag=True,
    help="Show schema usage statistics"
)
def show_stats(schema_usage: bool):
    """Show command execution statistics."""
    from nlp2cmd.history.tracker import get_global_history
    
    history = get_global_history()
    
    if schema_usage:
        stats = history.get_schema_usage_stats()
        
        console.print("\n[cyan]Schema Usage Statistics[/cyan]\n")
        console.print(f"Total schema uses: {stats['total_schema_uses']}")
        console.print(f"Unique schemas: {stats['unique_schemas']}\n")
        
        if stats['schemas']:
            table = Table(title="Schema Usage")
            table.add_column("Schema", style="cyan")
            table.add_column("Type", style="yellow")
            table.add_column("Uses", style="green")
            table.add_column("Success Rate", style="bold")
            table.add_column("Top Actions", style="dim")
            
            for schema_name, data in stats['schemas'].items():
                top_actions = sorted(
                    data['actions'].items(),
                    key=lambda x: x[1],
                    reverse=True
                )[:3]
                actions_str = ", ".join(f"{a}({c})" for a, c in top_actions)
                
                table.add_row(
                    schema_name,
                    data['schema_type'],
                    str(data['total_uses']),
                    f"{data['success_rate']:.1%}",
                    actions_str
                )
            
            console.print(table)
    else:
        stats = history.get_stats()
        
        console.print("\n[cyan]Overall Statistics[/cyan]\n")
        console.print(f"Total commands: {stats['total_commands']}")
        console.print(f"Success rate: {stats['success_rate']:.1%}")
        console.print(f"Successful: {stats['successful_commands']}")
        console.print(f"Failed: {stats['failed_commands']}")
        
        if stats.get('avg_duration_ms'):
            console.print(f"Average duration: {stats['avg_duration_ms']:.1f}ms")
        
        if stats['by_dsl']:
            console.print("\n[yellow]By DSL:[/yellow]")
            table = Table()
            table.add_column("DSL", style="cyan")
            table.add_column("Total", style="green")
            table.add_column("Successful", style="green")
            table.add_column("Success Rate", style="bold")
            
            for dsl, data in stats['by_dsl'].items():
                table.add_row(
                    dsl,
                    str(data['total']),
                    str(data['successful']),
                    f"{data['success_rate']:.1%}"
                )
            
            console.print(table)


@history_group.command(name="popular")
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Number of queries to show"
)
def show_popular(limit: int):
    """Show most popular queries."""
    from nlp2cmd.history.tracker import get_global_history
    
    history = get_global_history()
    queries = history.get_popular_queries(limit)
    
    if not queries:
        console.print("[yellow]No queries found[/yellow]")
        return
    
    table = Table(title=f"Top {len(queries)} Popular Queries")
    table.add_column("Rank", style="dim")
    table.add_column("Query", style="cyan")
    table.add_column("Count", style="green")
    
    for i, (query, count) in enumerate(queries, 1):
        table.add_row(
            str(i),
            query,
            str(count)
        )
    
    console.print(table)


@history_group.command(name="export")
@click.argument(
    "output",
    type=click.Path(path_type=Path),
)
def export_analytics(output: Path):
    """Export detailed analytics to JSON."""
    from nlp2cmd.history.tracker import get_global_history
    
    history = get_global_history()
    
    console.print(f"\n[cyan]Exporting analytics to {output}...[/cyan]")
    
    history.export_analytics(output)
    
    console.print(f"[green]✓ Analytics exported successfully[/green]")


@history_group.command(name="clear")
@click.option(
    "--confirm",
    is_flag=True,
    help="Skip confirmation prompt"
)
def clear_history(confirm: bool):
    """Clear command history."""
    from nlp2cmd.history.tracker import get_global_history
    
    history = get_global_history()
    
    if not confirm:
        console.print("[yellow]Clear all command history? [y/N]:[/yellow] ", end="")
        if console.input().strip().lower() not in ("y", "yes"):
            console.print("[dim]Cancelled[/dim]")
            return
    
    history.clear()
    console.print("[green]✓ Command history cleared[/green]")
