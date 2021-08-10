#!/bin/bash

dir=$(cd -P -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)

cd $dir

./ws_runner.py &
web_socket_runner=$!

trap onexit INT

function onexit() {
    echo "exiting websocker command runner"
    kill -9 $web_socket_runner
}

./http_server.py
