# Managed by standard-tooling — DO NOT EDIT in downstream repos.
# Canonical source: https://github.com/wphillipmoore/standard-tooling
ARG RUBY_VERSION=3.4
FROM ruby:${RUBY_VERSION}-slim

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential git curl && \
    rm -rf /var/lib/apt/lists/*

RUN gem install bundler

WORKDIR /workspace
