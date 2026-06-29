FROM python:3.13-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml README.md ./
RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir .

COPY . .

EXPOSE 8000

CMD ["sh", "-c", "python -m uvicorn services.api.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
