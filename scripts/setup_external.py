#!/usr/bin/env python3
"""
Setup script for nlp2cmd external dependencies.
Configures cache and installs required packages.
"""

import sys
import os
from pathlib import Path


def main():
    """Setup external dependencies cache."""
    print("🚀 Setting up nlp2cmd external dependencies...")
    
    try:
        from nlp2cmd.utils.external_cache import ExternalCacheManager
        
        # Create cache manager
        manager = ExternalCacheManager()
        print(f"📁 Cache directory: {manager.cache_dir}")
        
        # Setup environment
        if manager.setup_environment():
            print("✅ Environment configured")
        else:
            print("❌ Failed to configure environment")
            return 1
        
        # Check if Playwright is cached
        if manager.is_playwright_cached():
            print("✅ Playwright browsers already cached")
        else:
            print("📦 Installing Playwright browsers...")
            if manager.install_playwright_if_needed():
                print("✅ Playwright browsers installed")
            else:
                print("❌ Failed to install Playwright")
                return 1
        
        # Show final info
        info = manager.get_cache_info()
        print(f"\n📊 Setup complete!")
        print(f"   Cache size: {info['total_size'] / (1024*1024):.1f} MB")
        print(f"   Location: {info['cache_dir']}")
        
        if 'playwright' in info['packages']:
            browsers = info['packages']['playwright'].get('browsers', [])
            print(f"   Browsers: {', '.join(browsers)}")
        
        return 0
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        print("Make sure nlp2cmd is installed: pip install -e .")
        return 1
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
