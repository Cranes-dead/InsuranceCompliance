#!/usr/bin/env python3
"""
SAFE Migration script with validation, dry-run, and rollback capabilities.
This script helps move        # Check available disk space
        try:
            import shutil as disk_util
            total, used, free = disk_util.disk_usage(self.project_root)
            free_gb = free / (1024**3)
            if free_gb < 1:  # Less than 1GB free
                self.validation_errors.append(f"Low disk space: {free_gb:.2f}GB free")
                valid = False
            else:
                print_colored(f"✅ Disk space OK: {free_gb:.2f}GB free", GREEN)
        except Exception as e:
            self.validation_warnings.append(f"Could not check disk space: {e}")p        # Check for Git repository status
        git_dir = self.project_root / ".git"
        if git_dir.exists():
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "status", "--porcelain"], 
                    cwd=self.project_root, 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                if result.returncode == 0:
                    if result.stdout.strip():
                        self.validation_warnings.append("Git repository has uncommitted changes")
                        print_colored("⚠ Git has uncommitted changes - consider committing first", YELLOW)
                    else:
                        print_colored("✅ Git repository is clean", GREEN)
                else:
                    self.validation_warnings.append("Could not check Git status")
            except subprocess.TimeoutExpired:
                self.validation_warnings.append("Git status check timed out")
            except FileNotFoundError:
                self.validation_warnings.append("Git command not found")
            except Exception as e:
                self.validation_warnings.append(f"Could not check Git status: {e}")atically with safety checks.

USAGE:
    python migrate_structure_safe.py --dry-run    # Preview changes without making them
    python migrate_structure_safe.py --validate   # Only validate the current structure
    python migrate_structure_safe.py --migrate    # Perform actual migration (after validation)
    python migrate_structure_safe.py --rollback   # Rollback to backup if something goes wrong
"""

import os
import sys
import shutil
import re
import json
import argparse
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from datetime import datetime

# Color codes for console output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
CYAN = '\033[96m'
ENDC = '\033[0m'

def print_colored(message: str, color: str = ''):
    """Print colored message to console."""
    print(f"{color}{message}{ENDC}")

def print_section(title: str):
    """Print a section header."""
    print_colored(f"\n{'='*60}", BLUE)
    print_colored(f"  {title}", BLUE)
    print_colored(f"{'='*60}", BLUE)

