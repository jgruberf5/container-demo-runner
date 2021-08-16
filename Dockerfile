FROM ubuntu:20.04
LABEL maintainer="John Gruber <j.gruber@f5.com>"

WORKDIR /

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && \
    apt-get install --no-install-recommends -y \
    apt-transport-https \
    ca-certificates \
    iputils-ping \
    tcptraceroute \
    hping3 \
    nmap \
    bc \
    dnsutils \
    jq \
    apache2-utils \
    siege \
    curl \
    net-tools \
    netcat \
    iperf \
    traceroute \
    python3-pycurl \
    python3-yaml \
    python3-flask \
    python3-flask-socketio \
    python3-psutil \
    python3-eventlet \
    iproute2 \
    git

RUN curl http://www.vdberg.org/~richard/tcpping -o /usr/bin/tcping && chmod 755 /usr/bin/tcping

RUN curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list && \
    apt-get update && \
    apt-get install -u kubectl

RUN git clone https://github.com/jgruberf5/container-demo-runner.git

EXPOSE 8080
EXPOSE 5001

ENTRYPOINT [ "/container-demo-runner/run.sh" ]