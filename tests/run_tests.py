#!/usr/bin/env python3
"""
Main test runner for WayNotify test suite.

This script provides a convenient way to run tests with common configurations.
"""
import argparse
import subprocess
import sys


def main():
    parser = argparse.ArgumentParser(
        description="Run WayNotify test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Run all tests
  %(prog)s --unit            # Run only unit tests
  %(prog)s --integration     # Run only integration tests
  %(prog)s --dbus            # Run only D-Bus tests
  %(prog)s --fast            # Exclude slow tests
  %(prog)s --verbose         # Verbose output
  %(prog)s --coverage        # Run with coverage report
        """
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Verbose output'
    )

    parser.add_argument(
        '--unit',
        action='store_true',
        help='Run only unit tests (no daemon required)'
    )

    parser.add_argument(
        '--integration',
        action='store_true',
        help='Run only integration tests (require daemon)'
    )

    parser.add_argument(
        '--dbus',
        action='store_true',
        help='Run only D-Bus tests'
    )

    parser.add_argument(
        '--socket',
        action='store_true',
        help='Run only socket tests'
    )

    parser.add_argument(
        '--fast',
        action='store_true',
        help='Exclude slow tests'
    )

    parser.add_argument(
        '--coverage',
        action='store_true',
        help='Run with coverage report'
    )

    parser.add_argument(
        '--html-coverage',
        action='store_true',
        help='Generate HTML coverage report'
    )

    parser.add_argument(
        '-k',
        dest='pattern',
        help='Run tests matching pattern'
    )

    parser.add_argument(
        'pytest_args',
        nargs='*',
        help='Additional arguments to pass to pytest'
    )

    args = parser.parse_args()

    # Build pytest command
    cmd = ['pytest']

    # Add verbosity
    if args.verbose:
        cmd.append('-v')

    # Add markers
    markers = []
    if args.unit:
        markers.append('unit')
    if args.integration:
        markers.append('integration')
    if args.dbus:
        markers.append('dbus')
    if args.socket:
        markers.append('socket')
    if args.fast:
        markers.append('not slow')

    if markers:
        cmd.extend(['-m', ' and '.join(markers)])

    # Add pattern matching
    if args.pattern:
        cmd.extend(['-k', args.pattern])

    # Add coverage
    if args.coverage or args.html_coverage:
        cmd.extend(['--cov=src', '--cov-report=term'])
        if args.html_coverage:
            cmd.append('--cov-report=html')

    # Add any additional pytest arguments
    if args.pytest_args:
        cmd.extend(args.pytest_args)

    # Print command
    print(f"Running: {' '.join(cmd)}")
    print()

    # Run pytest
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


if __name__ == '__main__':
    main()
