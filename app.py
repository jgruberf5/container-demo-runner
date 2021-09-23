#!/usr/bin/env python3

import json
import shlex
import subprocess
import yaml
import os
import signal
import psutil
import socket
import re
import base64
import dns.resolver

from urllib.parse import urlparse

from flask import Flask, request, render_template, Response, send_from_directory
from flask_compress import Compress
from flask_socketio import SocketIO, emit

from threading import Thread, Event

CONFIG_FILE = os.getenv('CONFIG_FILE', './config.yaml')
CONFIG_MAP_DIR = '/etc/container-demo-runner'
NAMESPACE_FILE = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'
PUPPETEER_HOME = os.getenv('PYPPETEER_HOME', '/tmp/webscreenshots')

config = {}

with open(CONFIG_FILE, 'r') as config_yaml:
    config = yaml.safe_load(config_yaml)

if os.path.exists(CONFIG_MAP_DIR):
    for ck in config.keys():
        if os.path.exists("%s/%s" % (CONFIG_MAP_DIR, ck)):
            with open("%s/%s" % (CONFIG_MAP_DIR, ck), 'r') as cmv:
                cv = cmv.read()
                if isinstance(config[ck], list):
                    try:
                        cv = json.loads(cv)
                        print(
                            'loading config setting: %s from ConfigMap value: %s' % (ck, cv))
                        config[ck] = cv
                    except json.JSONDecodeError as jde:
                        print('error reading %s from ConfigMap: ' % (ck, jde))
                else:
                    print(
                        'loading config setting: %s from ConfigMap value: %s' % (ck, cv))
                    config[ck] = cv

if 'host_entries' in config:
    with open('/etc/hosts', 'a+') as eh:
        eh.write('\n#### entries added by container-demo-runner ####\n')
        eh.write(config['host_entries'])
        eh.write('\n#### end entries added by container-demo-runner ####\n')

app = Flask(__name__)
Compress(app)
websocket = SocketIO(app, cors_allowed_origins='*', async_mode='threading')

pids_by_sid = {}
runners = {}


def root_dir():  # pragma: no cover
    return os.path.abspath(os.path.dirname(__file__))


def get_file(filename):  # pragma: no cover
    try:
        src = os.path.join(root_dir(), filename)
        return open(src, mode='rb').read()
    except IOError as exc:
        return str(exc)


def getHostname():
    hostname = socket.gethostname()
    print('found hostname: %s' % hostname)
    if os.path.exists(NAMESPACE_FILE):
        print('running in K8s, adding namespace to hostname')
        with open(NAMESPACE_FILE, 'r') as nsf:
            hostname = "%s/%s" % (
                re.sub(r"[\n\t\s]*", "", nsf.read()), hostname)
    return hostname


def getNameserver():
    nameserver = dns.resolver.Resolver().nameservers[0]
    print('found nameserver: %s' % nameserver)
    return nameserver


def stream_emitter(id, event, stream_type, stream):
    print("started background thread to stream %s" % stream_type)
    while not event.is_set():
        line = stream.readline()
        if not line or event.is_set():
            break
        response = {
            'id': id,
            'stream': stream_type,
            'data': line
        }
        websocket.emit('commandResponse', response, namespace='/')
    event.set()


def destroy_pid(pid):
    print('destroying process id: %d' % pid)
    if pid in runners.keys():
        process_runner = runners[pid]
        if process_runner['stdout_thread'].is_alive():
            process_runner['stdout_kill_event'].set()
        if process_runner['stderr_thread'].is_alive():
            process_runner['stderr_kill_event'].set()
        del process_runner['stdout_thread']
        del process_runner['stdout_kill_event']
        del process_runner['stderr_thread']
        del process_runner['stderr_kill_event']
        os.kill(pid, signal.SIGKILL)
        del runners[pid]


def destroy_all_processes_for_sid(sid):
    if sid in pids_by_sid.keys():
        for pid in pids_by_sid[sid]:
            if psutil.pid_exists(pid):
                destroy_pid(pid)
        del pids_by_sid[sid]


def command_allowed(cmd):
    if isinstance(cmd, list):
        cmd = shlex.join(cmd)
    allowed = False
    for regex in config['allowed_commands']:
        if re.match(r"%s" % regex, cmd):
            allowed = True
            break
    return allowed


def run_cmd(sid, cmd, id, env=None):
    destroy_all_processes_for_sid(sid)
    if isinstance(cmd, list):
        cmd = shlex.join(cmd)
    print('running cmd: %s with id: %s' % (cmd, id))
    process = subprocess.Popen(
        cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True, env=env)
    pids_by_sid[sid] = [process.pid]
    stdout_kill_event = Event()
    stderr_kill_event = Event()
    process_runner = {
        'stdout_kill_event': stdout_kill_event,
        'stdout_thread': websocket.start_background_task(
            stream_emitter, id, stdout_kill_event, 'stdout', process.stdout),
        'stderr_kill_event': Event(),
        'stderr_thread': websocket.start_background_task(
            stream_emitter, id, stderr_kill_event, 'stderr', process.stderr)
    }
    runners[process.pid] = process_runner
    process.wait()
    return process.returncode


