"""
Service CLI commands for NLP2CMD.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Optional

try:
    import click
except ImportError:
    click = None

from . import NLP2CMDService, ServiceConfig, create_service_config_from_args


def add_service_command(main_group):
    """Add service command to the main CLI group."""
    if click is None:
        return
    
    @main_group.command()
    @click.option("--host", default="0.0.0.0", help="Host to bind the service to")
    @click.option("--port", default=8000, type=int, help="Port to bind the service to")
    @click.option("--debug", is_flag=True, help="Enable debug mode")
    @click.option("--log-level", default="info", 
                  type=click.Choice(["debug", "info", "warning", "error", "critical"]),
                  help="Log level")
    @click.option("--cors-origins", default="*", help="CORS origins (comma-separated)")
    @click.option("--max-workers", default=4, type=int, help="Maximum number of workers")
    @click.option("--auto-execute", is_flag=True, help="Auto-execute generated commands")
    @click.option("--session-timeout", default=3600, type=int, help="Session timeout in seconds")
    @click.option("--save-env", is_flag=True, help="Save configuration to .env file")
    @click.option("--env-file", default=None, help="Path to .env file (default: .env)")
    @click.option("--workers", default=1, type=int, help="Number of uvicorn workers")
    @click.option("--reload", is_flag=True, help="Enable auto-reload for development")
    def service(
        host: str,
        port: int,
        debug: bool,
        log_level: str,
        cors_origins: str,
        max_workers: int,
        auto_execute: bool,
        session_timeout: int,
        save_env: bool,
        env_file: Optional[str],
        workers: int,
        reload: bool
    ):
        """Start NLP2CMD as an HTTP API service."""
        
        # Create configuration from arguments
        config = create_service_config_from_args(
            host=host,
            port=port,
            debug=debug,
            log_level=log_level,
            cors_origins=cors_origins,
            max_workers=max_workers,
            auto_execute=auto_execute,
            session_timeout=session_timeout,
            save_env=save_env,
            env_file=env_file
        )
        
        # Set environment variables for multi-worker or reload mode
        if workers > 1 or reload:
            os.environ["NLP2CMD_HOST"] = host
            os.environ["NLP2CMD_PORT"] = str(port)
            os.environ["NLP2CMD_DEBUG"] = str(debug).lower()
            os.environ["NLP2CMD_LOG_LEVEL"] = log_level
            os.environ["NLP2CMD_CORS_ORIGINS"] = cors_origins
            os.environ["NLP2CMD_MAX_WORKERS"] = str(max_workers)
            os.environ["NLP2CMD_AUTO_EXECUTE"] = str(auto_execute).lower()
            os.environ["NLP2CMD_SESSION_TIMEOUT"] = str(session_timeout)
        
        # Create and run service
        service_instance = NLP2CMDService(config)
        
        try:
            service_instance.run(
                host=host,
                port=port,
                workers=workers,
                reload=reload
            )
        except KeyboardInterrupt:
            print("\nService stopped by user")
            sys.exit(0)
        except Exception as e:
            print(f"Error starting service: {e}")
            sys.exit(1)
    
    @main_group.command()
    @click.option("--host", default="0.0.0.0", help="Host to bind the service to")
    @click.option("--port", default=8000, type=int, help="Port to bind the service to")
    @click.option("--debug", is_flag=True, help="Enable debug mode")
    @click.option("--log-level", default="info", 
                  type=click.Choice(["debug", "info", "warning", "error", "critical"]),
                  help="Log level")
    @click.option("--cors-origins", default="*", help="CORS origins (comma-separated)")
    @click.option("--max-workers", default=4, type=int, help="Maximum number of workers")
    @click.option("--auto-execute", is_flag=True, help="Auto-execute generated commands")
    @click.option("--session-timeout", default=3600, type=int, help="Session timeout in seconds")
    @click.option("--env-file", default=".env", help="Path to .env file")
    def config_service(
        host: str,
        port: int,
        debug: bool,
        log_level: str,
        cors_origins: str,
        max_workers: int,
        auto_execute: bool,
        session_timeout: int,
        env_file: str
    ):
        """Configure and save service settings to .env file."""
        
        config = create_service_config_from_args(
            host=host,
            port=port,
            debug=debug,
            log_level=log_level,
            cors_origins=cors_origins,
            max_workers=max_workers,
            auto_execute=auto_execute,
            session_timeout=session_timeout,
            save_env=True,
            env_file=env_file
        )
        
        print(f"Service configuration saved to {env_file}")
        print("Current configuration:")
        for key, value in config.to_dict().items():
            print(f"  {key}: {value}")
    
    return main_group
