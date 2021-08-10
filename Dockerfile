FROM ubuntu:20.04
LABEL maintainer="John Gruber <j.gruber@f5.com>"

WORKDIR /

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    ca-certificates \
    iputils-ping \
    dnsutils \
    curl \
    net-tools \
    iperf \
    traceroute \
    kubectl \
    python3-pycurl \
    python3-yaml \
    python3-flask \
    python3-websockets \
    iproute2 \
    git

RUN git clone https://github.com/jgruberf5/container-demo-runner.git

EXPOSE 8080
EXPOSE 5678
EXPOSE 5001

ENTRYPOINT [ "/container-demo-runner/run.sh" ]