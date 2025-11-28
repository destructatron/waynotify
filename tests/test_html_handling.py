#!/usr/bin/env python3
"""Test script for HTML handling improvements"""

import sys
sys.path.insert(0, 'src')

# Import the strip_html function from waynotify
import re
from html import unescape as html_unescape
from html.parser import HTMLParser


def strip_html(text: str) -> str:
    """
    Strip HTML tags per freedesktop.org notification specification.

    Only strips the 5 tags allowed by the spec: <b>, <i>, <u>, <a>, <img>
    Preserves all other angle bracket usage (like <spoiler>, <@user>, etc.)

    Reference: https://specifications.freedesktop.org/notification/latest-single/
    "A full-blown HTML implementation is not required of this spec, and
    notifications should never take advantage of tags that are not listed above."

    Examples:
        "<b>Bold</b> text" -> "Bold text"
        "<i>Italic</i> text" -> "Italic text"
        "<a href='url'>Link</a>" -> "Link"
        "<spoiler>secret</spoiler>" -> "<spoiler>secret</spoiler>" (preserved)
        "Hey <@user123>" -> "Hey <@user123>" (preserved)
        "&lt;3" -> "<3" (entity decoded)
    """
    if not text:
        return text

    # Strip only the 5 tags allowed by freedesktop.org spec
    # Match opening tags with attributes: <tag ...> and closing tags: </tag>
    text = re.sub(r'</?b(?:\s[^>]*)?\s*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?i(?:\s[^>]*)?\s*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?u(?:\s[^>]*)?\s*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'</?a(?:\s[^>]*)?\s*>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<img(?:\s[^>]*)?\s*/?>', '', text, flags=re.IGNORECASE)

    # Decode HTML entities (&amp;, &lt;, &quot;, etc.)
    text = html_unescape(text)

    # Clean up excessive whitespace
    text = re.sub(r'\s+', ' ', text).strip()

    return text


# Test cases
test_cases = [
    # Real HTML tags per freedesktop.org spec (should be stripped)
    ("<b>Bold</b> text", "Bold text"),
    ("<i>Italic</i> message", "Italic message"),
    ("<u>Underline</u> text", "Underline text"),
    ("<a href='url'>Link</a> text", "Link text"),
    ("<img src='icon.png' alt='icon'/> text", "text"),

    # Non-spec HTML tags (should be preserved - not in spec)
    ("Text with <br> break", "Text with <br> break"),
    ("<p>Paragraph</p> text", "<p>Paragraph</p> text"),

    # Discord/chat patterns (should be preserved)
    ("<spoiler>secret text</spoiler>", "<spoiler>secret text</spoiler>"),
    ("Hey <@user123>", "Hey <@user123>"),
    ("<@123456789> mentioned you", "<@123456789> mentioned you"),
    ("<#channel-name>", "<#channel-name>"),

    # Mixed content
    ("<b>Bold</b> and <spoiler>hidden</spoiler>", "Bold and <spoiler>hidden</spoiler>"),

    # HTML entities (should be decoded)
    ("&lt;3", "<3"),
    ("&amp; symbol", "& symbol"),
    ("&quot;quoted&quot;", '"quoted"'),

    # Edge cases
    ("Normal text", "Normal text"),
    ("Text < 5 and > 3", "Text < 5 and > 3"),
    ("", ""),
    (None, None),
]

print("Testing HTML handling:\n")
passed = 0
failed = 0

for i, (input_text, expected) in enumerate(test_cases, 1):
    result = strip_html(input_text)
    status = "✓" if result == expected else "✗"

    if result == expected:
        passed += 1
    else:
        failed += 1

    print(f"{status} Test {i}:")
    print(f"  Input:    {repr(input_text)}")
    print(f"  Expected: {repr(expected)}")
    print(f"  Got:      {repr(result)}")
    if result != expected:
        print(f"  FAILED!")
    print()

print(f"\nResults: {passed} passed, {failed} failed out of {len(test_cases)} tests")
sys.exit(0 if failed == 0 else 1)
