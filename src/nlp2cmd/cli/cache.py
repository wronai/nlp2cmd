"""
CLI commands for external dependencies cache management.
"""

from __future__ import annotations

try:
    import click
except Exception:  # pragma: no cover
    class _ClickStub:
        class Group:
            def __init__(self, *args, **kwargs):
                pass
            def command(self, *args, **kwargs):
                def decorator(func):
                    return func
                return decorator
        def group(self, *args, **kwargs):
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
        def confirm(self, *args, **kwargs):
            def decorator(func):
                return func
            return decorator
        def Abort(self):
            raise SystemExit(1)
    click = _ClickStub()

from pathlib import Path
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.progress import Progress, SpinnerColumn, TextColumn
except Exception:  # pragma: no cover
    class Console:
        def print(self, *args, **kwargs):
            try:
                builtins_print = __builtins__["print"] if isinstance(__builtins__, dict) else print
                builtins_print(*args)
            except Exception:
                return
        def input(self, *args, **kwargs):
            return input(*args[0] if args else "")
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
    class Progress:
        def __enter__(self):
            return self
        def __exit__(self, *args, **kwargs):
            return
        def add_task(self, *args, **kwargs):
            return "task"
        def update(self, *args, **kwargs):
            return
    class SpinnerColumn:
        def __init__(self, *args, **kwargs):
            return
    class TextColumn:
        def __init__(self, *args, **kwargs):
            return

console = Console()


@click.group(name="cache")
def cache_group():
    """External dependencies cache management."""
    pass


@cache_group.command(name="setup")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory"
)
def setup_cache(cache_dir: Path | None):
    """Setup environment for cached external dependencies."""
    from nlp2cmd.utils.external_cache import ExternalCacheManager
    
    console.print("[cyan]Setting up external cache environment...[/cyan]")
    
    manager = ExternalCacheManager(cache_dir)
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Configuring cache...", total=None)
        
        if manager.setup_environment():
            progress.update(task, description="✓ Environment configured")
            console.print(f"[green]✓ Cache environment ready[/green]")
            console.print(f"[dim]Cache directory: {manager.cache_dir}[/dim]")
        else:
            progress.update(task, description="✗ Setup failed")
            console.print("[red]✗ Failed to setup cache environment[/red]")
            raise click.Abort()


@cache_group.command(name="install")
@click.option(
    "--package",
    type=click.Choice(['playwright', 'all']),
    default='all',
    help="Package to install (default: all)"
)
@click.option(
    "--force",
    is_flag=True,
    help="Force reinstallation"
)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory"
)
def install_package(package: str, force: bool, cache_dir: Path | None):
    """Install external packages to cache."""
    from nlp2cmd.utils.external_cache import ExternalCacheManager
    
    manager = ExternalCacheManager(cache_dir)
    
    if package == 'playwright' or package == 'all':
        console.print("[cyan]Installing Playwright browsers...[/cyan]")
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=console,
        ) as progress:
            task = progress.add_task("Installing...", total=None)
            
            if manager.install_playwright_if_needed(force=force):
                progress.update(task, description="✓ Installation complete")
                console.print("[green]✓ Playwright browsers installed[/green]")
                
                # Show cache info
                info = manager.get_cache_info()
                if 'playwright' in info['packages']:
                    browsers = info['packages']['playwright'].get('browsers', [])
                    console.print(f"[dim]Installed browsers: {', '.join(browsers)}[/dim]")
            else:
                progress.update(task, description="✗ Installation failed")
                console.print("[red]✗ Failed to install Playwright[/red]")
                raise click.Abort()


