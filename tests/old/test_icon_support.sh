#!/bin/bash
# Comprehensive icon support test for waynotify

echo "Testing waynotify icon support..."
echo ""

# Test 1: Icon theme name
echo "Test 1: Icon from theme (dialog-information)"
notify-send -i dialog-information "Icon Theme" "This uses a theme icon" 2>/dev/null
sleep 2

# Test 2: File path (absolute)
echo "Test 2: Icon from file path"
if [ -f /usr/share/pixmaps/debian-logo.png ]; then
    notify-send -i /usr/share/pixmaps/debian-logo.png "File Path Icon" "This uses an absolute file path" 2>/dev/null
else
    echo "  (debian-logo.png not found, skipping)"
fi
sleep 2

# Test 3: file:// URI
echo "Test 3: Icon from file:// URI"
if [ -f /usr/share/pixmaps/debian-logo.png ]; then
    notify-send -i file:///usr/share/pixmaps/debian-logo.png "File URI Icon" "This uses a file:// URI" 2>/dev/null
else
    echo "  (debian-logo.png not found, skipping)"
fi
sleep 2

# Test 4: No icon
echo "Test 4: No icon"
notify-send "No Icon" "This notification has no icon" 2>/dev/null
sleep 2

# Test 5: Various urgency levels with icons
echo "Test 5: Different urgency levels with icons"
notify-send -u low -i dialog-information "Low Priority" "Low urgency with icon" 2>/dev/null
sleep 1
notify-send -u normal -i dialog-warning "Normal Priority" "Normal urgency with icon" 2>/dev/null
sleep 1
notify-send -u critical -i dialog-error "Critical Priority" "Critical urgency with icon" 2>/dev/null
sleep 2

echo ""
echo "All tests completed! Check that:"
echo "  1. Icons from theme names displayed correctly"
echo "  2. Icons from file paths displayed correctly"
echo "  3. Icons from file:// URIs displayed correctly"
echo "  4. Notifications without icons displayed correctly"
echo "  5. Icons displayed at all urgency levels"
