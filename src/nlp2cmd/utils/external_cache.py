#!/usr/bin/env python3
"""
External dependencies cache manager for nlp2cmd.
Optimizes installation and usage of external packages like Playwright.
"""

import os
import sys
import json
import shutil
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Any
import hashlib


class ExternalCacheManager:
    """Manages caching of external dependencies like Playwright browsers."""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        if cache_dir is None:
            # Default cache in project root directory
            # Go from src/nlp2cmd/utils/external_cache.py to project root
            cache_dir = Path(__file__).parent.parent.parent.parent / ".cache" / "external"
        
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Cache manifest file
        self.manifest_file = self.cache_dir / "cache_manifest.json"
        self.manifest = self._load_manifest()
        
        # Environment variable for Playwright cache
        self.playwright_cache_dir = self.cache_dir / "playwright"
        self.playwright_browsers_dir = self.playwright_cache_dir / "browsers"
    
    def _load_manifest(self) -> Dict[str, Any]:
        """Load cache manifest from file."""
        if self.manifest_file.exists():
            try:
                with open(self.manifest_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {}
    
    def _save_manifest(self):
        """Save cache manifest to file."""
        try:
            with open(self.manifest_file, 'w') as f:
                json.dump(self.manifest, f, indent=2)
        except IOError:
            pass
    
    def _get_package_hash(self, package_name: str, version: Optional[str] = None) -> str:
        """Get hash for package identification."""
        import importlib.util
        
        # Try to get installed package version
        if version is None:
            try:
                spec = importlib.util.find_spec(package_name)
                if spec and spec.origin:
                    # Use file path and modification time for hash
                    file_path = Path(spec.origin)
                    if file_path.exists():
                        content = f"{package_name}:{file_path}:{file_path.stat().st_mtime}"
                        return hashlib.md5(content.encode()).hexdigest()
            except (ImportError, AttributeError):
                pass
        
        # Fallback to package name only
        return hashlib.md5(f"{package_name}:{version or 'unknown'}".encode()).hexdigest()
    
    def setup_playwright_cache(self) -> bool:
        """Setup Playwright to use local cache directory."""
        try:
            # Create cache directories
            self.playwright_browsers_dir.mkdir(parents=True, exist_ok=True)
            
            # Set environment variables for Playwright cache
            os.environ['PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)
            
            # Also set MS_PLAYWRIGHT cache (for newer versions)
            os.environ['MS_PLAYWRIGHT_BROWSERS_PATH'] = str(self.playwright_browsers_dir)
            
            print(f"Playwright cache configured: {self.playwright_browsers_dir}")
            
            # Update manifest if browsers are already cached
            if self.is_playwright_cached():
                self.manifest['playwright'] = {
                    'installed_at': str(Path.cwd()),
                    'cache_dir': str(self.playwright_browsers_dir),
                    'browsers': self._get_installed_browsers()
                }
                self._save_manifest()
            
            return True
            
        except Exception as e:
            print(f"Failed to setup Playwright cache: {e}")
            return False
    
    def is_playwright_cached(self) -> bool:
        """Check if Playwright browsers are cached."""
        if not self.playwright_browsers_dir.exists():
            return False
        
        # Check for any browser directories (including versioned ones)
        if not any(self.playwright_browsers_dir.iterdir()):
            return False
        
        # Look for common browser prefixes
        browser_prefixes = ['chromium', 'firefox', 'webkit']
        for item in self.playwright_browsers_dir.iterdir():
            if item.is_dir():
                for prefix in browser_prefixes:
                    if item.name.startswith(prefix):
                        return True
        
        return False
    
    def install_playwright_if_needed(self, force: bool = False) -> bool:
        """Install Playwright browsers if not cached or force=True."""
        if not force and self.is_playwright_cached():
            print("✓ Playwright browsers already cached")
            self.setup_playwright_cache()
            return True
        
        print("Installing Playwright browsers to cache...")
        
        # Setup cache first
        if not self.setup_playwright_cache():
            return False
        
        try:
            # Install Playwright browsers
            result = subprocess.run(
                [sys.executable, "-m", "playwright", "install"],
                capture_output=True,
                text=True,
                cwd=Path.cwd()
            )
            
            if result.returncode == 0:
                print("✓ Playwright browsers installed successfully")
                
                # Update manifest
                self.manifest['playwright'] = {
                    'installed_at': str(Path.cwd()),
                    'cache_dir': str(self.playwright_browsers_dir),
                    'browsers': self._get_installed_browsers()
                }
                self._save_manifest()
                
                return True
            else:
                print(f"✗ Playwright installation failed: {result.stderr}")
                return False
                
        except Exception as e:
            print(f"✗ Failed to install Playwright: {e}")
            return False
    
    def _get_installed_browsers(self) -> List[str]:
        """Get list of installed browsers."""
        browsers = []
        if self.playwright_browsers_dir.exists():
            for item in self.playwright_browsers_dir.iterdir():
                if item.is_dir():
                    browsers.append(item.name)
        return browsers
    
    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about cached packages."""
        info = {
            'cache_dir': str(self.cache_dir),
            'total_size': self._get_cache_size(),
            'packages': {}
        }
        
        # Playwright info
        if 'playwright' in self.manifest:
            playwright_info = self.manifest['playwright'].copy()
            playwright_info['browsers_cached'] = self.is_playwright_cached()
            playwright_info['cache_dir'] = str(self.playwright_browsers_dir)
            info['packages']['playwright'] = playwright_info
        
        return info
    
    def _get_cache_size(self) -> int:
        """Get total cache size in bytes."""
        total_size = 0
        try:
            for item in self.cache_dir.rglob('*'):
                if item.is_file():
                    total_size += item.stat().st_size
        except (OSError, PermissionError):
            pass
        return total_size
    
    def clear_cache(self, package: Optional[str] = None) -> bool:
        """Clear cache for specific package or all."""
        try:
            if package == 'playwright':
                if self.playwright_cache_dir.exists():
                    shutil.rmtree(self.playwright_cache_dir)
                    print("✓ Playwright cache cleared")
                if 'playwright' in self.manifest:
                    del self.manifest['playwright']
                    self._save_manifest()
            elif package is None:
                # Clear all cache
                if self.cache_dir.exists():
                    shutil.rmtree(self.cache_dir)
                    self.cache_dir.mkdir(parents=True, exist_ok=True)
                    print("✓ All external cache cleared")
                self.manifest = {}
                self._save_manifest()
            else:
                print(f"Unknown package: {package}")
                return False
            
            return True
            
        except Exception as e:
            print(f"✗ Failed to clear cache: {e}")
            return False
    
    def setup_environment(self) -> bool:
        """Setup environment variables for cached packages."""
        success = True
        
        # Setup Playwright
        if not self.setup_playwright_cache():
            success = False
        
        return success


def main():
    """CLI interface for cache manager."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Manage external dependencies cache")
    parser.add_argument(
        'action',
        choices=['setup', 'install', 'info', 'clear', 'check'],
        help='Action to perform'
    )
    parser.add_argument(
        '--package',
        choices=['playwright'],
        help='Specific package to manage'
    )
    parser.add_argument(
        '--force',
        action='store_true',
        help='Force action (e.g., reinstall)'
    )
    parser.add_argument(
        '--cache-dir',
        type=Path,
        help='Custom cache directory'
    )
    
    args = parser.parse_args()
    
    manager = ExternalCacheManager(args.cache_dir)
    
    if args.action == 'setup':
        if manager.setup_environment():
            print("✓ Environment setup complete")
        else:
            print("✗ Environment setup failed")
            sys.exit(1)
    
    elif args.action == 'install':
        if args.package == 'playwright' or not args.package:
            if manager.install_playwright_if_needed(force=args.force):
                print("✓ Playwright installation complete")
            else:
                print("✗ Playwright installation failed")
                sys.exit(1)
        else:
            print(f"Unknown package: {args.package}")
            sys.exit(1)
    
    elif args.action == 'info':
        info = manager.get_cache_info()
        print(f"Cache directory: {info['cache_dir']}")
        print(f"Total size: {info['total_size'] / (1024*1024):.1f} MB")
        
        for package, pkg_info in info['packages'].items():
            print(f"\n{package.upper()}:")
            for key, value in pkg_info.items():
                print(f"  {key}: {value}")
    
    elif args.action == 'check':
        if args.package == 'playwright' or not args.package:
            if manager.is_playwright_cached():
                print("✓ Playwright browsers are cached")
            else:
                print("✗ Playwright browsers not cached")
                sys.exit(1)
    
    elif args.action == 'clear':
        if manager.clear_cache(args.package):
            print("✓ Cache cleared")
        else:
            print("✗ Cache clear failed")
            sys.exit(1)


if __name__ == '__main__':
    main()
