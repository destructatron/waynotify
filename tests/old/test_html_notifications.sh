#!/bin/bash
# Test HTML sanitization in notifications
# These notifications contain HTML markup that should be stripped

echo "Testing HTML sanitization in notifications..."
echo "All HTML tags should be removed from displayed text and Orca announcements"
echo ""

# Test 1: Basic HTML tags
notify-send "Test 1: HTML Tags" "This has <b>bold</b> and <i>italic</i> text"
sleep 2

# Test 2: Hyperlinks (common in browser notifications)
notify-send "Test 2: Hyperlinks" "Click <a href='https://example.com'>here</a> to visit"
sleep 2

# Test 3: HTML entities
notify-send "Test 3: Entities" "Special chars: &lt; &gt; &amp; &quot;"
sleep 2

# Test 4: Complex markup (like Brave browser notifications)
notify-send "Test 4: Complex" "<div><p>Paragraph with <a href='url'>link</a></p></div>"
sleep 2

# Test 5: Multiple tags
notify-send "Test 5: Multiple Tags" "<span class='test'><strong>Bold</strong> and <em>emphasis</em></span>"
sleep 2

echo ""
echo "All tests sent. Check that:"
echo "  1. No HTML tags appear in popups"
echo "  2. Orca does not announce HTML tags"
echo "  3. Text is clean and readable"
