ARG ACMED_PLUGIN_BASE_IMAGE=ghcr.io/rohzb/acmed-plugin-base-image:v0.2.0
FROM ${ACMED_PLUGIN_BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/plugin

USER root
COPY addon/apt-packages.txt /tmp/apt-packages.txt
RUN apt-get update \
    && xargs -r apt-get install --yes --no-install-recommends < /tmp/apt-packages.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/apt-packages.txt

COPY pyproject.toml README.md /opt/plugin/
COPY src /opt/plugin/src
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir "uvicorn>=0.30.0"

EXPOSE 8081
CMD ["python", "-m", "uvicorn", "acmed_issuer_certbot.service:app", "--host", "0.0.0.0", "--port", "8081"]
