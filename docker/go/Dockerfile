# Managed by standard-tooling — DO NOT EDIT in downstream repos.
# Canonical source: https://github.com/wphillipmoore/standard-tooling
ARG GO_VERSION=1.23
FROM golang:${GO_VERSION}

RUN go install github.com/golangci/golangci-lint/cmd/golangci-lint@latest && \
    go install golang.org/x/vuln/cmd/govulncheck@latest && \
    go install github.com/google/go-licenses@latest

WORKDIR /workspace
