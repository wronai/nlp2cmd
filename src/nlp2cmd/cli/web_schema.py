"""
CLI commands for web schema extraction and management.
"""

from __future__ import annotations

import click
from pathlib import Path
from rich.console import Console
from rich.table import Table

console = Console()


@click.group(name="web-schema")
def web_schema_group():
    """Web schema extraction and management commands."""
    pass


@web_schema_group.command(name="extract")
@click.argument("url")
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default="./command_schemas/sites",
    help="Output directory for schema"
)
@click.option(
    "--headless/--no-headless",
    default=True,
    help="Run browser in headless mode"
)
def extract_schema(url: str, output: Path, headless: bool):
    """Extract schema from a web page."""
    from nlp2cmd.web_schema.extractor import extract_web_schema
    
    console.print(f"\n[cyan]Extracting schema from {url}...[/cyan]")
    
    try:
        schema = extract_web_schema(url, output_dir=output, headless=headless)
        
        console.print(f"\n[green]✓ Schema extracted successfully[/green]")
        console.print(f"[dim]Domain: {schema.domain}[/dim]")
        console.print(f"[dim]Title: {schema.title}[/dim]")
        
        # Display summary
        table = Table(title="Extracted Elements")
        table.add_column("Type", style="cyan")
        table.add_column("Count", style="green")
        
        table.add_row("Input fields", str(len(schema.inputs)))
        table.add_row("Buttons", str(len(schema.buttons)))
        table.add_row("Links", str(len(schema.links)))
        table.add_row("Forms", str(len(schema.forms)))
        
        console.print(table)
        
        # Show some examples
        if schema.inputs:
            console.print("\n[yellow]Example inputs:[/yellow]")
            for inp in schema.inputs[:3]:
                label = inp.aria_label or inp.placeholder or inp.name or "unnamed"
                console.print(f"  • {label} ({inp.selector})")
        
        if schema.buttons:
            console.print("\n[yellow]Example buttons:[/yellow]")
            for btn in schema.buttons[:3]:
                label = btn.text or btn.aria_label or "unnamed"
                console.print(f"  • {label} ({btn.selector})")
        
    except Exception as e:
        console.print(f"[red]✗ Failed to extract schema: {e}[/red]")
        raise click.Abort()


@web_schema_group.command(name="history")
@click.option(
    "--domain",
    help="Filter by domain"
)
@click.option(
    "--limit",
    type=int,
    default=20,
    help="Number of recent interactions to show"
)
@click.option(
    "--stats",
    is_flag=True,
    help="Show statistics instead of history"
)
def show_history(domain: str | None, limit: int, stats: bool):
    """Show interaction history."""
    from nlp2cmd.web_schema.history import InteractionHistory
    
    history = InteractionHistory()
    
    if stats and domain:
        # Show domain statistics
        stats_data = history.get_domain_stats(domain)
        
        console.print(f"\n[cyan]Statistics for {domain}[/cyan]\n")
        console.print(f"Total interactions: {stats_data['total_interactions']}")
        console.print(f"Success rate: {stats_data['success_rate']:.1%}")
        console.print(f"Successful: {stats_data['successful_interactions']}")
        console.print(f"Failed: {stats_data['failed_interactions']}")
        
        if stats_data.get('action_types'):
            console.print("\n[yellow]Action types:[/yellow]")
            for action, count in stats_data['action_types'].items():
                console.print(f"  • {action}: {count}")
        
    elif stats:
        console.print("[yellow]Please specify --domain for statistics[/yellow]")
    
    else:
        # Show recent interactions
        records = history.get_recent_interactions(limit)
        
        if domain:
            records = [r for r in records if r.domain == domain]
        
        if not records:
            console.print("[yellow]No interactions found[/yellow]")
            return
        
        table = Table(title=f"Recent Interactions ({len(records)})")
        table.add_column("Time", style="dim")
        table.add_column("Domain", style="cyan")
        table.add_column("Action", style="yellow")
        table.add_column("Selector", style="green")
        table.add_column("Status", style="bold")
        
        for record in records:
            status = "✓" if record.success else "✗"
            status_style = "green" if record.success else "red"
            
            table.add_row(
                record.timestamp.split('T')[1][:8],  # Time only
                record.domain,
                record.action_type,
                record.selector or "-",
                f"[{status_style}]{status}[/{status_style}]"
            )
        
        console.print(table)


@web_schema_group.command(name="export-learned")
@click.argument("domain")
@click.option(
    "-o", "--output",
    type=click.Path(path_type=Path),
    default="./command_schemas/sites",
    help="Output directory"
)
def export_learned_schema(domain: str, output: Path):
    """Export learned schema from interaction history."""
    from nlp2cmd.web_schema.history import InteractionHistory
    
    history = InteractionHistory()
    
    console.print(f"\n[cyan]Exporting learned schema for {domain}...[/cyan]")
    
    output_file = history.export_domain_schema(domain, output)
    
    if output_file:
        console.print(f"\n[green]✓ Learned schema exported to {output_file}[/green]")
        
        stats = history.get_domain_stats(domain)
        console.print(f"[dim]Based on {stats['total_interactions']} interactions[/dim]")
        console.print(f"[dim]Success rate: {stats['success_rate']:.1%}[/dim]")
    else:
        console.print(f"[yellow]No interactions found for {domain}[/yellow]")


@web_schema_group.command(name="clear")
@click.option(
    "--domain",
    help="Clear history for specific domain"
)
@click.option(
    "--all",
    "clear_all",
    is_flag=True,
    help="Clear all history"
)
def clear_history(domain: str | None, clear_all: bool):
    """Clear interaction history."""
    from nlp2cmd.web_schema.history import InteractionHistory
    
    history = InteractionHistory()
    
    if clear_all:
        console.print("[yellow]Clear all interaction history? [y/N]:[/yellow] ", end="")
        if console.input().strip().lower() in ("y", "yes"):
            history.clear_all()
            console.print("[green]✓ All history cleared[/green]")
    elif domain:
        console.print(f"[yellow]Clear history for {domain}? [y/N]:[/yellow] ", end="")
        if console.input().strip().lower() in ("y", "yes"):
            history.clear_domain(domain)
            console.print(f"[green]✓ History cleared for {domain}[/green]")
    else:
        console.print("[yellow]Please specify --domain or --all[/yellow]")
