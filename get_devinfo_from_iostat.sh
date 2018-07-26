#!/bin/bash

USAGE="Usage: $0 DEV FILEPATH"
EXAMPLE="Example: $0 sda measure_result/iostat.txt"

if [ $# -ne 2 ]; then
    echo "Invalid number of arguments. (!=2)" >&2
    echo $USAGE
    echo $EXAMPLE
    exit 1
fi

DEVICE=$1
FILEPATH=$2

grep -m 1 "Device" $FILEPATH | sed -e 's/Device:\s\+//' | sed -e "s/\s\+/\t/g"
grep "$DEVICE" $FILEPATH | sed -e "s/$DEVICE\s\+//" | sed -e 's/\s\+/\t/g'
