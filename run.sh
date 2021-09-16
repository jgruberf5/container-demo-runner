#!/bin/bash

netserver -4 -N

dir=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

cd $dir
./app.py
