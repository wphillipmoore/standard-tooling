#!/usr/bin/env bash
# Managed by standard-tooling — DO NOT EDIT in downstream repos.
# Canonical source: https://github.com/wphillipmoore/standard-tooling
# build.sh — build all dev container images with default version tags.
set -euo pipefail

script_dir="$(cd "$(dirname "$0")" && pwd)"

build() {
  local lang="$1" tag="$2" version_arg="$3" version_val="$4"
  echo "Building dev-${lang}:${version_val} ..."
  docker build \
    --build-arg "${version_arg}=${version_val}" \
    -t "dev-${lang}:${version_val}" \
    "${script_dir}/${lang}"
}

build ruby   ruby   RUBY_VERSION   3.2
build ruby   ruby   RUBY_VERSION   3.3
build ruby   ruby   RUBY_VERSION   3.4
build python python PYTHON_VERSION 3.13
build python python PYTHON_VERSION 3.14
build java   java   JDK_VERSION    21
build go     go     GO_VERSION     1.23

echo "All images built successfully."
