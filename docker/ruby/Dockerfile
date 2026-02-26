# Managed by standard-tooling — DO NOT EDIT in downstream repos.
# Canonical source: https://github.com/wphillipmoore/standard-tooling
ARG RUBY_VERSION=3.4
ARG NODE_VERSION=22.22.0
FROM node:${NODE_VERSION}-bookworm-slim AS node-donor
FROM ruby:${RUBY_VERSION}-slim
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

COPY --from=node-donor /usr/local/bin/node /usr/local/bin/node
COPY --from=node-donor /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/npm/bin/npm-cli.js /usr/local/bin/npm \
    && ln -s /usr/local/lib/node_modules/npm/bin/npx-cli.js /usr/local/bin/npx

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y --no-install-recommends \
      build-essential git curl xz-utils && \
    rm -rf /var/lib/apt/lists/*

ARG SHELLCHECK_VERSION=0.11.0
RUN curl -fsSL "https://github.com/koalaman/shellcheck/releases/download/v${SHELLCHECK_VERSION}/shellcheck-v${SHELLCHECK_VERSION}.linux.x86_64.tar.xz" \
    | tar -xJ --strip-components=1 -C /usr/local/bin/ "shellcheck-v${SHELLCHECK_VERSION}/shellcheck"

RUN npm install -g markdownlint-cli@0.47.0 && \
    npm cache clean --force

RUN gem install bundler

WORKDIR /workspace
