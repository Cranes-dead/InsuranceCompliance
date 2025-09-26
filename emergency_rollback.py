#!/usr/bin/env python3
"""
Emergency rollback script
Use this if migration goes wrong and you need to quickly restore.
"""

import shutil
import sys
from pathlib import Path
from datetime import datetime

def emergency_rollback():
    """Quick rollback using backup directory."""
    project_root = Path.cwd()
    backup_dir = project_root / "backup_pre_migration"
    
    print("🚨 EMERGENCY ROLLBACK")
    print("=" * 30)
    
    if not backup_dir.exists():
        print("❌ No backup found!")
        print("Backup directory not found:", backup_dir)
        return False
    
    print(f"📁 Found backup: {backup_dir}")
    print(f"⏰ Timestamp: {datetime.now()}")
    
    # Confirm
    response = input("\n⚠️  This will restore ALL files from backup. Continue? (yes/no): ")
    if response.lower() not in ['yes', 'y']:
        print("Rollback cancelled.")
        return False
    
    try:
        # Restore each item from backup
        restored_count = 0
        for item in backup_dir.iterdir():
            if item.name.startswith('.') or item.name == "backup_manifest.json":
                continue
            
            target = project_root / item.name
            print(f"Restoring: {item.name}")
            
            if target.exists():
                if target.is_dir():
                    shutil.rmtree(target)
                else:
                    target.unlink()
            
            if item.is_dir():
                shutil.copytree(item, target)
            else:
                shutil.copy2(item, target)
            
            restored_count += 1
        
        print(f"\n✅ Rollback completed!")
        print(f"📊 Restored {restored_count} items")
        print("\n⚠️  Remember to:")
        print("1. Restart any running services")
        print("2. Check that everything works as expected") 
        print("3. Consider what went wrong before trying migration again")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Rollback failed: {e}")
        print("You may need to manually restore files from:", backup_dir)
        return False

if __name__ == "__main__":
    success = emergency_rollback()
    sys.exit(0 if success else 1)