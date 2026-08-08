FROM python:3.12-slim AS builder
WORKDIR /build
RUN apt-get update && apt-get install -y --no-install-recommends build-essential \
    && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml README.md ./
COPY quantaura ./quantaura
COPY configs ./configs
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .

FROM python:3.12-slim AS production
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libgomp1 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --shell /bin/bash quantaura
COPY --from=builder /usr/local/lib/python3.12/site-packages /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/quantaura-serve /usr/local/bin/quantaura-serve
COPY --chown=quantaura:quantaura quantaura ./quantaura
COPY --chown=quantaura:quantaura configs ./configs
COPY --chown=quantaura:quantaura pyproject.toml README.md ./
USER quantaura
ENV QUANTAURA_ENV=production
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health')" || exit 1
CMD ["quantaura-serve", "--host", "0.0.0.0", "--port", "8000"]

FROM production AS development
USER root
RUN pip install --no-cache-dir black pytest pytest-asyncio ruff
USER quantaura
ENV QUANTAURA_ENV=development
CMD ["quantaura-serve", "--host", "0.0.0.0", "--port", "8000", "--reload"]