def performance_test(sid, id, sourcelabel, targetlabel, target, port, runcount):
    destroy_all_processes_for_sid(sid)
    stdout_response = {
        'id': id,
        'stream': 'stdout',
        'data': "source_host, target_host, avg_latency_usec, 32k_throughput_mbits, 64k_throughput_mbits, 128k_throughput_mbits, 1M_throughput_mbits\n"
    }
    websocket.emit('commandResponse', stdout_response)
    try:
        for i in range(runcount):
            print('running performance test (%d/%d)' % ((i + 1), runcount))
            stdout_response = {
                'id': id,
                'stream': 'stdout',
                'data': "%s, %s, " % (sourcelabel, targetlabel)
            }
            websocket.emit('commandResponse', stdout_response)
            cmd = "sockperf ping-pong --tcp -i %s -p %d | grep avg-latency | cut -d' ' -f3 | cut -d'=' -f2" % (target, port)
            print('    test : %s' % cmd)
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True
            )
            pids_by_sid[sid] = [process.pid]
            output = process.communicate()[0].strip()
            stdout_response = {
                'id': id,
                'stream': 'stdout',
                'data': "%s, " % output
            }
            websocket.emit('commandResponse', stdout_response)
            cmd = "sockperf throughput --tcp -i %s -m 32768 -p %s | grep BandWidth | cut -d'(' -f2 | cut -d' ' -f1" % (
                target, port)
            print('    test : %s' % cmd)
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True
            )
            pids_by_sid[sid] = [process.pid]
            output = process.communicate()[0].strip()
            stdout_response = {
                'id': id,
                'stream': 'stdout',
                'data': "%s, " % output
            }
            websocket.emit('commandResponse', stdout_response)
            cmd = "sockperf throughput --tcp -i %s -m 65536 -p %s | grep BandWidth | cut -d'(' -f2 | cut -d' ' -f1" % (
                target, port)
            print('    test : %s' % cmd)
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True
            )
            pids_by_sid[sid] = [process.pid]
            output = process.communicate()[0].strip()
            stdout_response = {
                'id': id,
                'stream': 'stdout',
                'data': "%s, " % output
            }
            websocket.emit('commandResponse', stdout_response)
            cmd = "sockperf throughput --tcp -i %s -m 131072 -p %s | grep BandWidth | cut -d'(' -f2 | cut -d' ' -f1" % (
                target, port)
            print('    test : %s' % cmd)
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True
            )
            pids_by_sid[sid] = [process.pid]
            output = process.communicate()[0].strip()
            stdout_response = {
                'id': id,
                'stream': 'stdout',
                'data': "%s, " % output
            }
            websocket.emit('commandResponse', stdout_response)
            cmd = "sockperf throughput --tcp -i %s -m 1048575 -p %s | grep BandWidth | cut -d'(' -f2 | cut -d' ' -f1" % (
                target, port)
            print('    test : %s' % cmd)
            process = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True, universal_newlines=True
            )
            pids_by_sid[sid] = [process.pid]
            output = process.communicate()[0].strip()
            stdout_response = {
                'id': id,
                'stream': 'stdout',
                'data': "%s\n" % output
            }
            websocket.emit('commandResponse', stdout_response)
        return 0
    except Exception as e:
        error_response = {
            'id': id,
            'stream': 'stderr',
            'data': "error running test on target: %s - %s - %s.. \n\n" % (target, e.__class__.__name__, e)
        }
        print("commandResponse to %s: %s" %
              (error_response['stream'], error_response['data']))
        websocket.emit('commandResponse', error_response)
        return -1


@app.route('/')
def runner_ui():
    host = request.host
    if str.find(host, ':') > 0:
        host = str.split(host, ':')[0]
    banner_text = os.getenv('BANNER', '')
    banner_background_color = "#%s" % os.getenv('BANNER_COLOR', '000000')
    banner_text_color = '#%s' % os.getenv('BANNER_TEXT_COLOR', 'ffffff')
    return render_template(
        'index.html',
        hostname='connecting...',
        banner_text=(banner_text),
        banner_background_color=banner_background_color,
        banner_text_color=banner_text_color)


@app.route('/webscreenshots/<path:name>')
def send_screenshot(name):
    return send_from_directory(PUPPETEER_HOME, name, mimetype='image/jepg')


@app.route('/', defaults={'path': ''})
@app.route('/<path:path>')
def get_resource(path):  # pragma: no cover
    mimetypes = {
        ".css": "text/css",
        ".html": "text/html",
        ".js": "application/javascript",
        ".jpeg": "image/jpeg",
        ".ico": "image/x-icon"
    }
    complete_path = os.path.join(root_dir(), path)
    ext = os.path.splitext(path)[1]
    mimetype = mimetypes.get(ext, "text/html")
    content = get_file(complete_path)
    return Response(content, mimetype=mimetype)


@websocket.on('connect')
def client_connect():
    print('client connected with sid:' % request.sid)


@websocket.on('disconnect')
def client_disconnect():
    print('client disconnected with sid:' % request.sid)
    destroy_all_processes_for_sid(request.sid)


