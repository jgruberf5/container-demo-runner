#!/usr/bin/env python3

import json
import yaml
import os
import socket
import re

from flask import Flask, request, render_template, Response

CONFIG_FILE = os.getenv('CONFIG_FILE', './config.yaml')
CONFIG_MAP_DIR = '/etc/container-demo-runner'
NAMESPACE_FILE = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'

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
                        pass
                        ''' cv = json.loads(cmv.read())
                        print(
                            'loading config setting: %s from ConfigMap value: %s' % (ck, cv))
                        config[ck] = cv '''
                    except json.JSONDecodeError as jde:
                        print('error reading %s from ConfigMap: ' % (ck, jde))
                else:
                    print(
                        'loading config setting: %s from ConfigMap value: %s' % (ck, cv))
                    config[ck] = cv


app = Flask(__name__)


def root_dir():  # pragma: no cover
    return os.path.abspath(os.path.dirname(__file__))


def get_file(filename):  # pragma: no cover
    try:
        src = os.path.join(root_dir(), filename)
        return open(src, mode='rb').read()
    except IOError as exc:
        return str(exc)


@app.route('/')
def runner_ui():
    host = request.host
    if str.find(host, ':') > 0:
        host = str.split(host, ':')[0]
    hostname = socket.gethostname()
    if os.path.exists(NAMESPACE_FILE):
        with open(NAMESPACE_FILE, 'r') as nsf:
            hostname = "%s/%s" % (re.sub(r"[\n\t\s]*",
                                  "", nsf.read()), hostname)
    port = int(os.getenv('WS_CLIENT_PORT', config['ws_listen_port']))
    return render_template(
        'index.html', host=host, port=port, hostname=hostname)


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


if __name__ == "__main__":
    app.run(host=config['http_listen_address'],
            port=int(config['http_listen_port']))
