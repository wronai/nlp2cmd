#!/usr/bin/env python3
"""
Restore System from Backup
Restores the original NLP2CMD system from backups
"""

import shutil
import sys
from pathlib import Path

def restore_core():
    """Restore core.py from backup"""
    print("🔧 Restoring core.py...")
    
    core_backup = Path("src/nlp2cmd/core_backup.py")
    core_current = Path("src/nlp2cmd/core.py")
    
    if core_backup.exists():
        shutil.copy2(core_backup, core_current)
        print("✅ Core.py restored from backup")
        return True
    else:
        print("❌ Core backup not found")
        return False

def restore_adapters():
    """Restore adapters from backups"""
    print("🔧 Restoring adapters...")
    
    adapters = [
        "src/nlp2cmd/adapters/shell.py",
        "src/nlp2cmd/adapters/sql.py", 
        "src/nlp2cmd/adapters/docker.py",
        "src/nlp2cmd/adapters/kubernetes.py"
    ]
    
    success_count = 0
    
    for adapter in adapters:
        adapter_path = Path(adapter)
        backup_path = Path(str(adapter_path).replace('.py', '_backup.py'))
        
        if Path(backup_path).exists():
            shutil.copy2(backup_path, adapter_path)
            print(f"✅ {adapter} restored from backup")
            success_count += 1
        else:
            print(f"❌ {adapter} backup not found")
    
    return success_count == len(adapters)

def verify_restoration():
    """Verify system restoration"""
    print("🔍 Verifying restoration...")
    
    try:
        # Test basic functionality
        import subprocess
        result = subprocess.run(
            [sys.executable, "-c", "from src.nlp2cmd.core import NLP2CMD; print('Core import successful')"],
            capture_output=True,
            text=True,
            timeout=10,
            cwd=Path(__file__).parent
        )
        
        if result.returncode == 0:
            print("✅ Core system restored successfully")
            return True
        else:
            print(f"❌ Core restoration failed: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Restoration verification failed: {e}")
        return False

def main():
    """Main restoration function"""
    print("🔄 RESTORING NLP2CMD SYSTEM")
    print("=" * 60)
    
    # Restore core
    core_success = restore_core()
    
    # Restore adapters
    adapters_success = restore_adapters()
    
    # Verify restoration
    verification_success = verify_restoration()
    
    print("\n" + "=" * 60)
    print("🎯 RESTORATION RESULTS")
    print("=" * 60)
    
    print(f"Core restoration: {'✅ Success' if core_success else '❌ Failed'}")
    print(f"Adapters restoration: {'✅ Success' if adapters_success else '❌ Failed'}")
    print(f"Verification: {'✅ Passed' if verification_success else '❌ Failed'}")
    
    if core_success and adapters_success and verification_success:
        print("\n🎉 System restored successfully!")
        print("NLP2CMD is back to original state")
        print("\nNext steps:")
        print("1. Test basic functionality")
        print("2. Run original comprehensive test suite")
        print("3. Plan new integration approach")
    else:
        print("\n⚠️  Restoration incomplete")
        print("Please check the errors above")
    
    return core_success and adapters_success and verification_success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