class SafeMigrator:
    """Safe migration tool with validation and rollback capabilities."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = project_root / "backup_pre_migration"
        self.migration_log_file = project_root / "migration_log.json"
        self.migration_log = []
        self.validation_errors = []
        self.validation_warnings = []
        self.dry_run = False
        
        # Define what we expect to find and where to move it
        self.file_mappings = {
            # Source -> Destination
            "updated_compliance_system.py": "app/ml/inference/legacy_compliance_engine.py",
            "src/api/main.py": "api/legacy_main.py",
            "src/api/routes/compliance.py": "api/v1/endpoints/legacy_compliance.py", 
            "src/api/routes/documents.py": "api/v1/endpoints/legacy_documents.py",
            "src/api/models/schemas.py": "app/models/legacy_schemas.py",
            "src/ml/models/legal_bert.py": "app/ml/models/legacy_legal_bert.py",
            "src/processing/parsers/document_parser.py": "app/processing/parsers/legacy_document_parser.py",
            "reclassify_rules.py": "app/ml/inference/legacy_rule_classifier.py",
            "rule_based_classifier.py": "app/ml/models/legacy_rule_classifier.py"
        }
        
        # Critical files that must not be touched
        self.protected_files = [
            ".git",
            "models/",
            "data/",
            "test_samples/",
            ".env",
            "requirements.txt",
            "readme.md"
        ]
        
        # Files to keep as reference but mark as legacy
        self.reference_files = [
            "demo_system.py",
            "simple_training.py", 
            "test_*.py"
        ]
    
    def validate_preconditions(self) -> bool:
        """Validate that the project is ready for migration."""
        print_section("🔍 VALIDATING PROJECT STRUCTURE")
        
        valid = True
        
        # Check if we're in the right directory
        if not (self.project_root / "updated_compliance_system.py").exists():
            self.validation_errors.append("Not in correct project directory - missing updated_compliance_system.py")
            valid = False
        
        # Check for existing new structure conflicts
        new_structure_exists = (self.project_root / "app" / "__init__.py").exists()
        if new_structure_exists:
            self.validation_warnings.append("New app structure already exists - migration may overwrite files")
        
        # Check for required source files
        for source_file, _ in self.file_mappings.items():
            source_path = self.project_root / source_file
            if source_path.exists():
                print_colored(f"✓ Found: {source_file}", GREEN)
            else:
                print_colored(f"⚠ Missing: {source_file}", YELLOW)
                self.validation_warnings.append(f"Source file missing: {source_file}")
        
        # Check for protected files
        for protected in self.protected_files:
            protected_path = self.project_root / protected
            if protected_path.exists():
                print_colored(f"✓ Protected file exists: {protected}", GREEN)
            else:
                print_colored(f"⚠ Protected file missing: {protected}", YELLOW)
        
        # Check write permissions
        try:
            test_file = self.project_root / "test_write_permission.tmp"
            test_file.write_text("test")
            test_file.unlink()
            print_colored("✓ Write permissions OK", GREEN)
        except Exception as e:
            self.validation_errors.append(f"No write permission: {e}")
            valid = False
        
        # Check available disk space
        try:
            import shutil as disk_util
            total, used, free = disk_util.disk_usage(self.project_root)
            free_gb = free / (1024**3)
            if free_gb < 1:  # Less than 1GB free
                self.validation_errors.append(f"Low disk space: {free_gb:.2f}GB free")
                valid = False
            else:
                print_colored(f"✓ Disk space OK: {free_gb:.2f}GB free", GREEN)
        except:
            self.validation_warnings.append("Could not check disk space")
        
        # Check for Git repository status
        git_dir = self.project_root / ".git"
        if git_dir.exists():
            try:
                import subprocess
                result = subprocess.run(
                    ["git", "status", "--porcelain"], 
                    cwd=self.project_root, 
                    capture_output=True, 
                    text=True,
                    timeout=10
                )
                if result.stdout.strip():
                    self.validation_warnings.append("Git repository has uncommitted changes")
                    print_colored("⚠ Git has uncommitted changes - consider committing first", YELLOW)
                else:
                    print_colored("✓ Git repository is clean", GREEN)
            except Exception as e:
                self.validation_warnings.append(f"Could not check Git status: {e}")
        
        # Print validation summary
        print_section("📋 VALIDATION SUMMARY")
        
        if self.validation_errors:
            print_colored("❌ VALIDATION FAILED - Cannot proceed:", RED)
            for error in self.validation_errors:
                print_colored(f"  • {error}", RED)
            valid = False
        
        if self.validation_warnings:
            print_colored("⚠️  WARNINGS:", YELLOW)
            for warning in self.validation_warnings:
                print_colored(f"  • {warning}", YELLOW)
        
        if valid:
            print_colored("✅ All validation checks passed!", GREEN)
        
        return valid
    
    def create_backup(self) -> bool:
        """Create a complete backup of the current state."""
        print_section("💾 CREATING BACKUP")
        
        try:
            if self.backup_dir.exists():
                print_colored(f"Removing existing backup: {self.backup_dir}", YELLOW)
                if not self.dry_run:
                    shutil.rmtree(self.backup_dir)
            
            if not self.dry_run:
                self.backup_dir.mkdir()
            
            # Items to backup
            items_to_backup = [
                "src/",
                "updated_compliance_system.py",
                "reclassify_rules.py", 
                "rule_based_classifier.py",
                "requirements.txt",
                "demo_system.py",
                "simple_training.py"
            ]
            
            total_size = 0
            for item in items_to_backup:
                item_path = self.project_root / item
                if item_path.exists():
                    if not self.dry_run:
                        if item_path.is_dir():
                            shutil.copytree(item_path, self.backup_dir / item)
                        else:
                            shutil.copy2(item_path, self.backup_dir / item)
                        
                        # Calculate size
                        if item_path.is_dir():
                            size = sum(f.stat().st_size for f in item_path.rglob('*') if f.is_file())
                        else:
                            size = item_path.stat().st_size
                        total_size += size
                    
                    print_colored(f"{'[DRY-RUN] ' if self.dry_run else ''}✓ Backed up: {item}", GREEN)
                else:
                    print_colored(f"⚠ Skipped (not found): {item}", YELLOW)
            
            # Create backup manifest
            manifest = {
                "timestamp": datetime.now().isoformat(),
                "project_root": str(self.project_root),
                "total_size_bytes": total_size,
                "items_backed_up": items_to_backup,
                "migration_script_version": "2.0.0"
            }
            
            if not self.dry_run:
                with open(self.backup_dir / "backup_manifest.json", "w") as f:
                    json.dump(manifest, f, indent=2)
            
            print_colored(f"{'[DRY-RUN] ' if self.dry_run else ''}💾 Backup created: {self.backup_dir}", GREEN)
            print_colored(f"{'[DRY-RUN] ' if self.dry_run else ''}📊 Total size: {total_size / (1024*1024):.2f} MB", CYAN)
            
            return True
            
        except Exception as e:
            print_colored(f"❌ Backup failed: {e}", RED)
            return False
    
    def analyze_file_contents(self, file_path: Path) -> Dict:
        """Analyze a Python file to understand its dependencies and structure."""
        if not file_path.exists() or file_path.suffix != '.py':
            return {}
        
        try:
            content = file_path.read_text(encoding='utf-8', errors='ignore')
            
            # Find imports
            imports = re.findall(r'^(?:from\s+[\w.]+\s+)?import\s+[\w.,\s*]+', content, re.MULTILINE)
            
            # Find class definitions
            classes = re.findall(r'^class\s+(\w+)', content, re.MULTILINE)
            
            # Find function definitions
            functions = re.findall(r'^def\s+(\w+)', content, re.MULTILINE)
            
            # Check for sys.path modifications
            has_syspath_hack = 'sys.path.append' in content
            
            # Check for relative imports
            has_relative_imports = 'from .' in content or 'from ..' in content
            
            return {
                "imports": imports,
                "classes": classes,
                "functions": functions,
                "has_syspath_hack": has_syspath_hack,
                "has_relative_imports": has_relative_imports,
                "line_count": len(content.split('\n'))
            }
            
        except Exception as e:
            print_colored(f"⚠ Could not analyze {file_path}: {e}", YELLOW)
            return {}
    
    def preview_migration(self):
        """Show what the migration will do without actually doing it."""
        print_section("🔍 MIGRATION PREVIEW")
        
        self.dry_run = True
        
        print_colored("FILES TO BE MOVED:", BLUE)
        for source, destination in self.file_mappings.items():
            source_path = self.project_root / source
            dest_path = self.project_root / destination
            
            if source_path.exists():
                # Analyze the file
                analysis = self.analyze_file_contents(source_path)
                
                print_colored(f"\n📁 {source} -> {destination}", CYAN)
                print_colored(f"   Size: {source_path.stat().st_size} bytes", "")
                print_colored(f"   Lines: {analysis.get('line_count', 'Unknown')}", "")
                
                if analysis.get('classes'):
                    print_colored(f"   Classes: {', '.join(analysis['classes'])}", "")
                
                if analysis.get('has_syspath_hack'):
                    print_colored(f"   ⚠ Contains sys.path hack (will need fixing)", YELLOW)
                
                if analysis.get('has_relative_imports'):
                    print_colored(f"   ⚠ Has relative imports (will need updating)", YELLOW)
                
                if dest_path.exists():
                    print_colored(f"   ⚠ Destination exists (will be overwritten)", YELLOW)
            else:
                print_colored(f"⚠ {source} (NOT FOUND - will skip)", YELLOW)
        
        print_colored(f"\nPROTECTED FILES (will not be touched):", BLUE)
        for protected in self.protected_files:
            protected_path = self.project_root / protected
            if protected_path.exists():
                print_colored(f"✓ {protected}", GREEN)
        
        # Check what imports need updating
        print_colored(f"\nFILES THAT NEED IMPORT UPDATES:", BLUE)
        python_files = list(self.project_root.rglob("*.py"))
        files_needing_updates = []
        
        for py_file in python_files:
            if any(protected in str(py_file) for protected in ["backup", ".git", "__pycache__"]):
                continue
                
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                if any(pattern in content for pattern in [
                    "from src.", "import src.", "from updated_compliance_system", 
                    "sys.path.append", "from .", "from .."
                ]):
                    files_needing_updates.append(py_file.relative_to(self.project_root))
            except:
                continue
        
        for file_path in files_needing_updates[:10]:  # Show first 10
            print_colored(f"  📝 {file_path}", "")
        
        if len(files_needing_updates) > 10:
            print_colored(f"  ... and {len(files_needing_updates) - 10} more files", YELLOW)
        
        self.dry_run = False
    
    def perform_migration(self) -> bool:
        """Perform the actual migration."""
        print_section("🚀 PERFORMING MIGRATION")
        
        success = True
        migration_steps = []
        
        try:
            # Step 1: Move files
            for source, destination in self.file_mappings.items():
                source_path = self.project_root / source
                dest_path = self.project_root / destination
                
                if not source_path.exists():
                    print_colored(f"⚠ Skipping {source} (not found)", YELLOW)
                    continue
                
                # Ensure destination directory exists
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Copy file (don't move, in case we need to rollback)
                shutil.copy2(source_path, dest_path)
                
                # Add legacy comment at the top
                self._add_legacy_header(dest_path)
                
                migration_steps.append({
                    "action": "copy",
                    "source": str(source_path),
                    "destination": str(dest_path),
                    "timestamp": datetime.now().isoformat()
                })
                
                print_colored(f"✓ Copied: {source} -> {destination}", GREEN)
            
            # Step 2: Update imports in new files
            print_colored("\n📝 Updating imports in migrated files...", BLUE)
            self._update_imports_in_migrated_files()
            
            # Step 3: Create migration report
            self._create_migration_report(migration_steps)
            
            print_colored("✅ Migration completed successfully!", GREEN)
            return True
            
        except Exception as e:
            print_colored(f"❌ Migration failed: {e}", RED)
            return False
    
    def _add_legacy_header(self, file_path: Path):
        """Add a legacy header to migrated files."""
        if not file_path.exists() or file_path.suffix != '.py':
            return
        
        try:
            content = file_path.read_text(encoding='utf-8')
            
            header = f'''"""
