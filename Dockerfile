# Milestone 2: reproducible container for local dev and cloud deployment.
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "e_cycle_ai.main:app", "--host", "0.0.0.0", "--port", "8000"]
