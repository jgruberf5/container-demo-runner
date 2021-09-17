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