#!/usr/bin/env python3
import os
import sys
import argparse
import socketio
import uuid
import signal

from urllib.parse import urlparse

sio = socketio.Client()


@sio.event
def connect_error(data):
    print("The connection failed!")


@sio.on('commandResponse')
def command_response(data):
    if data['stream'] == 'completed':
        sio.disconnect()
        sys.exit(data)
    if data['stream'] == 'stdout':
        sys.stdout.write(data['data'])
    if data['stream'] == 'stderr':
        sys.stderr.write(data['data'])


def sig_hanler(sig, fame):
    print('sending halt to server')
    commandRequest = {
        'id': 1,
        'type': 'halt'
    }
    sio.emit('message', data=('commandRequest', commandRequest))


def main():
    sample_usage = '''
If cmd is set to "performance", please include the following:

--performance-target, -t = target name or IP for the performance report
--performance-target-port, -p = target port (default is 11111)
--performance-run-count, -c = number of runs in the report
--performance-latency, -l =  include latency measurement in report
--performance-bandwidth, -b = include bandwidth measurement in report
--performance-source-label, -sl = your report source label
--performance-target-label, -tl = your report target label
 
 
'''

    ap = argparse.ArgumentParser(
        prog='demo-runner',
        usage='%(prog)s.py [options] url cmd',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        description='run a remote command on a demo-runner server',
        epilog=sample_usage
    )
    ap.add_argument(
        'url',
        help='target demo runner to perform command',
        nargs='?'
    )
    ap.add_argument(
        'cmd',
        help='command to run',
        nargs='?'
    )
    ap.add_argument(
        '-t', '--performance_target',
        help='target name or IP for the performance report',
        default=os.getenv('PERFORMANCE_TARGET', 'localhost')
    )
    ap.add_argument(
        '-p', '--performance_target_port',
        help='target port for the performance report',
        type=int,
        default=os.getenv('PERFORMACE_TARGET_PORT', 11111)
    )
    ap.add_argument(
        '-c', '--performance_run_count',
        help='number of performance tests in report',
        type=int,
        default=os.getenv('PERFORMANCE_RUN_COUNT', 1)
    )
    ap.add_argument(
        '-l', '--performance_latency',
        help='include latency stats in performance report',
        action='store_true'
    )
    ap.add_argument(
        '-b', '--performance_bandwidth',
        help='include bandwidth stats in the performance report',
        action='store_true'
    )
    ap.add_argument(
        '-sl', '--performance_source_label',
        help='performance source label in report',
        default=os.getenv('PERFORMANCE_SOURCE_LABEL', 'source')
    )
    ap.add_argument(
        '-tl', '--performance_target_label',
        help='performance target label in report',
        default=os.getenv('PERFORMANCE_SOURCE_LABEL', 'target')
    )

    args = ap.parse_args()

    latency = False
    if args.performance_latency:
        latency = True
    bandwidth = False
    if args.performance_bandwidth:
        bandwidth = True

    url = args.url
    if not args.url:
        url = os.getenv('URL', None)
    
    cmd = args.cmd
    if not cmd:
        cmd = os.getenv('CMD', None)
    
    if not url or not cmd:
        ap.print_help()
        print("URL and cmd arguments required\n\n")
        sys.exit(1)

    try:
        pu = urlparse(url)
        if pu.scheme not in ['http', 'https']:
            raise Exception('bad scheme')
    except:
        ap.print_help()
        print("INVALID URL: %s\n\n" % url)
        sys.exit(1)

    try:
        signal.signal(signal.SIGINT, sig_hanler)
        sio.connect(url)
        request_uuid = str(uuid.uuid4())
        if cmd == 'performance':
            commandRequest = {
                'id': request_uuid,
                'type': 'performance',
                'target': args.performance_target,
                'port': args.performance_target_port,
                'sourcelabel': args.performance_source_label,
                'targetlabel': args.performance_target_label,
                'runcount': int(args.performance_run_count),
                'latency': latency,
                'bandwidth': bandwidth,
                'cmd': ''
            }
            sio.emit('message', data=('commandRequest', commandRequest))
        else:
            commandRequest = {
                'id': request_uuid,
                'type': 'Running Command',
                'target': cmd,
                'cmd': cmd
            }
            sio.emit('message', data=('commandRequest', commandRequest))
    except Exception as ex:
        print("Unable to run command %s on %s - %s" % (cmd, url, ex))
        sys.exit(1)


if __name__ == "__main__":
    main()
