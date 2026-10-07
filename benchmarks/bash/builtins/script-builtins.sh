#!/usr/bin/env bash
# Optimized variant of test-cases/bash/builtins/script.sh: shell builtins only, no subprocess per line.
# Usage: ./script-builtins.sh access.log

LOG="$1"

total_lines=$(wc -l < "$LOG")
echo "Lines: $total_lines"

total_bytes=0
count_2xx=0
count_4xx=0
count_5xx=0

while read -r _ _ _ _ _ _ _ _ status bytes _; do
    [[ $bytes == "-" ]] && bytes=0
    (( total_bytes += bytes ))
    case $status in
        2*) (( count_2xx += 1 )) ;;
        4*) (( count_4xx += 1 )) ;;
        5*) (( count_5xx += 1 )) ;;
    esac
done < "$LOG"

echo "2xx: $count_2xx"
echo "4xx: $count_4xx"
echo "5xx: $count_5xx"
echo "Bytes: $total_bytes"
echo "Log file: ${LOG##*/}"
