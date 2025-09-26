#!/usr/bin/env python3
"""
Pre-migration safety checker
Run this before any migration to ensure everything is safe.
"""

import os
import sys
import subprocess
from pathlib import Path
from datetime import datetime

def check_git_status(project_root):
    """Check if git repository is in a safe state."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"], 
            cwd=project_root, 
            capture_output=True, 
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return False, "Not a git repository or git not available"
        
        if result.stdout.strip():
            return False, f"Uncommitted changes found:\n{result.stdout}"
        
        return True, "Git repository is clean"
        
    except subprocess.TimeoutExpired:
        return False, "Git command timed out"
    except Exception as e:
        return False, f"Git check failed: {e}"

def check_important_files(project_root):
    """Check that important files exist."""
    important_files = [
        "updated_compliance_system.py",
        "src/api/main.py",
        "src/ml/models/legal_bert.py",
        "requirements.txt"
    ]
    
    found = []
    missing = []
    
    for file_path in important_files:
        full_path = project_root / file_path
        if full_path.exists():
            found.append(file_path)
        else:
            missing.append(file_path)
    
    return found, missing

def check_disk_space(project_root):
    """Check available disk space."""
    try:
        import shutil
        total, used, free = shutil.disk_usage(project_root)
        free_gb = free / (1024**3)
        return free_gb, free_gb > 1.0  # Need at least 1GB free
    except:
        return 0, False

def main():
    project_root = Path.cwd()
    
    print("PRE-MIGRATION SAFETY CHECK")
    print("=" * 40)
    print(f"Project: {project_root}")
    print(f"Time: {datetime.now()}")
    print()
    
    all_good = True
    
    # Check 1: Git status
    git_ok, git_msg = check_git_status(project_root)
    if git_ok:
        print("✅ Git: " + git_msg)
    else:
        print("⚠️  Git: " + git_msg)
        print("   Recommendation: Commit your changes first")
        all_good = False
    
    # Check 2: Important files
    found_files, missing_files = check_important_files(project_root)
    print(f"✅ Found {len(found_files)} important files:")
    for f in found_files:
        print(f"   • {f}")
    
    if missing_files:
        print(f"⚠️  Missing {len(missing_files)} files:")
        for f in missing_files:
            print(f"   • {f}")
    
    # Check 3: Disk space
    free_space, space_ok = check_disk_space(project_root)
    if space_ok:
        print(f"✅ Disk space: {free_space:.2f}GB free")
    else:
        print(f"❌ Disk space: Only {free_space:.2f}GB free (need at least 1GB)")
        all_good = False
    
    # Check 4: Write permissions
    try:
        test_file = project_root / "test_write.tmp"
        test_file.write_text("test")
        test_file.unlink()
        print("✅ Write permissions: OK")
    except Exception as e:
        print(f"❌ Write permissions: Failed ({e})")
        all_good = False
    
    # Check 5: Python environment
    missing_packages = []
    try:
        import fastapi
    except ImportError:
        missing_packages.append("fastapi")
    
    try:
        import pydantic
    except ImportError:
        missing_packages.append("pydantic")
    
    if missing_packages:
        print(f"⚠️  Python packages: Missing {', '.join(missing_packages)}")
        print("   Run: pip install " + " ".join(missing_packages))
    else:
        print("✅ Python packages: FastAPI and Pydantic available")
    
    print()
    print("=" * 40)
    
    if all_good:
        print("🎉 ALL CHECKS PASSED!")
        print("Your project is ready for migration.")
        print()
        print("Next steps:")
        print("1. python migrate_structure_safe.py --dry-run    # Preview changes")
        print("2. python migrate_structure_safe.py --migrate    # Perform migration")
    else:
        print("⚠️  SOME ISSUES FOUND")
        print("Please fix the issues above before proceeding with migration.")
        print()
        print("You can still preview what migration would do:")
        print("python migrate_structure_safe.py --dry-run")
    
    return all_good

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)