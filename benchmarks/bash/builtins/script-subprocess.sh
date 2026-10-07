#!/usr/bin/env bash
# Summarizes an access log: requests per status code and total bytes sent.
# Usage: ./script.sh access.log   (sample: access.log in this folder)

LOG="$1"

total_lines=$(cat "$LOG" | wc -l)
echo "Lines: $total_lines"

total_bytes=0
count_2xx=0
count_4xx=0
count_5xx=0

while read line; do
    status=$(echo "$line" | cut -d' ' -f9)
    bytes=$(echo "$line" | cut -d' ' -f10)
    if [ "$bytes" = "-" ]; then
        bytes=0
    fi
    total_bytes=$(expr $total_bytes + $bytes)

    class=$(echo "$status" | cut -c1)
    if [ "$class" = "2" ]; then
        count_2xx=$(expr $count_2xx + 1)
    elif [ "$class" = "4" ]; then
        count_4xx=$(expr $count_4xx + 1)
    elif [ "$class" = "5" ]; then
        count_5xx=$(expr $count_5xx + 1)
    fi
done < "$LOG"

echo "2xx: $count_2xx"
echo "4xx: $count_4xx"
echo "5xx: $count_5xx"
echo "Bytes: $total_bytes"
echo "Log file: $(basename $LOG)"
