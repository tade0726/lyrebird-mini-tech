#!/usr/bin/env python3
"""
Test runner script for the Lyrebird API.

Usage:
    python run_tests.py                 # Run all tests
    python run_tests.py --unit          # Run only unit tests
    python run_tests.py --integration   # Run only integration tests
    python run_tests.py --auth          # Run only auth tests
    python run_tests.py --dictation     # Run only dictation tests
    python run_tests.py --coverage      # Run with coverage report
"""

import sys
import subprocess
import argparse


def run_command(cmd: list[str], description: str) -> int:
    """Run a command and return the exit code."""
    print(f"\n🚀 {description}")
    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print(f"✅ {description} completed successfully")
    else:
        print(f"❌ {description} failed with exit code {result.returncode}")

    return result.returncode


def main():
    parser = argparse.ArgumentParser(description="Run Lyrebird API tests")
    parser.add_argument("--unit", action="store_true", help="Run only unit tests")
    parser.add_argument(
        "--integration", action="store_true", help="Run only integration tests"
    )
    parser.add_argument(
        "--auth", action="store_true", help="Run only authentication tests"
    )
    parser.add_argument(
        "--dictation", action="store_true", help="Run only dictation tests"
    )
    parser.add_argument(
        "--coverage", action="store_true", help="Run with coverage report"
    )
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument(
        "--parallel", "-n", type=int, help="Run tests in parallel (number of workers)"
    )
    parser.add_argument(
        "--skip-slow",
        action="store_true",
        help="Skip slow tests (edge cases, performance)",
    )
    parser.add_argument(
        "--fail-fast", "-x", action="store_true", help="Stop on first failure"
    )

    args = parser.parse_args()

    # Check for async test support
    try:
        import pytest_asyncio
    except ImportError:
        print("⚠️  pytest-asyncio not installed, async tests will be skipped")
        print("   To run async tests: uv add pytest-asyncio")
        print()

    # Base pytest command
    cmd = ["uv", "run", "pytest"]

    # Add configuration file and test directory
    cmd.extend(["-c", "api/tests/pytest.ini", "api/tests/"])

    # Add markers based on arguments
    if args.unit:
        cmd.extend(["-m", "unit"])
    elif args.integration:
        cmd.extend(["-m", "integration"])
    elif args.auth:
        cmd.extend(["-m", "auth"])
    elif args.dictation:
        cmd.extend(["-m", "dictation"])

    # Add coverage if requested
    if args.coverage:
        cmd.extend(
            [
                "--cov=api",
                "--cov-report=html",
                "--cov-report=term-missing",
                "--cov-report=xml",
            ]
        )

    # Add verbosity
    if args.verbose:
        cmd.append("-vv")

    # Add parallel execution (only if pytest-xdist is available)
    if args.parallel:
        try:
            import xdist

            cmd.extend(["-n", str(args.parallel)])
        except ImportError:
            print("⚠️  pytest-xdist not installed, running tests sequentially")
            print("   To enable parallel execution: uv add pytest-xdist")

    # Skip slow tests if requested
    if args.skip_slow:
        cmd.extend(["-m", "not slow"])

    # Fail fast if requested
    if args.fail_fast:
        cmd.append("-x")

    # Run the tests
    exit_code = run_command(cmd, "Running Lyrebird API Tests")

    if args.coverage and exit_code == 0:
        print("\n📊 Coverage report generated:")
        print("  - HTML: htmlcov/index.html")
        print("  - XML: coverage.xml")

    return exit_code


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
