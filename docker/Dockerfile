ARG ACMED_PLUGIN_BASE_IMAGE=python:3.12-slim
FROM ${ACMED_PLUGIN_BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /opt/plugin

USER root
COPY acmed-issuer-certbot/addon/apt-packages.txt /tmp/apt-packages.txt
RUN apt-get update \
    && xargs -r apt-get install --yes --no-install-recommends < /tmp/apt-packages.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/apt-packages.txt

COPY acmed-plugin-sdk /opt/src/acmed-plugin-sdk
RUN pip install --no-cache-dir /opt/src/acmed-plugin-sdk[server] \
    && rm -rf /opt/src/acmed-plugin-sdk

COPY acmed-issuer-certbot /opt/src/acmed-issuer-certbot
RUN pip install --no-cache-dir /opt/src/acmed-issuer-certbot \
    && rm -rf /opt/src/acmed-issuer-certbot

EXPOSE 8081
CMD ["python", "-m", "uvicorn", "plugin_service.main:app", "--host", "0.0.0.0", "--port", "8081"]
