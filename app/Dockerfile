FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir uv && \
    uv pip install --system --no-cache -r pyproject.toml

COPY . .

EXPOSE 9009

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "9009"]
