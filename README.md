# container-demo-runner

## Containerized Remote Execution Service for Demonstration and Troubleshooting

This container hosts a web service and websocket service which enable exposure of the container's environment through a web interface.

By default the web interface and web socket services are started on port 8080. 

```bash
docker run --rm -p 8080:8080 -p 5001:5001 -p 11111:11111 --name container-demo-runner jgruberf5/container-demo-runner:latest
```

Then open a web browser to `http://localhost:8080` .

![Application Screenshot](https://github.com/jgruberf5/container-demo-runner/raw/main/static/application_screenshot.png)

The UI will show the remote hostname (or K8s namespace/hostname) in green in the top right corner when the service is connected. The settings (gear) icon in the top far right will let you change which backend websocket command host you are connected to.

## Configuration

The services will look for the presence of a `/etc/config.yaml` file. The default configuration YAML is as follows:

```yaml
---
ws_listen_address: 0.0.0.0
ws_listen_port: 8080
http_listen_address: 0.0.0.0
http_listen_port: 8080
allowed_commands:
  - "^ping"
  - "^cat /etc/hosts"
  - "^cat /etc/resolv.conf"
  - "^env$"
  - "^ip route$"
  - "^ip addr$"
  - "^ip link$"
  - "^ip neigh"
  - "^netstat"
  - "^dig"
  - "^nc"
  - "^ab"
  - "^siege"
  - "^tcping"
  - "^traceroute"
  - "^tcptraceroute"
  - "^curl"
  - "^whois"
  - "^kubectl"
  - "^sockperf"
  - "^iperf"
  - "^iperf3"
#host_entries: |
#  104.21.192.109    ifconfig.io
```

The `allowed_commands` list is a list of regular expressions which each requested command will be mapped against before the command is executed within the container.

When used in a K8s manifest YAML, create a JSON list using a multi-line text attribute to alter your `allowed_commands`.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: container-demo-runner-config
data:
  http_listen_address: "0.0.0.0"
  http_listen_port: "8080"
  ws_listen_address: "0.0.0.0"
  ws_listen_port: "5678"
  allowed_commands: |
    ["^ping", "^cat /etc/hosts", "^cat /etc/resolv.conf", "^env$", "^ip route$", "^ip addr$", "^ip link$", "^ip neigh", "^netstat", "^dig", "^nc", "^ab", "^siege", "^tcping", "^traceroute", "^tcptraceroute", "^curl", "^whois", "^kubectl", "^sockperf", "^iperf", "^iperf3"]
  host_entries: |
    104.21.192.109    ifconfig.io
```

The `host_entries` multi-line text attribute will be appended to `/etc/hosts`. If you plan on adding `host_entries` the container will need to be privledged to run as `root` (user 0).

## Preconfigured Command Runners

The web UI includes buttons and forms to run some preconfigured commands.

| Button | Command Run |
| ---------- | ---------- |
| *Show Routes* | `ip route` |
| *Show IP addresses* | `ip addr` |
| *Show Hosts* | `cat /etc/hosts` |
| *Show Environment* | `env` |
| *ICMP Ping* | `ping -c [count from form] [host from form]` |
| *TCP Ping* | `tcping -c [count from form] [host from form]` |
| *DNS Lookup* | `dig [FQDN from form] [type from form]` |
| *HTTP GET* | `curl -H "Connection: close" -k -L -s -o /dev/null -w " http_status_code: %{http_code}\n content_type: %{content_type}%\n dns_resolution: %{time_namelookup}\n tcp_established: %{time_connect}\n ssl_handshake_done: %{time_appconnect}\n TTFB: %{time_starttransfer}\n speed_download: %{speed_download}\n speed_upload: %{speed_upload}\n total_time: %{time_total}\n size: %{size_download}\n\n" [url from form]`|
| *Web Screenshot* | `web_screenshot.py --url [url from form]` |

You can run any included commands which regex matches your `/etc/config.yaml` file `allowed_commands` list. If the container does not include a CLI utility you need, add the appropriate Ubuntu package (or install via other means) in your `Dockerfile` and rebuild the container.

You can run various commands by using the *Run Command* form in the web UI.

## Monitoring Kubernetes from Inside a K8s Cluster

The included K8s manifest creates a service account which has `["get", "watch", "list"]` access to `["pods", "services", "namespaces", "deployments", "jobs", "statefulsets", "persistentvolumeclaims"]`. The included `kubectl` will use the `load_incluster_config` to access the K8s API endpoint defined in the environment.

## Doing Load Testing

The image includes the `ab` (apache bench) client and the `siege` web load testing tools. You can utilize these tools by using the *Run Command* form in the web UI.

The image also includes the `iperf` network performance tool. By default `iperf` uses port 5001. You will need to include a port forward to the `iperf` listener. The included K8s manifest will create both an `NodePort` and `ClusterIP` service for `iperf` port 5001. You can utilize `iperf` by using the *Run Command* form in the web UI.

## Visual Banners

The main index page will show a visual banner if the following environment variables are defined.

| Environement Variable | Description |
| ---------- | ---------- |
| BANNER | The text of the Banner to Display |
| BANNER_COLOR | The background collor of your banner in 'rrggbb' hex format. ie: ff0000 for bright red |
| BANNER_TEXT_COLOER | The text collor for your banner in 'rrggbb' hex format. ie: ffffff for white lettering |

## Command Line Client Scripting

The repository also includes a command line web service client. To run the command line client from the repository `cli` directory run:

```bash
pip3 install -r requirements.txt
./demo-runner.py
```

There is also a `Dockerfile` in the `cli` directory that can be used to build a container of the command line client.

```bash
docker build --rm -t container-demo-cli:latest .
```

Once built, the container client can be run via docker command. If you include the `-i` and `-t` output and arguments will be interactive with your current shell.

```bash
docker run -i -t --rm container-demo-cli:latest 'http://ibm-k8s-us-east-1.appinsights.io:30080' 'ping -c 5 www.google.com'
```

Default options can be seen by issuing the `--help` argument:

```bash
$ ./demo-runner.py --help
```

or

```bash
$ docker run -i -t --rm container-demo-cli:latest --help
```

```bash
usage: demo-runner.py [options] url cmd

run a remote command on a demo-runner server

positional arguments:
  url                   target demo runner to perform command
  cmd                   command to run

optional arguments:
  -h, --help            show this help message and exit
  -t PERFORMANCE_TARGET, --performance_target PERFORMANCE_TARGET
                        target name or IP for the performance report
  -p PERFORMANCE_TARGET_PORT, --performance_target_port PERFORMANCE_TARGET_PORT
                        target port for the performance report
  -c PERFORMANCE_RUN_COUNT, --performance_run_count PERFORMANCE_RUN_COUNT
                        number of performance tests in report
  -l, --performance_latency
                        include latency stats in performance report
  -b, --performance_bandwidth
                        include bandwidth stats in the performance report
  -sl PERFORMANCE_SOURCE_LABEL, --performance_source_label PERFORMANCE_SOURCE_LABEL
                        performance source label in report
  -tl PERFORMANCE_TARGET_LABEL, --performance_target_label PERFORMANCE_TARGET_LABEL
                        performance target label in report

If cmd is set to "performance", please include the following:

--performance-target, -t = target name or IP for the performance report
--performance-target-port, -p = target port (default is 11111)
--performance-run-count, -c = number of runs in the report
--performance-latency, -l =  include latency measurement in report
--performance-bandwidth, -b = include bandwidth measurement in report
--performance-source-label, -sl = your report source label
--performance-target-label, -tl = your report target label

```

You can run a command by targetting the running container server by URL as the first argument and the command to run as the second argument. If the command is allowed on the remote server, it will be executed from the remote contain and the `stdout` and `stderr` will be sent to your terminal `stdout` and `stderr`.

```bash
$ ./demo-runner.py http://ibm-k8s-us-east-1.appinsights.io 'ping -c 5 www.google.com'
PING www.google.com (142.250.68.132) 56(84) bytes of data.
64 bytes from dfw28s27-in-f4.1e100.net (142.250.68.132): icmp_seq=1 ttl=116 time=30.8 ms
64 bytes from dfw28s27-in-f4.1e100.net (142.250.68.132): icmp_seq=2 ttl=116 time=30.8 ms
64 bytes from dfw28s27-in-f4.1e100.net (142.250.68.132): icmp_seq=3 ttl=116 time=30.8 ms
64 bytes from dfw28s27-in-f4.1e100.net (142.250.68.132): icmp_seq=4 ttl=116 time=30.8 ms
64 bytes from dfw28s27-in-f4.1e100.net (142.250.68.132): icmp_seq=5 ttl=116 time=30.8 ms

--- www.google.com ping statistics ---
5 packets transmitted, 5 received, 0% packet loss, time 4006ms
rtt min/avg/max/mdev = 30.790/30.823/30.840/0.018 ms
```

Running client test in the container is just as easy:

```bash
docker run -i -t --rm container-demo-cli:latest http://ibm-k8s-us-east-1.appinsights.io 'ping -c 5 www.google.com'
PING www.google.com (142.250.115.103) 56(84) bytes of data.
64 bytes from rq-in-f103.1e100.net (142.250.115.103): icmp_seq=1 ttl=105 time=30.5 ms
64 bytes from rq-in-f103.1e100.net (142.250.115.103): icmp_seq=2 ttl=105 time=30.5 ms
64 bytes from rq-in-f103.1e100.net (142.250.115.103): icmp_seq=3 ttl=105 time=30.5 ms
64 bytes from rq-in-f103.1e100.net (142.250.115.103): icmp_seq=4 ttl=105 time=30.5 ms
64 bytes from rq-in-f103.1e100.net (142.250.115.103): icmp_seq=5 ttl=105 time=30.4 ms
```


If you want to run the embedded performance test, there are addition command line options to define to format the output report.


```bash
$ ./demo-runner.py http://ibm-k8s-us-east-1.appinsights.io  performance -sl k8s_dc -tl k8s_dallas -t sockperf-in-dallas.ves-system -p 11112 -c 10 -l -b 2>/dev/null
source_host, target_host, avg_latency_usec, 32k_throughput_mbits, 64k_throughput_mbits, 128k_throughput_mbits, 1M_throughput_mbits
k8s_dc, k8s_dallas, 15724.503, 206.500, 193.500, 276.000, 200.000
k8s_dc, k8s_dallas, 16308.453, 266.500, 189.000, 270.000, 280.000
k8s_dc, k8s_dallas, 22197.107, 270.000, 195.500, 194.000, 200.000
k8s_dc, k8s_dallas, 21993.921, 297.250, 210.500, 303.000, 232.000
k8s_dc, k8s_dallas, 15645.346, 314.250, 214.000, 319.000, 320.000
k8s_dc, k8s_dallas, 15745.421, 240.000, 141.000, 288.000, 216.000
k8s_dc, k8s_dallas, 22202.887, 205.750, 300.500, 216.000, 192.000
k8s_dc, k8s_dallas, 15694.005, 272.500, 271.500, 162.000, 264.000
k8s_dc, k8s_dallas, 22040.820, 183.500, 194.000, 271.000, 184.000
k8s_dc, k8s_dallas, 21961.309, 165.000, 167.000, 253.000, 176.000
```

## Running the Same Test as the Web Client

The web interface has some pre-built commands to run. You can get the same results by issuing the commands below:

| Web Command | CLI Command |
| ---------- | ---------- |
| Show Routes | `ip route` |
| Show IP addresses | `ip addr` |
| Show Hosts | `cat /etc/hosts` |
| Show Environment | `env` |
| Show Resolver | `cat /etc/resolv.conf` |
| ICMP Ping | `ping -c [count] [target]` |
| TCP Ping | `tcping -x [count] [target] [port]` |
| DNS Lookup | `dig @[dnshost] [target] [type]` |
| HTTP GET (statistics) | `curl -H 'Connection: close' -k -L -s -o '/dev/null' -w ' http_status_code: %{http_code}\n content_type: %{content_type}%\n dns_resolution: %{time_namelookup}\n tcp_established: %{time_connect}\n ssl_handshake_done: %{time_appconnect}\n TTFB: %{time_starttransfer}\n speed_download: %{speed_download}\n speed_upload: %{speed_upload}\n total_time: %{time_total}\n size: %{size_download}\n\n' [url]`