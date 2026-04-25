FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

ARG ACMED_PLUGIN_SDK_SPEC=acmed-plugin-sdk>=0.2.0
ARG ACMED_PLUGIN_SDK_FALLBACK=

WORKDIR /opt/plugin

USER root
COPY addon/apt-packages.txt /tmp/apt-packages.txt
RUN apt-get update \
    && xargs -r apt-get install --yes --no-install-recommends < /tmp/apt-packages.txt \
    && rm -rf /var/lib/apt/lists/* /tmp/apt-packages.txt

COPY pyproject.toml README.md /opt/plugin/
COPY src /opt/plugin/src
RUN pip install --no-cache-dir "${ACMED_PLUGIN_SDK_SPEC}" \
    || (test -n "${ACMED_PLUGIN_SDK_FALLBACK}" && pip install --no-cache-dir "${ACMED_PLUGIN_SDK_FALLBACK}")
RUN pip install --no-cache-dir . \
    && pip install --no-cache-dir "uvicorn>=0.30.0"

EXPOSE 8081
CMD ["python", "-m", "uvicorn", "plugin_service.main:app", "--host", "0.0.0.0", "--port", "8081"]
