#!/usr/bin/env python3

import asyncio
import websockets
import shlex
import json
import yaml
import os
import re

CONFIG_FILE = os.getenv('CONFIG_FILE', './config.yaml')
if os.path.exists('/etc/config.yaml'):
    CONFIG_FILE = '/etc/config.yaml'

config = {}

with open(CONFIG_FILE, 'r') as config_yaml:
    config = yaml.safe_load(config_yaml)


async def _stream_to_ws(stream, header, socket):
    while True:
        line = await stream.readline()
        if line:
            await socket.send(json.dumps({'stream': header, 'data': line.decode()}))
        else:
            break


async def runner(socket, path='/'):
    try:
        rawdata = await socket.recv()
        data = json.loads(rawdata)
        cmd = data['cmd']
        if isinstance(data['cmd'], list):
            cmd = shlex.join(data['cmd'])
        allowed = False
        for regex in config['allowed_commands']:
            if re.match(r"%s" % regex, cmd):
                allowed=True
                break
        if allowed:
            process=await asyncio.create_subprocess_shell(
                cmd, stdout = asyncio.subprocess.PIPE, stderr = asyncio.subprocess.PIPE)
            await asyncio.wait([
                _stream_to_ws(process.stdout, 'stdout', socket),
                _stream_to_ws(process.stderr, 'stderr', socket)
            ])
            await socket.send(json.dumps({'stream': 'completed', 'data': process.returncode}))
        else:
            await socket.send(json.dumps({'stream': 'stderr', 'data': "command: %s is not allowed." % cmd}))
            await socket.send(json.dumps({'stream': 'completed', 'data': 1}))
    except json.JSONDecodeError:
        print("invalid request from client: %s" % rawdata)
    except websockets.exceptions.ConnectionClosed:
        print("client disconnected")


start_server=websockets.serve(
    runner, config['ws_listen_address'], config['ws_listen_port'])
asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
