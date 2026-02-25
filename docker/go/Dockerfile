# Managed by standard-tooling — DO NOT EDIT in downstream repos.
# Canonical source: https://github.com/wphillipmoore/standard-tooling
ARG GO_VERSION=1.25
FROM golang:${GO_VERSION}

RUN go install github.com/golangci/golangci-lint/v2/cmd/golangci-lint@v2.10.1 && \
    go install golang.org/x/vuln/cmd/govulncheck@v1.1.4 && \
    go install github.com/google/go-licenses@v2.0.1 && \
    go install github.com/fzipp/gocyclo/cmd/gocyclo@latest

WORKDIR /workspace
