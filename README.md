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
- "^ip route$"
- "^ip addr$"
- "^ip link$"
- "^ip neigh"
- "^netstat"
- "^dig"
- "^traceroute"
- "^curl"
- "^whois"
- "^kubectl"
- "^iperf"
```

The `allowed_commands` list is a list of regular expressions which each requested command will be mapped against before the command is executed within the container.