@websocket.on_error_default
def error_handler(e):
    print('socket IO error: %s' % e)


@websocket.on('message')
def message_handler(message, data):
    print('received message: %s:%s sid: %s' % (message, data, request.sid))
    if message == 'commandRequest':
        if data['type'] == 'variable':
            print('setting client variable: %s with command: %s' %
                  (data['target'], data['cmd']))
            response = {
                'variableName': data['target'],
                'variableValue': None
            }
            if data['cmd'][0] == 'hostname':
                response['variableValue'] = getHostname()
            if data['cmd'][0] == 'nameserver':
                response['variableValue'] = getNameserver()
            emit('variableResponse', response)
        elif data['type'] == 'performance':
            print('running performance test with target: %s:%d' %
                  (data['target'], int(data['port'])))
            try:
                data['target'] = socket.gethostbyname(data['target'])

                exit_code = performance_test(
                    request.sid, data['id'], data['sourcelabel'], data['targetlabel'], data['target'], int(data['port']), int(data['runcount']))
                complete_response = {
                    'id': data['id'],
                    'stream': 'completed',
                    'data': exit_code
                }
                print("commandResponse to %s: %s" %
                      (complete_response['stream'], complete_response['data']))
                emit('commandResponse', complete_response)
            except Exception as e:
                error_response = {
                    'id': data['id'],
                    'stream': 'stderr',
                    'data': "target: %s is not valid. %s - %s\n\n" % (data['target'], e.__class__.__name__, e)
                }
                print("commandResponse to %s: %s" %
                      (error_response['stream'], error_response['data']))
                emit('commandResponse', error_response)
                complete_response = {
                    'id': data['id'],
                    'stream': 'completed',
                    'data': -1
                }
                print("commandResponse to %s: %s" %
                      (complete_response['stream'], complete_response['data']))
                emit('commandResponse', complete_response)
        elif data['type'] == 'halt':
            destroy_all_processes_for_sid(request.sid)
            complete_response = {
                'id': data['id'],
                'stream': 'completed',
                'data': 0
            }
            emit('commandResponse', complete_response)
        elif data['type'] == 'webscreenshot':
            print('getting web screen shot for: %s' % data['target'])
            try:
                if not os.path.exists:
                    os.makedirs(PUPPETEER_HOME)
                urlparse(data['target'])
                scripting_path = os.path.dirname(os.path.realpath(__file__))
                snapshot_file_name = "%s.jpg" % base64.b64encode(
                    data['target'].encode()).decode()
                snapshot_file_path = "%s/%s" % (
                    PUPPETEER_HOME, snapshot_file_name)
                cmd = "%s/web_screenshot.py --url '%s' --screenshot '%s'" % (
                    scripting_path, data['target'], snapshot_file_path)
                print('running command: %s' % cmd)
                env = {'PYPPETEER_HOME': PUPPETEER_HOME}
                exit_code = run_cmd(request.sid, cmd, data['id'], env)
                display_response = {
                    'id': data['id'],
                    'stream': 'image',
                    'data': "/webscreenshots/%s" % snapshot_file_name
                }
                print("commandResponse to %s: %s" %
                      (display_response['stream'], display_response['data']))
                emit('commandResponse', display_response)
                complete_response = {
                    'id': data['id'],
                    'stream': 'completed',
                    'data': exit_code
                }
                print("commandResponse to %s: %s" %
                      (complete_response['stream'], complete_response['data']))
                emit('commandResponse', complete_response)
            except Exception as e:
                error_response = {
                    'id': data['id'],
                    'stream': 'stderr',
                    'data': "url: %s is not valid. %s - %s\n\n" % (data['cmd'], e.__class__.__name__, e)
                }
                print("commandResponse to %s: %s" %
                      (error_response['stream'], error_response['data']))
                emit('commandResponse', error_response)
                complete_response = {
                    'id': data['id'],
                    'stream': 'completed',
                    'data': -1
                }
                print("commandResponse to %s: %s" %
                      (complete_response['stream'], complete_response['data']))
                emit('commandResponse', complete_response)
        else:
            if command_allowed(data['cmd']):
                exit_code = run_cmd(request.sid, data['cmd'], data['id'])
                complete_response = {
                    'id': data['id'],
                    'stream': 'completed',
                    'data': exit_code
                }
                print("commandResponse to %s: %s" %
                      (complete_response['stream'], complete_response['data']))
                emit('commandResponse', complete_response)
            else:
                error_response = {
                    'id': data['id'],
                    'stream': 'stderr',
                    'data': "command: %s is not allowed on server." % data['cmd']
                }
                print("commandResponse to %s: %s" %
                      (error_response['stream'], error_response['data']))
                emit('commandResponse', error_response)
                complete_response = {
                    'id': data['id'],
                    'stream': 'completed',
                    'data': -1
                }
                print("commandResponse to %s: %s" %
                      (complete_response['stream'], complete_response['data']))
                emit('commandResponse', complete_response)
    else:
        print("recieved unknown message: %s:%s" % (message, data))


if __name__ == "__main__":
    websocket.run(
        app,
        host=config['http_listen_address'],
        port=int(config['http_listen_port'])
    )
