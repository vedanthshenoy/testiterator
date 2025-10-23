#!/usr/bin/env python3
"""
Package validation script for testiterator.

This script performs comprehensive validation checks before uploading to PyPI:
1. Verify package structure
2. Check required files exist
3. Validate setup configuration
4. Run linters and type checkers
5. Check documentation
6. Verify version consistency
7. Test import functionality

Usage:
    python check_package.py              # Run all checks
    python check_package.py --quick      # Run quick checks only
    python check_package.py --fix        # Auto-fix issues where possible
"""

import argparse
import ast
import re
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple


class Colors:
    """ANSI color codes."""
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    BOLD = '\033[1m'
    ENDC = '\033[0m'


class PackageChecker:
    """Validates testiterator package before upload."""
    
    def __init__(self, fix_issues=False):
        self.fix_issues = fix_issues
        self.errors = []
        self.warnings = []
        self.successes = []
        self.root_dir = Path(__file__).parent
    
    def print_header(self, message):
        """Print section header."""
        print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{message}{Colors.ENDC}")
        print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.ENDC}\n")
    
    def print_success(self, message):
        """Print success message."""
        print(f"{Colors.GREEN}✓ {message}{Colors.ENDC}")
        self.successes.append(message)
    
    def print_error(self, message):
        """Print error message."""
        print(f"{Colors.RED}✗ {message}{Colors.ENDC}")
        self.errors.append(message)
    
    def print_warning(self, message):
        """Print warning message."""
        print(f"{Colors.YELLOW}⚠ {message}{Colors.ENDC}")
        self.warnings.append(message)
    
    def check_required_files(self) -> bool:
        """Check if all required files exist."""
        self.print_header("Checking Required Files")
        
        required_files = [
                "setup.py",
                "README.md",
                "LICENSE",
                "MANIFEST.in",
                "requirements.txt",
                "testiterator/__init__.py",
                "testiterator/decorator.py",
                "testiterator/cli.py",
                "testiterator/core/__init__.py",
                "testiterator/core/analyzer.py",
                "testiterator/core/test_writer.py",
                "testiterator/core/runner.py",
            ]

        
        all_exist = True
        for file_path in required_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                self.print_success(f"Found: {file_path}")
            else:
                self.print_error(f"Missing: {file_path}")
                all_exist = False
        
        return all_exist
    
    def check_version_consistency(self) -> bool:
        """Check version consistency across files."""
        self.print_header("Checking Version Consistency")
        
        # Extract version from __init__.py
        init_file = self.root_dir / "testiterator" / "__init__.py"
        if not init_file.exists():
            self.print_error("Cannot find testiterator/__init__.py")
            return False
        
        content = init_file.read_text()
        match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
        if not match:
            self.print_error("Cannot find __version__ in __init__.py")
            return False
        
        version = match.group(1)
        self.print_success(f"Package version: {version}")
        
        # Check version format (semantic versioning)
        if not re.match(r'^\d+\.\d+\.\d+', version):
            self.print_warning(f"Version '{version}' doesn't follow semantic versioning (x.y.z)")
        
        # Check setup.py (if it extracts from __init__.py, this is OK)
        setup_file = self.root_dir / "setup.py"
        if setup_file.exists():
            setup_content = setup_file.read_text()
            if "get_version()" in setup_content or "__version__" in setup_content:
                self.print_success("setup.py reads version from __init__.py")
            else:
                self.print_warning("setup.py might have hardcoded version")
        
        return True
    
    def check_package_structure(self) -> bool:
        """Verify package structure is correct."""
        self.print_header("Checking Package Structure")
        
        package_dir = self.root_dir / "testiterator"
        if not package_dir.exists():
            self.print_error("testiterator package directory not found")
            return False
        
        # Check for __init__.py files
        init_files = list(package_dir.rglob("__init__.py"))
        self.print_success(f"Found {len(init_files)} __init__.py files")
        
        # Check for Python files
        py_files = list(package_dir.rglob("*.py"))
        self.print_success(f"Found {len(py_files)} Python files")
        
        # Check core module
        core_dir = package_dir / "core"
        if core_dir.exists():
            self.print_success("Core module exists")
        else:
            self.print_error("Core module not found")
            return False
        
        return True
    
    def check_imports(self) -> bool:
        """Test that package can be imported."""
        self.print_header("Checking Package Imports")
        
        try:
            # Try importing main package
            import testiterator
            self.print_success("Successfully imported testiterator")
            
            # Check version
            if hasattr(testiterator, '__version__'):
                self.print_success(f"Version accessible: {testiterator.__version__}")
            else:
                self.print_warning("__version__ not accessible")
            
            # Check main exports
            required_exports = ['testiterator', 'CodeAnalyzer', 'TestWriter', 'TestRunner']
            for export in required_exports:
                if hasattr(testiterator, export):
                    self.print_success(f"Export available: {export}")
                else:
                    self.print_error(f"Missing export: {export}")
            
            return True
            
        except ImportError as e:
            self.print_error(f"Cannot import testiterator: {e}")
            return False
        except Exception as e:
            self.print_error(f"Import error: {e}")
            return False
    
    def check_syntax(self) -> bool:
        """Check Python syntax in all files."""
        self.print_header("Checking Python Syntax")
        
        package_dir = self.root_dir / "testiterator"
        py_files = list(package_dir.rglob("*.py"))
        
        syntax_ok = True
        for py_file in py_files:
            try:
                with open(py_file, 'r', encoding='utf-8') as f:
                    ast.parse(f.read(), filename=str(py_file))
                self.print_success(f"Syntax OK: {py_file.relative_to(self.root_dir)}")
            except SyntaxError as e:
                self.print_error(f"Syntax error in {py_file.relative_to(self.root_dir)}: {e}")
                syntax_ok = False
        
        return syntax_ok
    
    def run_linters(self) -> bool:
        """Run code quality checks."""
        self.print_header("Running Code Quality Checks")
        
        # Check if flake8 is available
        try:
            result = subprocess.run(
                ["flake8", "testiterator/", "--count", "--max-line-length=100"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.print_success("flake8: No issues found")
            else:
                self.print_warning(f"flake8 found issues:\n{result.stdout}")
            
        except FileNotFoundError:
            self.print_warning("flake8 not installed, skipping")
        
        # Check if black would reformat
        try:
            result = subprocess.run(
                ["black", "--check", "testiterator/"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                self.print_success("black: Code formatting is correct")
            else:
                self.print_warning("black: Code needs reformatting")
                if self.fix_issues:
                    subprocess.run(["black", "testiterator/"])
                    self.print_success("black: Code reformatted")
        
        except FileNotFoundError:
            self.print_warning("black not installed, skipping")
        
        return True
    
    def check_documentation(self) -> bool:
        """Check documentation completeness."""
        self.print_header("Checking Documentation")
        
        # Check README
        readme = self.root_dir / "README.md"
        if readme.exists():
            content = readme.read_text()
            required_sections = [
                "# testiterator",
                "## Installation",
                "## Usage",
                "## Features",
            ]
            
            for section in required_sections:
                if section.lower() in content.lower():
                    self.print_success(f"README contains: {section}")
                else:
                    self.print_warning(f"README missing: {section}")
            
            # Check length
            if len(content) < 500:
                self.print_warning("README is quite short (< 500 chars)")
            else:
                self.print_success(f"README length: {len(content)} characters")
        else:
            self.print_error("README.md not found")
            return False
        
        # Check LICENSE
        license_file = self.root_dir / "LICENSE"
        if license_file.exists():
            self.print_success("LICENSE file exists")
        else:
            self.print_error("LICENSE file not found")
            return False
        
        # Check docstrings in main modules
        main_files = [
            "testiterator/__init__.py",
            "testiterator/decorator.py",
            "testiterator/cli.py",
        ]
        
        for file_path in main_files:
            full_path = self.root_dir / file_path
            if full_path.exists():
                content = full_path.read_text()
                if '"""' in content or "'''" in content:
                    self.print_success(f"Docstrings found in: {file_path}")
                else:
                    self.print_warning(f"No docstrings in: {file_path}")
        
        return True
    
    def check_dependencies(self) -> bool:
        """Check dependencies are properly specified."""
        self.print_header("Checking Dependencies")
        
        req_file = self.root_dir / "requirements.txt"
        if not req_file.exists():
            self.print_error("requirements.txt not found")
            return False
        
        requirements = req_file.read_text().strip().split('\n')
        requirements = [r.strip() for r in requirements if r.strip() and not r.startswith('#')]
        
        self.print_success(f"Found {len(requirements)} dependencies")
        for req in requirements:
            self.print_success(f"  - {req}")
        
        # Check if dependencies are installed
        for req in requirements:
            package_name = req.split('>=')[0].split('==')[0].strip()
            try:
                __import__(package_name.replace('-', '_'))
                self.print_success(f"Installed: {package_name}")
            except ImportError:
                self.print_warning(f"Not installed: {package_name}")
        
        return True
    
    def check_entry_points(self) -> bool:
        """Check CLI entry points are configured."""
        self.print_header("Checking Entry Points")
        
        setup_file = self.root_dir / "setup.py"
        if setup_file.exists():
            content = setup_file.read_text()
            if "console_scripts" in content and "testiterator" in content:
                self.print_success("CLI entry point configured in setup.py")
            else:
                self.print_warning("CLI entry point not found in setup.py")
        
        # Check pyproject.toml
        pyproject = self.root_dir / "pyproject.toml"
        if pyproject.exists():
            content = pyproject.read_text()
            if "[project.scripts]" in content:
                self.print_success("Scripts configured in pyproject.toml")
            else:
                self.print_warning("No scripts section in pyproject.toml")
        
        return True
    
    def print_summary(self):
        """Print validation summary."""
        self.print_header("Validation Summary")
        
        total_checks = len(self.successes) + len(self.warnings) + len(self.errors)
        
        print(f"{Colors.GREEN}Passed: {len(self.successes)}{Colors.ENDC}")
        print(f"{Colors.YELLOW}Warnings: {len(self.warnings)}{Colors.ENDC}")
        print(f"{Colors.RED}Errors: {len(self.errors)}{Colors.ENDC}")
        print(f"Total checks: {total_checks}\n")
        
        if self.errors:
            print(f"{Colors.RED}{Colors.BOLD}FAILED - Fix errors before uploading{Colors.ENDC}\n")
            print("Errors found:")
            for error in self.errors:
                print(f"  - {error}")
            return False
        elif self.warnings:
            print(f"{Colors.YELLOW}{Colors.BOLD}PASSED WITH WARNINGS{Colors.ENDC}\n")
            print("Warnings (consider fixing):")
            for warning in self.warnings:
                print(f"  - {warning}")
            return True
        else:
            print(f"{Colors.GREEN}{Colors.BOLD}ALL CHECKS PASSED ✓{Colors.ENDC}\n")
            print("Package is ready for upload!")
            return True
    
    def run_all_checks(self, quick=False) -> bool:
        """Run all validation checks."""
        checks = [
            ("Required Files", self.check_required_files),
            ("Version Consistency", self.check_version_consistency),
            ("Package Structure", self.check_package_structure),
            ("Python Syntax", self.check_syntax),
            ("Package Imports", self.check_imports),
            ("Dependencies", self.check_dependencies),
            ("Documentation", self.check_documentation),
            ("Entry Points", self.check_entry_points),
        ]
        
        if not quick:
            checks.append(("Code Quality", self.run_linters))
        
        all_passed = True
        for check_name, check_func in checks:
            try:
                result = check_func()
                if not result:
                    all_passed = False
            except Exception as e:
                self.print_error(f"Check '{check_name}' failed with exception: {e}")
                all_passed = False
        
        return self.print_summary()


def main():
    """Main execution."""
    parser = argparse.ArgumentParser(
        description="Validate testiterator package before PyPI upload",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "--quick",
        action="store_true",
        help="Run quick checks only (skip linters)"
    )
    parser.add_argument(
        "--fix",
        action="store_true",
        help="Auto-fix issues where possible"
    )
    
    args = parser.parse_args()
    
    print(f"\n{Colors.BOLD}{Colors.BLUE}")
    print("╔════════════════════════════════════════════════════════════╗")
    print("║         testiterator Package Validation Tool              ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print(f"{Colors.ENDC}\n")
    
    checker = PackageChecker(fix_issues=args.fix)
    success = checker.run_all_checks(quick=args.quick)
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()