FROM node:24-slim AS web
WORKDIR /web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci --no-audit --no-fund
COPY apps/web/ ./
RUN npm run build

FROM python:3.12-slim
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends tesseract-ocr poppler-utils && rm -rf /var/lib/apt/lists/*
COPY pyproject.toml uv.lock ./
RUN pip install --no-cache-dir uv && uv export --quiet --frozen --no-dev --no-emit-project -o /tmp/requirements.txt && pip install --no-cache-dir -r /tmp/requirements.txt
COPY src ./src
RUN pip install --no-cache-dir --no-deps .
COPY alembic.ini ./
COPY migrations ./migrations
COPY evals ./evals
COPY --from=web /web/dist ./apps/web/dist
RUN useradd -m app && mkdir -p /app/data/uploads && chown -R app:app /app
USER app
CMD ["uvicorn", "knowdoc.api:app", "--host", "0.0.0.0", "--port", "8000"]
