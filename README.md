# container-demo-runner

**Containerized Remote Execution Service for Demonstration and Troubleshooting**

This container hosts a web service and websocket service which enable exposure of the container's environment through a web interface.

By default the web interface is started on port 8080 and the websocket command runner is started on port 5678. 

```bash
docker run --rm -p 8080:8080 -p 5678:5678 --name container-demo-runner jgruberf5/container-demo-runner:latest
```

Then open a web browser to http://localhost:8080 .

![Application Screenshot](https://github.com/jgruberf5/container-demo-runner/raw/main/static/application_screenshot.png)


## Configuration

The services will look for the presence of a `/etc/config.yaml` file. The default configuration YAML is as follows:

```yaml
---
ws_listen_address: 0.0.0.0
ws_listen_port: 5678
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
  - "^iperf"
host_entries: |
  104.21.192.109    ifconfig.io
```

The `allowed_commands` list is a list of regular expressions which each requested command will be mapped against before the command is executed within the container.

When using in a K8s manifest YAML, create a JSON list using a multi-line text attribute to alter your `allowed_commands`.

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
    ["^ping", "^cat /etc/hosts", "^cat /etc/resolv.conf", "^env$", "^ip route$", "^ip addr$", "^ip link$", "^ip neigh", "^netstat", "^dig", "^nc", "^ab", "^siege", "^tcping", "^traceroute", "^tcptraceroute", "^curl", "^whois", "^kubectl", "^iperf"]
  host_entries: |
    104.21.192.109    ifconfig.io
```

The `host_entries` multi-line text attribute will be appended to `/etc/hosts`.
