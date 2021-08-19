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
    netbase \
    iperf \
    traceroute \
    iproute2 \
    python3-pip \
    git \
    install \
    gconf-service \
    libasound2 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libc6 \
    libcairo2 \
    libcups2 \
    libdbus-1-3 \
    libexpat1 \
    libfontconfig1 \
    libgcc1 \
    libgconf-2-4 \
    libgdk-pixbuf2.0-0 \
    libglib2.0-0 \
    libgtk-3-0 \
    libnspr4 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libstdc++6 \
    libx11-6 \
    libx11-xcb1 \
    libxcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxext6 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxrender1 \
    libxss1 \
    libxtst6 \
    fonts-liberation \
    libappindicator1 \
    libnss3 \
    lsb-release \
    xdg-utils \
    wget

RUN curl http://www.vdberg.org/~richard/tcpping -o /usr/bin/tcping && chmod 755 /usr/bin/tcping

RUN curl -fsSLo /usr/share/keyrings/kubernetes-archive-keyring.gpg https://packages.cloud.google.com/apt/doc/apt-key.gpg && \
    echo "deb [signed-by=/usr/share/keyrings/kubernetes-archive-keyring.gpg] https://apt.kubernetes.io/ kubernetes-xenial main" | tee /etc/apt/sources.list.d/kubernetes.list && \
    apt-get update && \
    apt-get install -u kubectl

RUN git clone https://github.com/jgruberf5/container-demo-runner.git

RUN pip3 install -r /container-demo-runner/requirements.txt

EXPOSE 8080
EXPOSE 5001

ENTRYPOINT [ "/container-demo-runner/run.sh" ]