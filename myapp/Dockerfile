FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install poetry && poetry install --no-root

ENV PYTHONPATH=/app/src

CMD ["poetry", "run", "uvicorn", "myapp.main:app", "--host", "0.0.0.0", "--port", "8000"]