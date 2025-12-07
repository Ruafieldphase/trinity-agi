#!/bin/bash
# Check if kmcaster is already running
if pgrep -f "kmcaster.jar" > /dev/null; then
    echo "KMCaster is already running!"
    exit 0
fi

# Start kmcaster
java -jar /home/bino/agi/tools/kmcaster.jar &
echo "KMCaster started!"

