#!/usr/bin/env python3
"""Refactor remaining _prepare_shell_entities logic in TemplateGenerator."""

from __future__ import annotations

from typing import Any, Callable, Dict


def _apply_shell_backup_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply backup-related defaults."""
    backup_handlers = {
        'backup_create': self._shell_intent_backup_create,
        'backup_copy': self._shell_intent_backup_copy,
        'backup_restore': self._shell_intent_backup_restore,
        'backup_integrity': self._shell_intent_backup_integrity,
        'backup_status': self._shell_intent_backup_path,
        'backup_cleanup': self._shell_intent_backup_path,
        'backup_size': self._shell_intent_backup_size,
    }
    
    handler = backup_handlers.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_system_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply system-related defaults."""
    system_handlers = {
        'system_logs': lambda e, r: self._shell_intent_system_logs(r),
        'system_reboot': lambda e, r: result.setdefault('force', False),
        'system_shutdown': lambda e, r: result.setdefault('delay', 'now'),
        'system_info': lambda e, r: result.setdefault('format', 'human'),
    }
    
    handler = system_handlers.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_dev_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply development-related defaults."""
    dev_handlers = {
        'dev_lint': lambda e, r: self._shell_intent_dev_lint(r),
        'dev_logs': lambda e, r: self._shell_intent_dev_logs(r),
        'dev_debug': lambda e, r: self._shell_intent_dev_debug(r),
        'dev_docs': lambda e, r: self._shell_intent_dev_docs(r),
        'dev_test': lambda e, r: result.setdefault('test_path', '.'),
        'dev_build': lambda e, r: result.setdefault('build_args', ''),
    }
    
    handler = dev_handlers.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_security_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply security-related defaults."""
    security_handlers = {
        'security_permissions': self._shell_intent_security_permissions,
        'security_scan': lambda e, r: result.setdefault('target', '.'),
        'security_audit': lambda e, r: result.setdefault('output', 'json'),
        'security_firewall': lambda e, r: result.setdefault('action', 'status'),
    }
    
    handler = security_handlers.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_text_search_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply text search defaults."""
    text_handlers = {
        'text_search_errors': lambda e, r: self._shell_intent_text_search_errors(r),
        'text_search_pattern': lambda e, r: result.setdefault('pattern', ''),
        'text_replace': lambda e, r: result.setdefault('replacement', ''),
        'text_count': lambda e, r: result.setdefault('unique', False),
    }
    
    handler = text_handlers.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_network_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply network-related defaults."""
    network_handlers = {
        'network_ping': lambda e, r: self._shell_intent_network_ping(r),
        'network_lsof': lambda e, r: self._shell_intent_network_lsof(r),
        'network_scan': lambda e, r: self._shell_intent_network_scan(r),
        'network_speed': lambda e, r: self._shell_intent_network_speed(r),
        'network_connections': lambda e, r: result.setdefault('state', 'established'),
    }
    
    handler = network_handlers.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_disk_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply disk-related defaults."""
    disk_handlers = {
        'disk_health': lambda e, r: self._shell_intent_disk_device(r),
        'disk_usage': lambda e, r: result.setdefault('path', '.'),
        'disk_free': lambda e, r: result.setdefault('path', '.'),
        'disk_defrag': lambda e, r: self._shell_intent_disk_device(r),
        'disk_cleanup': lambda e, r: result.setdefault('target', '/tmp'),
    }
    
    handler = disk_handlers.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_process_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply process-related defaults."""
    process_handlers = {
        'process_kill': lambda e, r: self._shell_intent_process_kill(r),
        'process_background': lambda e, r: self._shell_intent_process_background(r),
        'process_script': self._shell_intent_process_script,
        'process_user': self._shell_intent_process_user,
        'process_monitor': lambda e, r: result.setdefault('interval', '1s'),
        'process_tree': lambda e, r: result.setdefault('pid', 'self'),
    }
    
    handler = process_handlers.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_service_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply service-related defaults."""
    service_intents = {
        'service_start': self._shell_intent_service,
        'service_stop': self._shell_intent_service,
        'service_restart': self._shell_intent_service,
        'service_status': self._shell_intent_service,
        'service_enable': self._shell_intent_service,
        'service_disable': self._shell_intent_service,
        'service_logs': lambda e, r: result.setdefault('lines', '50'),
    }
    
    handler = service_intents.get(intent)
    if handler:
        handler(entities, result)


def _apply_shell_browser_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
    """Apply browser-related defaults."""
    if intent in ('open_url', 'open_browser', 'browse'):
        self._shell_intent_open_url(entities, result)
        return
    
    browser_handlers = {
        'search_web': self._shell_intent_search_web,
        'browser_history': lambda e, r: result.setdefault('limit', '20'),
        'browser_bookmarks': lambda e, r: result.setdefault('category', 'all'),
    }
    
    handler = browser_handlers.get(intent)
    if handler:
        handler(entities, result)


# Apply the refactored methods to TemplateGenerator
def apply_refactor_to_template_generator():
    """Apply the refactored _apply_shell_intent_specific_defaults method."""
    from nlp2cmd.generation.templates import TemplateGenerator
    
    # Store original method
    original_apply_shell_intent_specific_defaults = TemplateGenerator._apply_shell_intent_specific_defaults
    
    def _apply_shell_intent_specific_defaults(self, intent: str, entities: dict[str, Any], result: dict[str, Any]) -> None:
        """Refactored intent-specific defaults with reduced complexity."""
        # File operations
        file_handlers = {
            'file_search': self._shell_intent_file_search,
            'file_content': self._shell_intent_file_content,
            'file_tail': self._shell_intent_file_tail,
            'file_size': self._shell_intent_file_size,
            'file_rename': self._shell_intent_file_rename,
            'file_delete_all': self._shell_intent_file_delete_all,
            'dir_create': self._shell_intent_dir_create,
            'remove_all': self._shell_intent_remove_all,
            'file_operation': self._shell_intent_file_operation,
        }
        
        # Check file handlers first
        handler = file_handlers.get(intent)
        if handler:
            handler(entities, result)
            return
        
        # Dispatch to category-specific handlers
        category_handlers = [
            (_apply_shell_backup_defaults, 'backup'),
            (_apply_shell_system_defaults, 'system'),
            (_apply_shell_dev_defaults, 'dev'),
            (_apply_shell_security_defaults, 'security'),
            (_apply_shell_text_search_defaults, 'text_search'),
            (_apply_shell_network_defaults, 'network'),
            (_apply_shell_disk_defaults, 'disk'),
            (_apply_shell_process_defaults, 'process'),
            (_apply_shell_service_defaults, 'service'),
            (_apply_shell_browser_defaults, 'browser'),
        ]
        
        for handler_func, prefix in category_handlers:
            if intent.startswith(prefix):
                handler_func(self, intent, entities, result)
                return
    
    # Replace the method
    TemplateGenerator._apply_shell_intent_specific_defaults = _apply_shell_intent_specific_defaults
    
    # Add helper methods
    TemplateGenerator._apply_shell_backup_defaults = _apply_shell_backup_defaults
    TemplateGenerator._apply_shell_system_defaults = _apply_shell_system_defaults
    TemplateGenerator._apply_shell_dev_defaults = _apply_shell_dev_defaults
    TemplateGenerator._apply_shell_security_defaults = _apply_shell_security_defaults
    TemplateGenerator._apply_shell_text_search_defaults = _apply_shell_text_search_defaults
    TemplateGenerator._apply_shell_network_defaults = _apply_shell_network_defaults
    TemplateGenerator._apply_shell_disk_defaults = _apply_shell_disk_defaults
    TemplateGenerator._apply_shell_process_defaults = _apply_shell_process_defaults
    TemplateGenerator._apply_shell_service_defaults = _apply_shell_service_defaults
    TemplateGenerator._apply_shell_browser_defaults = _apply_shell_browser_defaults
    
    return original_apply_shell_intent_specific_defaults


if __name__ == "__main__":
    # Apply the refactor
    original = apply_refactor_to_template_generator()
    print("✅ Refactored _apply_shell_intent_specific_defaults to reduce complexity")
    print(f"Original method: {original.__name__ if hasattr(original, '__name__') else 'method'}")
