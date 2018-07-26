#!/bin/bash

USAGE="Usage: $0 FILEPATH"
EXAMPLE="Example: $0 measure_result/iostat.txt"

if [ $# -ne 1 ]; then
    echo "Invalid number of arguments. (!=1)" >&2
    echo $USAGE
    echo $EXAMPLE
    exit 1
fi

FILEPATH=$1

grep -m 1 "avg-cpu" $FILEPATH | sed -e 's/avg-cpu:\s\+//' | sed -e "s/\s\+/\t/g"
grep -n "avg-cpu" $FILEPATH | awk -F: '{print $1+1}' | xargs | sed -e 's/ /p;/g' | awk -v filepath="${FILEPATH}" '{print "sed -n \x27" $1 "p\x27 " filepath}' | bash | sed -e "s/^\s\+//g" | sed -e "s/\s\+/\t/g"
