#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
if [ -f $DIR/multilat.so ]
then
    echo ""
else
    gcc -c -fPIC -O3 $DIR/multilat.c
    gcc -shared -o $DIR/multilat.so $DIR/multilat.o
fi
if [ -f $DIR/multilat.so ]
then
    python3 $DIR/ips.py
fi
