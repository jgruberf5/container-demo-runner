#!/bin/bash

sockperf server --tcp --daemonize -m 1024000

dir=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

cd $dir
./app.py
