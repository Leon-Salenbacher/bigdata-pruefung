FROM docker:27.5.1-cli AS docker_cli

FROM apache/airflow:3.1.0

USER root
COPY --from=docker_cli /usr/local/bin/docker /usr/local/bin/docker
COPY --from=docker_cli /usr/local/libexec/docker/cli-plugins/docker-compose /usr/local/libexec/docker/cli-plugins/docker-compose
USER airflow