LEGACY FILE - Migrated from old structure
Original location: {file_path.name}
Migration date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

⚠️  This file needs manual review and integration with the new structure:
1. Update imports to use new package structure
2. Integrate with new service layer
3. Update configuration usage
4. Add proper error handling
5. Update tests

Remove this header once integration is complete.
"""

'''
            
            # Add header at the top (after shebang if present)
            lines = content.split('\n')
            insert_index = 0
            
            if lines and lines[0].startswith('#!'):
                insert_index = 1
            
            lines.insert(insert_index, header)
            new_content = '\n'.join(lines)
            
            file_path.write_text(new_content, encoding='utf-8')
            
        except Exception as e:
            print_colored(f"⚠ Could not add legacy header to {file_path}: {e}", YELLOW)
    
    def _update_imports_in_migrated_files(self):
        """Update imports in the migrated files."""
        # This is a basic implementation - more sophisticated updates would be manual
        migrated_files = []
        
        for source, destination in self.file_mappings.items():
            dest_path = self.project_root / destination
            if dest_path.exists():
                migrated_files.append(dest_path)
        
        for file_path in migrated_files:
            try:
                content = file_path.read_text(encoding='utf-8')
                original_content = content
                
                # Basic import replacements
                replacements = [
                    (r'from src\.', 'from app.'),
                    (r'import src\.', 'import app.'),
                    (r'sys\.path\.append\([^)]+\)', '# TODO: Remove sys.path hack'),
                ]
                
                for pattern, replacement in replacements:
                    content = re.sub(pattern, replacement, content)
                
                if content != original_content:
                    file_path.write_text(content, encoding='utf-8')
                    print_colored(f"  ✓ Updated imports in {file_path.name}", GREEN)
                    
            except Exception as e:
                print_colored(f"  ⚠ Could not update imports in {file_path}: {e}", YELLOW)
    
    def _create_migration_report(self, migration_steps: List[Dict]):
        """Create a detailed migration report."""
        report = {
            "migration_timestamp": datetime.now().isoformat(),
            "project_root": str(self.project_root),
            "backup_location": str(self.backup_dir),
            "validation_errors": self.validation_errors,
            "validation_warnings": self.validation_warnings,
            "migration_steps": migration_steps,
            "files_migrated": len(migration_steps),
            "next_steps": [
                "Review all files marked with LEGACY header",
                "Update imports throughout the project",
                "Test the new API endpoints", 
                "Update configuration files",
                "Run comprehensive tests"
            ]
        }
        
        # Save as JSON
        with open(self.migration_log_file, "w") as f:
            json.dump(report, f, indent=2)
        
        # Create human-readable report
        report_md = self.project_root / "MIGRATION_REPORT_DETAILED.md"
        with open(report_md, "w") as f:
            f.write(f"""# Migration Report
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Summary
- ✅ Files migrated: {len(migration_steps)}
- 💾 Backup location: `{self.backup_dir}`
- ⚠️  Validation warnings: {len(self.validation_warnings)}

