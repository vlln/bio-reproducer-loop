FROM ghcr.io/prefix-dev/pixi:0.72.2@sha256:008522050e595a65f6ace804d6159c677afedf22dd9396c820b2668d98551844 AS pixi

FROM python:3.10-slim@sha256:c1e4e6c01eb489c422288b2de34b0761ca316f7a2d98e2c33f47659a73ed108a

ARG CLAUDE_CODE_VERSION=2.1.126

RUN apt-get update \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        ca-certificates \
        curl \
        docker.io \
        git \
        nodejs \
        npm \
    && rm -rf /var/lib/apt/lists/*

COPY --from=pixi /usr/local/bin/pixi /usr/local/bin/pixi
COPY pixi.toml pixi.lock /opt/bio-reproducer-runtime/
RUN cd /opt/bio-reproducer-runtime \
    && pixi install --locked \
    && pixi clean cache --yes

COPY loopflow/ /build/loopflow/
RUN python -m pip install --no-cache-dir /build/loopflow \
    && npm install --global "@anthropic-ai/claude-code@${CLAUDE_CODE_VERSION}" \
    && rm -rf /build/loopflow /root/.cache /root/.npm

ENV PATH="/opt/bio-reproducer-runtime/.pixi/envs/default/bin:/usr/local/bin:/usr/bin:/bin"

RUN loop --help >/dev/null \
    && claude --version \
    && java -version \
    && nextflow -version
