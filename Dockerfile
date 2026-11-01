FROM alpine:3.24.3@sha256:be2656061b536c1883c4034790e21d0a09c5aaaf51968b89368a3c0371ea2c9a

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
