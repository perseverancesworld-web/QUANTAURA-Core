# -------- Builder stage --------
FROM python:3.12-slim AS builder

WORKDIR /build

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml README.md ./
COPY quantaura ./quantaura

RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir .

# -------- Runtime stage --------
FROM python:3.12-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

RUN useradd --create-home --shell /bin/bash quantaura

COPY --from=builder /usr/local/lib/python3.12/site-packages \
     /usr/local/lib/python3.12/site-packages
COPY --from=builder /usr/local/bin/quantaura-serve \
     /usr/local/bin/quantaura-serve

COPY --chown=quantaura:quantaura . .

USER quantaura

EXPOSE 8000

CMD ["quantaura-serve", "--host", "0.0.0.0", "--port", "8000"]
