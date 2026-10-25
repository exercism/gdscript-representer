FROM alpine:3.24.2@sha256:294b683cb724975bec92580e1e685676bd4b50bda910ddb8c51d4cabeaec77e6

RUN apk add --no-cache python3 py3-pip
RUN pip install --user --break-system-packages 'gdtoolkit == 4.5.0'
# gdtoolkit pins an older lark release. Force a newer version.
RUN pip install --user --break-system-packages --no-deps 'lark == 1.3.1'

# Load and cache the gdscipt grammar
RUN python3 -c 'import gdtoolkit.parser; gdtoolkit.parser.parser.parse("")'

# Everything prior to this line should be synced with gdscript-analyzer/Dockerfile

WORKDIR /opt/representer

COPY bin/run.sh bin/run.sh
COPY bin/run.py bin/run.py

ENTRYPOINT ["/opt/representer/bin/run.sh"]
