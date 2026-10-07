#!/usr/bin/env bash
# Optimized variant of test-cases/bash/builtins/script.sh: the whole file in a single awk pass.
# Usage: ./script-awk.sh access.log

LOG="$1"

awk '
    {
        class = substr($9, 1, 1)
        if (class == "2") c2++
        else if (class == "4") c4++
        else if (class == "5") c5++
        if ($10 != "-") bytes += $10
    }
    END {
        printf "Lines: %d\n2xx: %d\n4xx: %d\n5xx: %d\nBytes: %.0f\n", NR, c2, c4, c5, bytes
    }' "$LOG"
echo "Log file: ${LOG##*/}"
