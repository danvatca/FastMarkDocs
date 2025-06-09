#!/usr/bin/env python3
"""
Test runner for FastMarkDocs library.

This script provides a convenient way to run different types of tests
with various options and configurations.
"""

import sys
import subprocess
import argparse
from pathlib import Path


def run_command(cmd, description):
    """Run a command and handle the result."""
    print(f"\n🔍 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)
    
    result = subprocess.run(cmd, capture_output=False)
    
    if result.returncode == 0:
        print(f"✅ {description} - PASSED")
    else:
        print(f"❌ {description} - FAILED")
        return False
    
    return True


def main():
    """Main test runner function."""
    parser = argparse.ArgumentParser(description="Run tests for FastMarkDocs library")
    parser.add_argument(
        "--type", 
        choices=["unit", "integration", "all"], 
        default="all",
        help="Type of tests to run (default: all)"
    )
    parser.add_argument(
        "--coverage", 
        action="store_true",
        help="Run tests with coverage reporting"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    parser.add_argument(
        "--fast",
        action="store_true",
        help="Skip slow tests"
    )
    parser.add_argument(
        "--parallel", "-n",
        type=int,
        help="Run tests in parallel (specify number of workers)"
    )
    parser.add_argument(
        "--pattern",
        help="Run tests matching pattern"
    )
    
    args = parser.parse_args()
    
    # Base pytest command
    cmd = ["python", "-m", "pytest"]
    
    # Add test type selection
    if args.type == "unit":
        cmd.extend(["tests/unit"])
    elif args.type == "integration":
        cmd.extend(["tests/integration"])
    else:
        cmd.extend(["tests"])
    
    # Add coverage if requested
    if args.coverage:
        cmd.extend([
            "--cov=src/fastapi_markdown_docs",
            "--cov-report=html:htmlcov",
            "--cov-report=term-missing",
            "--cov-report=xml"
        ])
    
    # Add verbosity
    if args.verbose:
        cmd.append("-vv")
    
    # Skip slow tests if requested
    if args.fast:
        cmd.extend(["-m", "not slow"])
    
    # Add parallel execution
    if args.parallel:
        cmd.extend(["-n", str(args.parallel)])
    
    # Add pattern matching
    if args.pattern:
        cmd.extend(["-k", args.pattern])
    
    # Run the tests
    success = run_command(cmd, f"Running {args.type} tests")
    
    if not success:
        print("\n❌ Tests failed!")
        sys.exit(1)
    
    print("\n✅ All tests passed!")
    
    # Show coverage report location if coverage was run
    if args.coverage:
        print(f"\n📊 Coverage report generated:")
        print(f"  - HTML: htmlcov/index.html")
        print(f"  - XML: coverage.xml")


if __name__ == "__main__":
    main() 