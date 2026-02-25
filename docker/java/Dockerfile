# Managed by standard-tooling — DO NOT EDIT in downstream repos.
# Canonical source: https://github.com/wphillipmoore/standard-tooling
ARG JDK_VERSION=21
FROM eclipse-temurin:${JDK_VERSION}-jdk

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
      git curl && \
    rm -rf /var/lib/apt/lists/*

# Maven wrapper self-bootstraps from consuming repos.

WORKDIR /workspace
