#!/usr/bin/env python3
"""
Automated build and upload script for testiterator package.

This script automates the process of:
1. Cleaning previous builds
2. Building source and wheel distributions
3. Validating the package
4. Uploading to PyPI or TestPyPI

Usage:
    python build_and_upload.py              # Upload to PyPI
    python build_and_upload.py --test       # Upload to TestPyPI
    python build_and_upload.py --check-only # Only validate, don't upload
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path


class Colors:
    """ANSI color codes for terminal output."""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(message):
    """Print a formatted header message."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{message}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*60}{Colors.ENDC}\n")


def print_success(message):
    """Print a success message."""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")


def print_error(message):
    """Print an error message."""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")


def print_warning(message):
    """Print a warning message."""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")


def print_info(message):
    """Print an info message."""
    print(f"{Colors.OKCYAN}ℹ {message}{Colors.ENDC}")


def run_command(command, description="", check=True):
    """Run a shell command and print full stdout/stderr if fails."""
    if description:
        print_info(description)
    try:
        result = subprocess.run(
            command,
            check=check,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print_success("Command completed successfully")
            if result.stdout:
                print(result.stdout)
        else:
            print_error(f"Command failed (code {result.returncode})")
            if result.stdout:
                print("STDOUT:\n" + result.stdout)
            if result.stderr:
                print("STDERR:\n" + result.stderr)
        return result
    except subprocess.CalledProcessError as e:
        print_error(f"Command failed: {e}")
        if e.stdout:
            print("STDOUT:\n" + e.stdout)
        if e.stderr:
            print("STDERR:\n" + e.stderr)
        if check:
            sys.exit(1)
        return e


def clean_build_artifacts():
    """Remove old build artifacts and cache directories."""
    print_header("Cleaning Build Artifacts")
    
    dirs_to_remove = [
        "build",
        "dist",
        "*.egg-info",
        "__pycache__",
        ".pytest_cache",
        ".mypy_cache",
        "htmlcov",
        ".coverage",
    ]
    
    removed_count = 0
    for pattern in dirs_to_remove:
        if "*" in pattern:
            # Handle glob patterns
            for path in Path(".").rglob(pattern.replace("*", "")):
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                    removed_count += 1
                elif path.is_file():
                    path.unlink(missing_ok=True)
                    removed_count += 1
        else:
            path = Path(pattern)
            if path.exists():
                if path.is_dir():
                    shutil.rmtree(path, ignore_errors=True)
                else:
                    path.unlink()
                removed_count += 1
    
    print_success(f"Cleaned {removed_count} artifacts")


def check_requirements():
    """Check if required tools are installed."""
    print_header("Checking Requirements")
    
    required_packages = ["build", "twine"]
    missing = []
    
    for package in required_packages:
        try:
            __import__(package)
            print_success(f"{package} is installed")
        except ImportError:
            missing.append(package)
            print_error(f"{package} is not installed")
    
    if missing:
        print_warning(f"Installing missing packages: {', '.join(missing)}")
        run_command(
            f"{sys.executable} -m pip install {' '.join(missing)}",
            "Installing dependencies"
        )


def get_version():
    """Extract version from __init__.py"""
    init_file = Path("testiterator/__init__.py")
    if not init_file.exists():
        print_error("Cannot find testiterator/__init__.py")
        sys.exit(1)
    
    content = init_file.read_text()
    import re
    match = re.search(r'^__version__\s*=\s*[\'"]([^\'"]*)[\'"]', content, re.MULTILINE)
    if match:
        return match.group(1)
    
    print_error("Cannot find version in __init__.py")
    sys.exit(1)


def build_package():
    """Build source and wheel distributions."""
    print_header("Building Package")
    
    version = get_version()
    print_info(f"Building testiterator version {version}")
    
    # Build using python -m build
    run_command(
        [sys.executable, "-m", "build"],
        "Building source and wheel distributions"
    )
    
    # Verify build artifacts
    dist_dir = Path("dist")
    if not dist_dir.exists() or not list(dist_dir.iterdir()):
        print_error("Build failed: no artifacts in dist/")
        sys.exit(1)
    
    print_success(f"Build artifacts created in dist/")
    for file in dist_dir.iterdir():
        print(f"  - {file.name}")


def check_package():
    """Validate the built package."""
    print_header("Validating Package")
    
    # Check with twine
    run_command(
        [sys.executable, "-m", "twine", "check", "dist/*"],
        "Running twine check"
    )
    
    print_success("Package validation passed")


def upload_to_pypi(test_pypi=False):
    """
    Upload package to PyPI or TestPyPI.
    
    Args:
        test_pypi: If True, upload to TestPyPI instead of PyPI
    """
    if test_pypi:
        print_header("Uploading to TestPyPI")
        repository = "testpypi"
        repository_url = "https://test.pypi.org/legacy/"
    else:
        print_header("Uploading to PyPI")
        repository = "pypi"
        repository_url = "https://upload.pypi.org/legacy/"
    
    print_warning("This will upload the package to the repository.")
    print_info(f"Repository: {repository}")
    print_info(f"URL: {repository_url}")
    
    # Confirm upload
    response = input(f"\n{Colors.BOLD}Proceed with upload? [y/N]: {Colors.ENDC}").strip().lower()
    if response != 'y':
        print_warning("Upload cancelled")
        return
    
    # Upload using twine
    if test_pypi:
        run_command(
            [sys.executable, "-m", "twine", "upload", "--repository", "testpypi", "dist/*"],
            f"Uploading to {repository}"
        )
    else:
        run_command(
            [sys.executable, "-m", "twine", "upload", "dist/*"],
            f"Uploading to {repository}"
        )
    
    version = get_version()
    
    if test_pypi:
        print_success(f"Package uploaded to TestPyPI!")
        print_info(f"View at: https://test.pypi.org/project/testiterator/{version}/")
        print_info(f"Install with: pip install -i https://test.pypi.org/simple/ testiterator=={version}")
    else:
        print_success(f"Package uploaded to PyPI!")
        print_info(f"View at: https://pypi.org/project/testiterator/{version}/")
        print_info(f"Install with: pip install testiterator=={version}")


def create_git_tag():
    """Create and push git tag for the release."""
    print_header("Creating Git Tag")
    
    version = get_version()
    tag_name = f"v{version}"
    
    # Check if tag already exists
    result = run_command(
        ["git", "tag", "-l", tag_name],
        "Checking if tag exists",
        check=False
    )
    
    if result.stdout.strip():
        print_warning(f"Tag {tag_name} already exists")
        response = input(f"{Colors.BOLD}Delete and recreate? [y/N]: {Colors.ENDC}").strip().lower()
        if response == 'y':
            run_command(["git", "tag", "-d", tag_name], "Deleting local tag")
            run_command(
                ["git", "push", "origin", f":refs/tags/{tag_name}"],
                "Deleting remote tag",
                check=False
            )
        else:
            return
    
    # Create tag
    run_command(
        ["git", "tag", "-a", tag_name, "-m", f"Release version {version}"],
        f"Creating tag {tag_name}"
    )
    
    # Push tag
    response = input(f"\n{Colors.BOLD}Push tag to remote? [y/N]: {Colors.ENDC}").strip().lower()
    if response == 'y':
        run_command(
            ["git", "push", "origin", tag_name],
            "Pushing tag to remote"
        )
        print_success(f"Tag {tag_name} pushed to remote")


def run_tests():
    """Run the test suite before building."""
    print_header("Running Tests")
    
    result = run_command(
        [sys.executable, "-m", "pytest", "tests/", "-v"],
        "Running test suite",
        check=False
    )
    
    if result.returncode != 0:
        print_error("Tests failed!")
        response = input(f"\n{Colors.BOLD}Continue anyway? [y/N]: {Colors.ENDC}").strip().lower()
        if response != 'y':
            sys.exit(1)
    else:
        print_success("All tests passed")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Build and upload testiterator package to PyPI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python build_and_upload.py              # Full build and upload to PyPI
  python build_and_upload.py --test       # Upload to TestPyPI
  python build_and_upload.py --check-only # Only validate package
  python build_and_upload.py --no-tests   # Skip test execution
  python build_and_upload.py --tag        # Create git tag only
        """
    )
    
    parser.add_argument(
        "--test",
        action="store_true",
        help="Upload to TestPyPI instead of PyPI"
    )
    parser.add_argument(
        "--check-only",
        action="store_true",
        help="Only build and validate, don't upload"
    )
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleaning build artifacts"
    )
    parser.add_argument(
        "--no-tests",
        action="store_true",
        help="Skip running tests"
    )
    parser.add_argument(
        "--tag",
        action="store_true",
        help="Create and push git tag"
    )
    parser.add_argument(
        "--skip-tag",
        action="store_true",
        help="Skip creating git tag"
    )
    
    args = parser.parse_args()
    
    try:
        # Display banner
        print(f"\n{Colors.BOLD}{Colors.HEADER}")
        print("╔════════════════════════════════════════════════════════════╗")
        print("║         testiterator Package Build & Upload Tool          ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print(f"{Colors.ENDC}\n")
        
        version = get_version()
        print_info(f"Package version: {version}")
        print_info(f"Python version: {sys.version.split()[0]}")
        print_info(f"Working directory: {Path.cwd()}")
        
        # Step 1: Check requirements
        check_requirements()
        
        # Step 2: Run tests (unless skipped)
        if not args.no_tests:
            if Path("tests").exists():
                run_tests()
            else:
                print_warning("No tests directory found, skipping tests")
        
        # Step 3: Clean build artifacts (unless skipped)
        if not args.no_clean:
            clean_build_artifacts()
        
        # Step 4: Build package
        build_package()
        
        # Step 5: Validate package
        check_package()
        
        # Step 6: Upload (unless check-only)
        if not args.check_only:
            upload_to_pypi(test_pypi=args.test)
            
            # Step 7: Create git tag (unless skipped)
            if args.tag or (not args.skip_tag and not args.test):
                create_git_tag()
        else:
            print_info("Check-only mode: Skipping upload")
        
        # Success message
        print_header("Build and Upload Complete!")
        print_success("All operations completed successfully")
        
        if not args.check_only:
            print("\n" + Colors.BOLD + "Next steps:" + Colors.ENDC)
            if args.test:
                print("  1. Test installation: pip install -i https://test.pypi.org/simple/ testiterator")
                print("  2. Run tests on installed package")
                print("  3. If all good, run without --test flag to upload to PyPI")
            else:
                print("  1. Verify on PyPI: https://pypi.org/project/testiterator/")
                print("  2. Test installation: pip install testiterator")
                print("  3. Update documentation and announce release")
        
    except KeyboardInterrupt:
        print_warning("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print_error(f"\n\nUnexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()