@cache_group.command(name="info")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory"
)
def show_cache_info(cache_dir: Path | None):
    """Show cache information and statistics."""
    from nlp2cmd.utils.external_cache import ExternalCacheManager
    
    manager = ExternalCacheManager(cache_dir)
    info = manager.get_cache_info()
    
    # Overview panel
    overview_text = f"""
Cache Directory: {info['cache_dir']}
Total Size: {info['total_size'] / (1024*1024):.1f} MB
Cached Packages: {len(info['packages'])}
    """.strip()
    
    console.print(Panel(overview_text, title="Cache Overview", border_style="cyan"))
    
    # Package details
    if info['packages']:
        table = Table(title="Cached Packages")
        table.add_column("Package", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Size/Info", style="dim")
        
        for package, pkg_info in info['packages'].items():
            status = "✓ Cached" if pkg_info.get('browsers_cached', False) else "✗ Not cached"
            
            # Get size info
            size_info = ""
            if 'browsers' in pkg_info:
                browsers = pkg_info['browsers']
                size_info = f"Browsers: {', '.join(browsers)}"
            
            table.add_row(package, status, size_info)
        
        console.print(table)
    else:
        console.print("[yellow]No packages cached[/yellow]")


@cache_group.command(name="check")
@click.option(
    "--package",
    type=click.Choice(['playwright']),
    help="Check specific package"
)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory"
)
def check_cache(package: str | None, cache_dir: Path | None):
    """Check if packages are cached."""
    from nlp2cmd.utils.external_cache import ExternalCacheManager
    
    manager = ExternalCacheManager(cache_dir)
    
    if package == 'playwright' or not package:
        if manager.is_playwright_cached():
            console.print("[green]✓ Playwright browsers are cached[/green]")
            
            # Show browser details
            info = manager.get_cache_info()
            if 'playwright' in info['packages']:
                browsers = info['packages']['playwright'].get('browsers', [])
                console.print(f"[dim]Available: {', '.join(browsers)}[/dim]")
        else:
            console.print("[red]✗ Playwright browsers not cached[/red]")
            console.print("[dim]Run 'nlp2cmd cache install' to fix this[/dim]")


@cache_group.command(name="clear")
@click.option(
    "--package",
    type=click.Choice(['playwright']),
    help="Clear specific package cache"
)
@click.option(
    "--all",
    "clear_all",
    is_flag=True,
    help="Clear all cache"
)
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory"
)
@click.confirmation_option(
    prompt="Are you sure you want to clear cache?",
    help="Confirm cache clearing"
)
def clear_cache(package: str | None, clear_all: bool, cache_dir: Path | None):
    """Clear cached packages."""
    from nlp2cmd.utils.external_cache import ExternalCacheManager
    
    manager = ExternalCacheManager(cache_dir)
    
    target = package or ('all' if clear_all else None)
    
    console.print(f"[cyan]Clearing cache: {target or 'all'}[/cyan]")
    
    if manager.clear_cache(target):
        console.print("[green]✓ Cache cleared successfully[/green]")
    else:
        console.print("[red]✗ Failed to clear cache[/red]")
        raise click.Abort()


@cache_group.command(name="auto-setup")
@click.option(
    "--cache-dir",
    type=click.Path(path_type=Path),
    help="Custom cache directory"
)
def auto_setup(cache_dir: Path | None):
    """Automatically setup and install if needed."""
    from nlp2cmd.utils.external_cache import ExternalCacheManager
    
    console.print("[cyan]Auto-setting up external dependencies...[/cyan]")
    
    manager = ExternalCacheManager(cache_dir)
    
    # Setup environment
    if not manager.setup_environment():
        console.print("[red]✗ Failed to setup environment[/red]")
        raise click.Abort()
    
    # Check if Playwright is cached
    if not manager.is_playwright_cached():
        console.print("[yellow]Playwright browsers not cached, installing...[/yellow]")
        
        if manager.install_playwright_if_needed():
            console.print("[green]✓ Auto-setup complete[/green]")
        else:
            console.print("[red]✗ Auto-install failed[/red]")
            raise click.Abort()
    else:
        console.print("[green]✓ Everything already cached and ready[/green]")
    
    # Show final status
    info = manager.get_cache_info()
    console.print(f"[dim]Cache directory: {info['cache_dir']}[/dim]")
    console.print(f"[dim]Total size: {info['total_size'] / (1024*1024):.1f} MB[/dim]")
