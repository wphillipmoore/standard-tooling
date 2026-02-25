# Managed by standard-tooling — DO NOT EDIT in downstream repos.
# Canonical source: https://github.com/wphillipmoore/standard-tooling
ARG RUBY_VERSION=3.4
FROM ruby:${RUBY_VERSION}-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential git curl shellcheck nodejs npm && \
    rm -rf /var/lib/apt/lists/*

RUN npm install -g markdownlint-cli@0.47.0 && \
    npm cache clean --force

RUN gem install bundler

WORKDIR /workspace
