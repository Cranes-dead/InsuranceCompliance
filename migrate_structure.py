#!/usr/bin/env python3
"""
Migration script to transition from old project structure to new structure.
This script helps move files and update imports systematically.
"""

import os
import shutil
import re
from pathlib import Path
from typing import List, Dict, Tuple

# Color codes for console output
GREEN = '\033[92m'
YELLOW = '\033[93m'
RED = '\033[91m'
BLUE = '\033[94m'
ENDC = '\033[0m'

def print_colored(message: str, color: str = ''):
    """Print colored message to console."""
    print(f"{color}{message}{ENDC}")

class ProjectMigrator:
    """Handles migration from old structure to new structure."""
    
    def __init__(self, project_root: Path):
        self.project_root = project_root
        self.backup_dir = project_root / "backup_old_structure"
        self.migration_log = []
        
    def log_action(self, action: str, details: str = ""):
        """Log migration actions."""
        log_entry = f"{action}: {details}"
        self.migration_log.append(log_entry)
        print_colored(f"✓ {log_entry}", GREEN)
    
    def create_backup(self):
        """Create backup of current structure before migration."""
        print_colored("Creating backup of current structure...", BLUE)
        
        if self.backup_dir.exists():
            shutil.rmtree(self.backup_dir)
        
        self.backup_dir.mkdir()
        
        # Backup key files and directories
        items_to_backup = [
            "src",
            "updated_compliance_system.py",
            "reclassify_rules.py", 
            "simple_training.py",
            "rule_based_classifier.py",
            "requirements.txt"
        ]
        
        for item in items_to_backup:
            item_path = self.project_root / item
            if item_path.exists():
                if item_path.is_dir():
                    shutil.copytree(item_path, self.backup_dir / item)
                else:
                    shutil.copy2(item_path, self.backup_dir / item)
                self.log_action("BACKUP", f"{item} -> backup_old_structure/{item}")
    
    def move_compliance_engine(self):
        """Move and refactor the main compliance engine."""
        old_file = self.project_root / "updated_compliance_system.py"
        new_dir = self.project_root / "app" / "ml" / "inference"
        
        if old_file.exists():
            # Read and analyze the old file
            content = old_file.read_text(encoding='utf-8')
            
            # Create a refactored version (this would need manual review)
            refactored_content = self._refactor_compliance_engine(content)
            
            # Write to new location
            new_file = new_dir / "legacy_compliance_engine.py"
            new_file.write_text(refactored_content, encoding='utf-8')
            
            self.log_action("MOVE", f"updated_compliance_system.py -> app/ml/inference/legacy_compliance_engine.py")
            
    def move_document_parsers(self):
        """Move document parsing logic."""
        old_parser = self.project_root / "src" / "processing" / "parsers" / "document_parser.py"
        new_parser = self.project_root / "app" / "processing" / "parsers" / "document_parser_legacy.py"
        
        if old_parser.exists():
            shutil.copy2(old_parser, new_parser)
            self.log_action("MOVE", f"src/processing/parsers/document_parser.py -> app/processing/parsers/document_parser_legacy.py")
    
    def move_api_routes(self):
        """Move and refactor API routes."""
        old_routes_dir = self.project_root / "src" / "api" / "routes"
        new_endpoints_dir = self.project_root / "api" / "v1" / "endpoints"
        
        if old_routes_dir.exists():
            for route_file in old_routes_dir.glob("*.py"):
                if route_file.name != "__init__.py":
                    new_file = new_endpoints_dir / f"legacy_{route_file.name}"
                    shutil.copy2(route_file, new_file)
                    self.log_action("MOVE", f"src/api/routes/{route_file.name} -> api/v1/endpoints/legacy_{route_file.name}")
    
    def move_ml_models(self):
        """Move ML model files."""
        old_models_dir = self.project_root / "src" / "ml" / "models"
        new_models_dir = self.project_root / "app" / "ml" / "models"
        
        if old_models_dir.exists():
            for model_file in old_models_dir.glob("*.py"):
                if model_file.name != "__init__.py":
                    new_file = new_models_dir / f"legacy_{model_file.name}"
                    shutil.copy2(model_file, new_file)
                    self.log_action("MOVE", f"src/ml/models/{model_file.name} -> app/ml/models/legacy_{model_file.name}")
    
    def move_training_data(self):
        """Move training data files."""
        old_data = self.project_root / "data" / "training"
        if old_data.exists():
            self.log_action("KEEP", "data/training directory maintained in same location")
    
    def update_imports_in_file(self, file_path: Path):
        """Update imports in a Python file to use new structure."""
        if not file_path.exists() or file_path.suffix != '.py':
            return
        
        try:
            content = file_path.read_text(encoding='utf-8')
            original_content = content
            
            # Common import patterns to update
            import_mappings = {
                r'from src\.api\.': 'from api.',
                r'from src\.ml\.': 'from app.ml.',
                r'from src\.processing\.': 'from app.processing.',
                r'from src\.data\.': 'from app.data.',
                r'from updated_compliance_system import': 'from app.ml.inference.compliance_engine import ComplianceEngine',
                r'import updated_compliance_system': 'from app.ml.inference.compliance_engine import ComplianceEngine',
                r'sys\.path\.append\([^)]+\)': '# Removed sys.path.append - using proper package imports',
            }
            
            changes_made = []
            for pattern, replacement in import_mappings.items():
                if re.search(pattern, content):
                    content = re.sub(pattern, replacement, content)
                    changes_made.append(f"{pattern} -> {replacement}")
            
            if content != original_content:
                file_path.write_text(content, encoding='utf-8')
                self.log_action("UPDATE_IMPORTS", f"{file_path.relative_to(self.project_root)}: {len(changes_made)} changes")
                
        except Exception as e:
            print_colored(f"Warning: Could not update imports in {file_path}: {e}", YELLOW)
    
    def _refactor_compliance_engine(self, content: str) -> str:
        """Basic refactoring of the compliance engine code."""
        # This is a simplified refactor - manual review would be needed
        refactored = f'''"""
Legacy compliance engine - NEEDS MANUAL REVIEW AND INTEGRATION
Migrated from updated_compliance_system.py
"""

# TODO: Integrate this code with the new ComplianceEngine class
# TODO: Update imports to use new package structure
# TODO: Refactor to use new configuration system

{content}
'''
        return refactored
    
    def update_all_imports(self):
        """Update imports in all Python files."""
        print_colored("Updating imports in Python files...", BLUE)
        
        python_files = []
        for pattern in ["**/*.py"]:
            python_files.extend(self.project_root.glob(pattern))
        
        for py_file in python_files:
            if "backup_old_structure" not in str(py_file):
                self.update_imports_in_file(py_file)
    
    def create_migration_report(self):
        """Create a migration report."""
        report_file = self.project_root / "MIGRATION_REPORT.md"
        
        report_content = f"""# Migration Report
Generated: {os.popen('date').read().strip()}

## Summary
- Total actions: {len(self.migration_log)}
- Backup created: {self.backup_dir}

## Actions Performed
"""
        
        for action in self.migration_log:
            report_content += f"- {action}\n"
        
        report_content += """
## Next Steps (Manual)

### 1. Review Moved Files
- Check `app/ml/inference/legacy_compliance_engine.py`
- Integrate with new `ComplianceEngine` class
- Update imports and dependencies

### 2. Update Configuration
- Review `app/core/config.py`
- Update environment variables
- Set proper paths for models and data

### 3. Test the New Structure
```bash
# Install new requirements
pip install -r requirements-new.txt

# Test API server
python api/main.py

# Test compliance analysis
python -m app.services.compliance_service
```

### 4. Update Documentation
- Update README.md with new structure
- Update HOW_TO_RUN.md
- Review API documentation

### 5. Frontend Integration
- Update Streamlit app imports
- Prepare for Next.js migration
- Update API endpoints calls

## Files Requiring Manual Review
- All files marked as "legacy_*"
- Import statements throughout the project  
- Configuration files
- Environment variables
"""
        
        report_file.write_text(report_content)
        self.log_action("CREATE", f"Migration report: {report_file}")
    
    def run_migration(self):
        """Run the complete migration process."""
        print_colored("🚀 Starting Project Migration", BLUE)
        print_colored("=" * 50, BLUE)
        
        # Step 1: Create backup
        self.create_backup()
        
        # Step 2: Move core files
        self.move_compliance_engine()
        self.move_document_parsers()
        self.move_api_routes()
        self.move_ml_models()
        self.move_training_data()
        
        # Step 3: Update imports
        self.update_all_imports()
        
        # Step 4: Create migration report
        self.create_migration_report()
        
        print_colored("=" * 50, BLUE)
        print_colored("🎉 Migration completed!", GREEN)
        print_colored(f"📋 Check MIGRATION_REPORT.md for next steps", YELLOW)
        print_colored(f"💾 Backup available at: {self.backup_dir}", YELLOW)


if __name__ == "__main__":
    import sys
    
    # Get project root
    if len(sys.argv) > 1:
        project_root = Path(sys.argv[1])
    else:
        project_root = Path.cwd()
    
    if not project_root.exists():
        print_colored(f"❌ Project root not found: {project_root}", RED)
        sys.exit(1)
    
    print_colored(f"📁 Project root: {project_root}", BLUE)
    
    # Confirm before proceeding
    response = input(f"\n⚠️  This will modify your project structure. Continue? (y/N): ")
    if response.lower() not in ['y', 'yes']:
        print_colored("Migration cancelled.", YELLOW)
        sys.exit(0)
    
    # Run migration
    migrator = ProjectMigrator(project_root)
    migrator.run_migration()