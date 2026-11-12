#!/bin/bash
# Monitor running experiments

echo "================================"
echo "EXPERIMENT PROGRESS MONITOR"
echo "================================"
echo ""

# Check running processes
echo "Running processes:"
ps aux | grep -E "run_(championship|framebreak|language_test)" | grep -v grep | awk '{print "  " $11, "(PID:", $2 ")"}'
echo ""

# Count completed rounds
echo "Rounds completed:"
echo "  Championship:  $(ls results/championship/rounds 2>/dev/null | wc -l | tr -d ' ')/150 ($(ls results/championship/rounds 2>/dev/null | wc -l | awk '{print int($1/150*100)}')%)"
echo "  Frame Break:   $(ls results/framebreak/rounds 2>/dev/null | wc -l | tr -d ' ')/90  ($(ls results/framebreak/rounds 2>/dev/null | wc -l | awk '{print int($1/90*100)}')%)"
echo "  Language Test: $(ls results/language_test/rounds 2>/dev/null | wc -l | tr -d ' ')/90  ($(ls results/language_test/rounds 2>/dev/null | wc -l | awk '{print int($1/90*100)}')%)"
echo ""

# Check latest log activity
echo "Latest log activity:"
for exp in championship frame_break language_test; do
    latest_log=$(ls -t logs/${exp}_*.log 2>/dev/null | head -1)
    if [ -f "$latest_log" ]; then
        size=$(du -h "$latest_log" | awk '{print $1}')
        echo "  ${exp}: $size ($(basename $latest_log))"
        if [ -s "$latest_log" ]; then
            echo "    Last line: $(tail -1 $latest_log 2>/dev/null | head -c 80)"
        fi
    fi
done
echo ""

echo "================================"
echo "Monitor again: ./monitor_experiments.sh"
echo "View logs: tail -f logs/championship_*.log"
echo "================================"
