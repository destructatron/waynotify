#!/bin/bash
# Test script for WayNotify

echo "Testing WayNotify notification daemon..."
echo

echo "1. Sending basic notification..."
notify-send "Test Notification" "This is a basic test message"
sleep 2

echo "2. Sending urgent notification..."
notify-send -u critical "Urgent Alert" "This is an urgent notification!"
sleep 2

echo "3. Sending notification with icon..."
notify-send -i dialog-information "Information" "This notification has an icon"
sleep 2

echo "4. Sending notification with action..."
notify-send "Action Test" "This has a default action" -A "default=Click Me"
sleep 2

echo "5. Sending low priority notification..."
notify-send -u low "Background Task" "This is a low priority notification"
sleep 2

echo "6. Sending notification with body markup..."
notify-send "Markup Test" "<b>Bold text</b> and <i>italic text</i>"
sleep 2

echo "7. Sending persistent notification..."
notify-send -t 0 "Persistent" "This notification won't expire"
sleep 2

echo "8. Sending notification from different app..."
notify-send -a "CustomApp" "Custom Application" "This is from a custom app"
sleep 2

echo
echo "All test notifications sent!"
echo "Launch the client to view them: ../src/waynotify-client"
