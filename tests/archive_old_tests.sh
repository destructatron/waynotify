#!/bin/bash
# Script to archive old test files after verifying new tests work

set -e

echo "Archiving old test files..."
echo "This will move the old .py and .sh test files to tests/old/"
echo ""
read -p "Have you verified the new pytest suite works? (y/N) " -n 1 -r
echo

if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborting. Run 'pytest' to verify tests first."
    exit 1
fi

# Create old tests directory
mkdir -p old

# List of old test files to archive
OLD_FILES=(
    "test-simple.py"
    "test-client.sh"
    "test_spec_compliance.py"
    "test_markup.py"
    "test_signals.py"
    "test_client_actions.py"
    "test_action_freeze.py"
    "test_action_id.py"
    "test_delayed_action.py"
    "test_first_notification_bug.py"
    "test_client_first_notif.py"
    "test_request_id_zero.py"
    "test_expired_action.sh"
    "test_notifications.sh"
    "test_icon_support.sh"
    "test_html_notifications.sh"
    "test_all_actions.sh"
    "test-full.sh"
    "run-test.sh"
    "verify_fix.sh"
)

MOVED=0
SKIPPED=0

for file in "${OLD_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo "  Moving $file to old/"
        mv "$file" old/
        ((MOVED++))
    else
        echo "  Skipping $file (not found)"
        ((SKIPPED++))
    fi
done

echo ""
echo "Done! Moved $MOVED files, skipped $SKIPPED"
echo "Old test files are in tests/old/"
echo ""
echo "To use the new test suite:"
echo "  pytest                    # Run all tests"
echo "  pytest -v                 # Verbose output"
echo "  ./run_tests.py --help     # See all options"
