# syntax = docker/dockerfile:1.4

FROM golang:1.22.2-alpine AS build
WORKDIR /src
ENV CGO_ENABLED=0
COPY --link go.* ./
RUN --mount=type=cache,target=/go/pkg/mod go mod download
COPY --link . .
RUN --mount=type=cache,target=/go/pkg/mod --mount=type=cache,target=/root/.cache/go-build \
	go build -trimpath -o /out/ccp .

FROM alpine:3.19.1 AS ccp
ARG USER_ID=1000
ARG GROUP_ID=1000
RUN addgroup -g ${GROUP_ID} -S ccp
RUN adduser -u ${USER_ID} -S -D ccp ccp
COPY --from=build --link /out/ccp /home/ccp/bin/ccp
USER ccp
CMD ["/home/ccp/bin/ccp", "server"]
