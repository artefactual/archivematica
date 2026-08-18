# Local/test-only Apereo CAS server for Archivematica development.
#
# The image is environment-agnostic: the runtime configuration (including the
# server port), the JSON service registry and the JSON user store are expected
# to be mounted at /etc/cas/config and /etc/cas/services.
#
# The CAS version is determined by the pinned commit of the Apereo CAS WAR
# overlay template below. The default commit is the head of the 7.3 branch as
# of 2026-08-17 and builds the CAS 7.3.8 stable release, as declared by the
# cas.version property in its gradle.properties file. To upgrade, pick a
# commit from the target release branch in
# https://github.com/apereo/cas-overlay-template and check its
# gradle.properties file for the CAS version it builds.
ARG CAS_OVERLAY_COMMIT=b244d192d9462068fc24625a75ebe19ed6fc34cd

FROM alpine:3.22 AS overlay-generator
ARG CAS_OVERLAY_COMMIT
RUN apk add --no-cache curl tar ca-certificates
WORKDIR /tmp
RUN curl -fsSL --retry 5 --retry-delay 2 \
      https://github.com/apereo/cas-overlay-template/archive/${CAS_OVERLAY_COMMIT}.tar.gz \
    | tar -xz \
    && mv cas-overlay-template-${CAS_OVERLAY_COMMIT} cas-overlay

FROM eclipse-temurin:21-jdk-jammy AS builder
COPY --from=overlay-generator /tmp/cas-overlay /cas-overlay
WORKDIR /cas-overlay
# json-service-registry: register services from /etc/cas/services JSON files.
# generic: authenticate against the static JSON user store (users.json).
RUN chmod +x gradlew && \
    ./gradlew clean build -x test --no-daemon \
      -PcasModules=json-service-registry,generic

FROM eclipse-temurin:21-jre-jammy
USER root
RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY --from=builder /cas-overlay/build/libs/cas.war /app/cas.war
ENTRYPOINT ["java", "-jar", "/app/cas.war"]