## Files Migrated
""")
            for step in migration_steps:
                f.write(f"- `{step['source']}` → `{step['destination']}`\n")
            
            f.write(f"""
## Next Steps (IMPORTANT!)
1. **Review Legacy Files**: All migrated files have LEGACY headers - review and integrate
2. **Update Imports**: Update import statements throughout the project  
3. **Test API**: Start new API server and test endpoints
4. **Configuration**: Update all configuration to use new structure
5. **Run Tests**: Execute comprehensive test suite

## Rollback Instructions
If something goes wrong, you can rollback:
```powershell
python migrate_structure_safe.py --rollback
```

## Validation Warnings
""")
            for warning in self.validation_warnings:
                f.write(f"- ⚠️ {warning}\n")
        
        print_colored(f"📋 Detailed report created: {report_md}", CYAN)
    
    def rollback_migration(self) -> bool:
        """Rollback the migration using the backup."""
        print_section("🔄 ROLLING BACK MIGRATION")
        
        if not self.backup_dir.exists():
            print_colored("❌ No backup found - cannot rollback", RED)
            return False
        
        try:
            # Read backup manifest
            manifest_file = self.backup_dir / "backup_manifest.json"
            if manifest_file.exists():
                with open(manifest_file) as f:
                    manifest = json.load(f)
                print_colored(f"📋 Found backup from: {manifest['timestamp']}", CYAN)
            
            # Restore files from backup
            for item in self.backup_dir.iterdir():
                if item.name == "backup_manifest.json":
                    continue
                
                target = self.project_root / item.name
                
                if item.is_dir():
                    if target.exists():
                        shutil.rmtree(target)
                    shutil.copytree(item, target)
                else:
                    shutil.copy2(item, target)
                
                print_colored(f"✓ Restored: {item.name}", GREEN)
            
            # Remove migrated files that weren't in backup
            migrated_files = []
            for _, destination in self.file_mappings.items():
                dest_path = self.project_root / destination
                if dest_path.exists():
                    migrated_files.append(dest_path)
            
            for file_path in migrated_files:
                try:
                    file_path.unlink()
                    print_colored(f"✓ Removed migrated file: {file_path.relative_to(self.project_root)}", GREEN)
                except:
                    pass
            
            print_colored("✅ Rollback completed successfully!", GREEN)
            print_colored("⚠️  Remember to restart any running services", YELLOW)
            return True
            
        except Exception as e:
            print_colored(f"❌ Rollback failed: {e}", RED)
            return False


def main():
    parser = argparse.ArgumentParser(description="Safe project migration tool")
    parser.add_argument("--dry-run", action="store_true", help="Preview changes without making them")
    parser.add_argument("--validate", action="store_true", help="Only validate the project structure")  
    parser.add_argument("--migrate", action="store_true", help="Perform the actual migration")
    parser.add_argument("--rollback", action="store_true", help="Rollback to backup")
    parser.add_argument("--project-root", type=str, help="Project root directory", default=".")
    
    args = parser.parse_args()
    
    # Get project root
    project_root = Path(args.project_root).resolve()
    
    if not project_root.exists():
        print_colored(f"❌ Project root not found: {project_root}", RED)
        sys.exit(1)
    
    print_colored(f"📁 Project root: {project_root}", BLUE)
    
    # Create migrator
    migrator = SafeMigrator(project_root)
    
    # Handle different modes
    if args.rollback:
        success = migrator.rollback_migration()
        sys.exit(0 if success else 1)
    
    if args.validate or args.dry_run or args.migrate:
        # Always validate first
        if not migrator.validate_preconditions():
            print_colored("❌ Validation failed - fix issues before proceeding", RED)
            sys.exit(1)
    
    if args.dry_run:
        migrator.preview_migration()
        print_colored("\n💡 This was a dry run. Use --migrate to perform actual migration.", CYAN)
        sys.exit(0)
    
    if args.validate:
        print_colored("✅ Validation completed successfully!", GREEN)
        sys.exit(0)
    
    if args.migrate:
        # Confirm before proceeding
        print_colored("\n⚠️  This will modify your project structure.", YELLOW)
        response = input("Continue with migration? (yes/no): ")
        if response.lower() not in ['yes', 'y']:
            print_colored("Migration cancelled.", YELLOW)
            sys.exit(0)
        
        # Create backup first
        if not migrator.create_backup():
            print_colored("❌ Backup failed - aborting migration", RED)
            sys.exit(1)
        
        # Perform migration
        success = migrator.perform_migration()
        sys.exit(0 if success else 1)
    
    # Default: show help
    parser.print_help()


if __name__ == "__main__":
    main()