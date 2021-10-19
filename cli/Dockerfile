FROM python:3.8-slim
LABEL maintainer="John Gruber <j.gruber@f5.com>"

WORKDIR /

RUN apt-get update && \
    apt-get install --no-install-recommends -y git

RUN git clone https://github.com/jgruberf5/container-demo-runner.git
RUN pip3 install python-socketio requests websocket-client

ENV URL '--help'
ENV CMD ''

ENV PERFORMANCE_TARGET "localhost"
ENV PERFORMACE_TARGET_PORT 11111
ENV PERFORMANCE_RUN_COUNT 1
ENV PERFORMANCE_SOURCE_LABEL "source"
ENV PERFORMANCE_SOURCE_LABEL "target"


ENTRYPOINT [ "/container-demo-runner/cli/demo-runner.py"]