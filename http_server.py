#!/usr/bin/env python3

import json
import yaml
import os
import socket
import re

from flask import Flask, request, render_template, Response

CONFIG_FILE = os.getenv('CONFIG_FILE', './config.yaml')
if os.path.exists('/etc/config.yaml'):
    CONFIG_FILE = '/etc/config.yaml'

NAMESPACE_FILE = '/var/run/secrets/kubernetes.io/serviceaccount/namespace'

config = {}

with open(CONFIG_FILE, 'r') as config_yaml:
    config = yaml.safe_load(config_yaml)

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
    return render_template(
        'index.html', host=host, port=config['ws_listen_port'], hostname=hostname)


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
            port=config['http_listen_port'])
